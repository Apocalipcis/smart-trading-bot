"""Order queue with idempotent submissions and retry logic."""

import asyncio
import hashlib
import json
import logging
import time
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field

from .types import Order, OrderStatus

logger = logging.getLogger(__name__)


class QueuePriority(str, Enum):
    """Order queue priority levels."""
    HIGH = "high"      # Market orders, stop orders
    NORMAL = "normal"  # Regular limit orders
    LOW = "low"        # Non-urgent orders


class OrderSubmissionResult(BaseModel):
    """Result of order submission attempt."""
    
    success: bool = Field(..., description="Whether submission was successful")
    order_id: str = Field(..., description="Internal order ID")
    exchange_order_id: Optional[str] = Field(None, description="Exchange order ID")
    status: OrderStatus = Field(..., description="Order status")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    retry_count: int = Field(default=0, description="Number of retries attempted")
    submitted_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class QueuedOrder(BaseModel):
    """Order in the submission queue."""
    
    order: Order = Field(..., description="The order to submit")
    priority: QueuePriority = Field(default=QueuePriority.NORMAL, description="Queue priority")
    idempotency_key: str = Field(..., description="Unique idempotency key")
    retry_count: int = Field(default=0, description="Current retry count")
    max_retries: int = Field(default=3, description="Maximum retry attempts")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    next_retry_at: Optional[datetime] = Field(None, description="When to retry next")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class OrderQueue:
    """Asynchronous order queue with idempotency and retry logic."""
    
    def __init__(
        self,
        max_concurrent_orders: int = 10,
        retry_delays: List[float] = None,
        idempotency_ttl: int = 3600
    ):
        self.max_concurrent_orders = max_concurrent_orders
        self.retry_delays = retry_delays or [1.0, 5.0, 15.0]  # Exponential backoff
        self.idempotency_ttl = idempotency_ttl
        
        # Queue storage
        self._high_priority_queue: asyncio.Queue = asyncio.Queue()
        self._normal_priority_queue: asyncio.Queue = asyncio.Queue()
        self._low_priority_queue: asyncio.Queue = asyncio.Queue()
        
        # Tracking
        self._idempotency_store: Dict[str, Dict[str, Any]] = {}
        self._active_orders: Dict[str, QueuedOrder] = {}
        self._completed_orders: Dict[str, OrderSubmissionResult] = {}
        
        # Control
        self._running = False
        self._worker_tasks: List[asyncio.Task] = []
        self._cleanup_task: Optional[asyncio.Task] = None
        
        # Statistics
        self._stats = {
            "submitted": 0,
            "successful": 0,
            "failed": 0,
            "retried": 0,
            "duplicates": 0
        }
    
    async def start(self) -> None:
        """Start the order queue workers."""
        if self._running:
            logger.warning("Order queue is already running")
            return
        
        self._running = True
        
        # Start worker tasks
        for i in range(self.max_concurrent_orders):
            task = asyncio.create_task(self._worker(f"worker-{i}"))
            self._worker_tasks.append(task)
        
        # Start cleanup task
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        
        logger.info(f"Order queue started with {self.max_concurrent_orders} workers")
    
    async def stop(self) -> None:
        """Stop the order queue workers."""
        if not self._running:
            return
        
        self._running = False
        
        # Cancel worker tasks
        for task in self._worker_tasks:
            task.cancel()
        
        # Wait for workers to finish
        if self._worker_tasks:
            await asyncio.gather(*self._worker_tasks, return_exceptions=True)
        
        # Cancel cleanup task
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Order queue stopped")
    
    async def submit_order(
        self,
        order: Order,
        priority: QueuePriority = QueuePriority.NORMAL,
        max_retries: int = 3
    ) -> str:
        """
        Submit an order to the queue.
        
        Args:
            order: The order to submit
            priority: Queue priority
            max_retries: Maximum retry attempts
            
        Returns:
            Order ID
        """
        # Generate idempotency key
        idempotency_key = self._generate_idempotency_key(order)
        
        # Check for duplicate
        if idempotency_key in self._idempotency_store:
            self._stats["duplicates"] += 1
            logger.info(f"Duplicate order detected: {idempotency_key}")
            return self._idempotency_store[idempotency_key]["order_id"]
        
        # Create queued order
        queued_order = QueuedOrder(
            order=order,
            priority=priority,
            idempotency_key=idempotency_key,
            max_retries=max_retries
        )
        
        # Store idempotency key
        self._idempotency_store[idempotency_key] = {
            "order_id": order.id,
            "timestamp": time.time(),
            "status": "queued"
        }
        
        # Add to appropriate queue
        await self._add_to_queue(queued_order)
        
        self._stats["submitted"] += 1
        logger.info(f"Order {order.id} queued with priority {priority.value}")
        
        return order.id
    
    async def get_order_status(self, order_id: str) -> Optional[OrderSubmissionResult]:
        """Get the status of a submitted order."""
        return self._completed_orders.get(order_id)
    
    async def cancel_order(self, order_id: str) -> bool:
        """Cancel a queued order."""
        # Check if order is in active orders
        if order_id in self._active_orders:
            queued_order = self._active_orders[order_id]
            queued_order.order.update_status(OrderStatus.CANCELLED)
            
            # Remove from active orders
            del self._active_orders[order_id]
            
            # Update idempotency store
            for key, value in self._idempotency_store.items():
                if value["order_id"] == order_id:
                    value["status"] = "cancelled"
                    break
            
            logger.info(f"Order {order_id} cancelled")
            return True
        
        # Check if order is in any of the queues
        cancelled_from_queue = await self._cancel_from_queue(order_id)
        if cancelled_from_queue:
            # Update idempotency store
            for key, value in self._idempotency_store.items():
                if value["order_id"] == order_id:
                    value["status"] = "cancelled"
                    break
            logger.info(f"Order {order_id} cancelled from queue")
            return True
        
        return False
    
    def get_queue_stats(self) -> Dict[str, Any]:
        """Get queue statistics."""
        return {
            "running": self._running,
            "active_orders": len(self._active_orders),
            "completed_orders": len(self._completed_orders),
            "queue_sizes": {
                "high": self._high_priority_queue.qsize(),
                "normal": self._normal_priority_queue.qsize(),
                "low": self._low_priority_queue.qsize()
            },
            "statistics": self._stats.copy(),
            "idempotency_keys": len(self._idempotency_store)
        }
    
    async def _worker(self, worker_name: str) -> None:
        """Worker task that processes orders from the queue."""
        logger.info(f"Worker {worker_name} started")
        
        while self._running:
            try:
                # Get order from queue (prioritize high priority)
                queued_order = await self._get_next_order()
                
                if queued_order is None:
                    continue
                
                # Process the order
                await self._process_order(queued_order, worker_name)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Worker {worker_name} error: {e}")
                await asyncio.sleep(1)
        
        logger.info(f"Worker {worker_name} stopped")
    
    async def _get_next_order(self) -> Optional[QueuedOrder]:
        """Get the next order from the queue based on priority."""
        # Try high priority first
        try:
            return self._high_priority_queue.get_nowait()
        except asyncio.QueueEmpty:
            pass
        
        # Try normal priority
        try:
            return self._normal_priority_queue.get_nowait()
        except asyncio.QueueEmpty:
            pass
        
        # Try low priority
        try:
            return self._low_priority_queue.get_nowait()
        except asyncio.QueueEmpty:
            pass
        
        # No orders available
        await asyncio.sleep(0.1)
        return None
    
    async def _add_to_queue(self, queued_order: QueuedOrder) -> None:
        """Add order to the appropriate priority queue."""
        if queued_order.priority == QueuePriority.HIGH:
            await self._high_priority_queue.put(queued_order)
        elif queued_order.priority == QueuePriority.NORMAL:
            await self._normal_priority_queue.put(queued_order)
        else:  # LOW
            await self._low_priority_queue.put(queued_order)
    
    async def _cancel_from_queue(self, order_id: str) -> bool:
        """Cancel an order from any of the queues."""
        # Check high priority queue
        if await self._remove_from_queue(self._high_priority_queue, order_id):
            return True
        
        # Check normal priority queue
        if await self._remove_from_queue(self._normal_priority_queue, order_id):
            return True
        
        # Check low priority queue
        if await self._remove_from_queue(self._low_priority_queue, order_id):
            return True
        
        return False
    
    async def _remove_from_queue(self, queue: asyncio.Queue, order_id: str) -> bool:
        """Remove an order from a specific queue."""
        # Get all items from the queue
        items = []
        try:
            while True:
                item = queue.get_nowait()
                if item.order.id != order_id:
                    items.append(item)
        except asyncio.QueueEmpty:
            pass
        
        # Put back all items except the one to cancel
        for item in items:
            await queue.put(item)
        
        # Return True if we found and removed the order
        return len(items) < queue.qsize() + 1  # +1 because we removed one item
    
    async def _process_order(self, queued_order: QueuedOrder, worker_name: str) -> None:
        """Process a single order."""
        order = queued_order.order
        
        try:
            # Add to active orders
            self._active_orders[order.id] = queued_order
            
            # Check if order should be retried
            if queued_order.next_retry_at and datetime.now(timezone.utc) < queued_order.next_retry_at:
                # Put back in queue for later retry
                await self._add_to_queue(queued_order)
                return
            
            # Submit order to exchange (mock implementation)
            result = await self._submit_to_exchange(order, queued_order)
            
            # Handle result
            if result.success:
                self._stats["successful"] += 1
                logger.info(f"Order {order.id} submitted successfully")
            else:
                # Handle failure
                await self._handle_submission_failure(queued_order, result)
            
            # Store result
            self._completed_orders[order.id] = result
            
            # Remove from active orders
            if order.id in self._active_orders:
                del self._active_orders[order.id]
            
            # Update idempotency store
            for key, value in self._idempotency_store.items():
                if value["order_id"] == order.id:
                    value["status"] = result.status.value
                    break
            
        except Exception as e:
            logger.error(f"Error processing order {order.id}: {e}")
            
            # Create error result
            result = OrderSubmissionResult(
                success=False,
                order_id=order.id,
                status=OrderStatus.REJECTED,
                error_message=str(e)
            )
            
            self._completed_orders[order.id] = result
            self._stats["failed"] += 1
    
    async def _submit_to_exchange(self, order: Order, queued_order: QueuedOrder) -> OrderSubmissionResult:
        """Submit order to exchange (mock implementation)."""
        # This would integrate with the actual exchange client
        # For now, simulate successful submission
        
        # Simulate processing delay
        await asyncio.sleep(0.1)
        
        # Simulate success (90% success rate)
        import random
        if random.random() < 0.9:
            return OrderSubmissionResult(
                success=True,
                order_id=order.id,
                exchange_order_id=f"EXCH_{uuid.uuid4().hex[:8]}",
                status=OrderStatus.SUBMITTED,
                retry_count=queued_order.retry_count
            )
        else:
            return OrderSubmissionResult(
                success=False,
                order_id=order.id,
                status=OrderStatus.REJECTED,
                error_message="Exchange error (simulated)",
                retry_count=queued_order.retry_count
            )
    
    async def _handle_submission_failure(self, queued_order: QueuedOrder, result: OrderSubmissionResult) -> None:
        """Handle order submission failure with retry logic."""
        queued_order.retry_count += 1
        self._stats["retried"] += 1
        
        if queued_order.retry_count <= queued_order.max_retries:
            # Calculate retry delay
            delay_index = min(queued_order.retry_count - 1, len(self.retry_delays) - 1)
            delay = self.retry_delays[delay_index]
            
            # Add jitter
            jitter = delay * 0.1 * (hash(queued_order.id) % 100) / 100
            total_delay = delay + jitter
            
            # Schedule retry
            queued_order.next_retry_at = datetime.now(timezone.utc) + asyncio.Timedelta(seconds=total_delay)
            
            logger.info(f"Order {queued_order.order.id} will be retried in {total_delay:.2f}s (attempt {queued_order.retry_count})")
            
            # Put back in queue
            await self._add_to_queue(queued_order)
        else:
            # Max retries exceeded
            self._stats["failed"] += 1
            logger.error(f"Order {queued_order.order.id} failed after {queued_order.max_retries} retries")
    
    def _generate_idempotency_key(self, order: Order) -> str:
        """Generate idempotency key for order deduplication."""
        # Create a hash of order properties that should be unique
        key_data = {
            "pair": order.pair,
            "side": order.side.value,
            "order_type": order.order_type.value,
            "quantity": str(order.quantity),
            "price": str(order.price) if order.price else None,
            "stop_price": str(order.stop_price) if order.stop_price else None,
            "timestamp": int(time.time() / 60)  # Round to minute for deduplication window
        }
        
        key_string = json.dumps(key_data, sort_keys=True)
        return hashlib.sha256(key_string.encode()).hexdigest()
    
    async def _cleanup_loop(self) -> None:
        """Periodic cleanup of expired idempotency keys."""
        while self._running:
            try:
                await asyncio.sleep(300)  # Clean up every 5 minutes
                
                current_time = time.time()
                expired_keys = []
                
                for key, value in self._idempotency_store.items():
                    if current_time - value["timestamp"] > self.idempotency_ttl:
                        expired_keys.append(key)
                
                for key in expired_keys:
                    del self._idempotency_store[key]
                
                if expired_keys:
                    logger.info(f"Cleaned up {len(expired_keys)} expired idempotency keys")
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")
