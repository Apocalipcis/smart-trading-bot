"""Pending confirmation store with TTL management."""

import asyncio
import logging
import time
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Union
from enum import Enum

from pydantic import BaseModel, Field

from .types import Order, OrderStatus

logger = logging.getLogger(__name__)


class PendingConfirmation(BaseModel):
    """Pending order confirmation."""
    
    order_id: str = Field(..., description="Order ID")
    order: Order = Field(..., description="The order awaiting confirmation")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: datetime = Field(..., description="When the confirmation expires")
    ttl_seconds: int = Field(..., description="Time to live in seconds")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    def is_expired(self) -> bool:
        """Check if the confirmation has expired."""
        return datetime.now(timezone.utc) > self.expires_at
    
    def get_remaining_time(self) -> float:
        """Get remaining time until expiration in seconds."""
        remaining = (self.expires_at - datetime.now(timezone.utc)).total_seconds()
        return max(0, remaining)
    
    def get_expiration_percentage(self) -> float:
        """Get expiration percentage (0-100)."""
        total_time = self.ttl_seconds
        elapsed = (datetime.now(timezone.utc) - self.created_at).total_seconds()
        percentage = (elapsed / total_time) * 100
        return min(100, max(0, percentage))


class ConfirmationAction(str, Enum):
    """Confirmation action types."""
    APPROVE = "approve"
    REJECT = "reject"
    MODIFY = "modify"


class ConfirmationResult(BaseModel):
    """Result of confirmation action."""
    
    order_id: str = Field(..., description="Order ID")
    action: ConfirmationAction = Field(..., description="Action taken")
    confirmed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    modified_order: Optional[Order] = Field(None, description="Modified order if action was modify")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class PendingConfirmationStore:
    """Store for orders awaiting manual confirmation with TTL management."""
    
    def __init__(
        self,
        default_ttl_seconds: int = 300,  # 5 minutes default
        max_pending_orders: int = 100,
        cleanup_interval: int = 60  # Cleanup every minute
    ):
        self.default_ttl_seconds = default_ttl_seconds
        self.max_pending_orders = max_pending_orders
        self.cleanup_interval = cleanup_interval
        
        # Storage
        self._pending_confirmations: Dict[str, PendingConfirmation] = {}
        self._confirmation_results: Dict[str, ConfirmationResult] = {}
        
        # Control
        self._running = False
        self._cleanup_task: Optional[asyncio.Task] = None
        
        # Statistics
        self._stats = {
            "total_added": 0,
            "total_confirmed": 0,
            "total_expired": 0,
            "total_rejected": 0,
            "total_modified": 0
        }
    
    async def start(self) -> None:
        """Start the pending confirmation store."""
        if self._running:
            logger.warning("Pending confirmation store is already running")
            return
        
        self._running = True
        
        # Start cleanup task
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        
        logger.info("Pending confirmation store started")
    
    async def stop(self) -> None:
        """Stop the pending confirmation store."""
        if not self._running:
            return
        
        self._running = False
        
        # Cancel cleanup task
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Pending confirmation store stopped")
    
    async def add_pending_confirmation(
        self,
        order: Order,
        ttl_seconds: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Add an order to pending confirmations.
        
        Args:
            order: The order awaiting confirmation
            ttl_seconds: Time to live in seconds (uses default if not provided)
            metadata: Additional metadata
            
        Returns:
            Order ID
        """
        # Check if order is already pending
        if order.id in self._pending_confirmations:
            logger.warning(f"Order {order.id} is already pending confirmation")
            return order.id
        
        # Check if we've reached the limit
        if len(self._pending_confirmations) >= self.max_pending_orders:
            # Remove oldest pending confirmation
            oldest_id = min(
                self._pending_confirmations.keys(),
                key=lambda x: self._pending_confirmations[x].created_at
            )
            await self._expire_confirmation(oldest_id, "replaced_by_new_order")
        
        # Calculate TTL
        ttl = ttl_seconds or self.default_ttl_seconds
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=ttl)
        
        # Create pending confirmation
        pending_confirmation = PendingConfirmation(
            order_id=order.id,
            order=order,
            expires_at=expires_at,
            ttl_seconds=ttl,
            metadata=metadata or {}
        )
        
        # Store it
        self._pending_confirmations[order.id] = pending_confirmation
        self._stats["total_added"] += 1
        
        logger.info(f"Order {order.id} added to pending confirmations (expires in {ttl}s)")
        
        return order.id
    
    async def confirm_order(
        self,
        order_id: str,
        action: ConfirmationAction,
        modified_order: Optional[Order] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[ConfirmationResult]:
        """
        Confirm or reject a pending order.
        
        Args:
            order_id: Order ID to confirm
            action: Action to take (approve, reject, modify)
            modified_order: Modified order if action is modify
            metadata: Additional metadata
            
        Returns:
            Confirmation result or None if order not found
        """
        if order_id not in self._pending_confirmations:
            logger.warning(f"Order {order_id} not found in pending confirmations")
            return None
        
        pending_confirmation = self._pending_confirmations[order_id]
        
        # Check if expired
        if pending_confirmation.is_expired():
            logger.warning(f"Order {order_id} has expired, cannot confirm")
            await self._expire_confirmation(order_id, "expired_before_confirmation")
            return None
        
        # Create confirmation result
        result = ConfirmationResult(
            order_id=order_id,
            action=action,
            modified_order=modified_order,
            metadata=metadata or {}
        )
        
        # Store result
        self._confirmation_results[order_id] = result
        
        # Remove from pending
        del self._pending_confirmations[order_id]
        
        # Update statistics
        if action == ConfirmationAction.APPROVE:
            self._stats["total_confirmed"] += 1
        elif action == ConfirmationAction.REJECT:
            self._stats["total_rejected"] += 1
        elif action == ConfirmationAction.MODIFY:
            self._stats["total_modified"] += 1
        
        logger.info(f"Order {order_id} {action.value}ed")
        
        return result
    
    async def get_pending_confirmation(self, order_id: str) -> Optional[PendingConfirmation]:
        """Get a pending confirmation by order ID."""
        return self._pending_confirmations.get(order_id)
    
    async def get_confirmation_result(self, order_id: str) -> Optional[ConfirmationResult]:
        """Get confirmation result by order ID."""
        return self._confirmation_results.get(order_id)
    
    async def list_pending_confirmations(
        self,
        include_expired: bool = False
    ) -> List[PendingConfirmation]:
        """List all pending confirmations."""
        confirmations = list(self._pending_confirmations.values())
        
        if not include_expired:
            confirmations = [c for c in confirmations if not c.is_expired()]
        
        # Sort by creation time (oldest first)
        confirmations.sort(key=lambda x: x.created_at)
        
        return confirmations
    
    async def list_confirmation_results(
        self,
        limit: Optional[int] = None
    ) -> List[ConfirmationResult]:
        """List confirmation results."""
        results = list(self._confirmation_results.values())
        
        # Sort by confirmation time (newest first)
        results.sort(key=lambda x: x.confirmed_at, reverse=True)
        
        if limit:
            results = results[:limit]
        
        return results
    
    async def cancel_pending_confirmation(self, order_id: str) -> bool:
        """Cancel a pending confirmation."""
        if order_id not in self._pending_confirmations:
            return False
        
        await self._expire_confirmation(order_id, "cancelled_manually")
        return True
    
    async def extend_ttl(self, order_id: str, additional_seconds: int) -> bool:
        """Extend the TTL of a pending confirmation."""
        if order_id not in self._pending_confirmations:
            return False
        
        pending_confirmation = self._pending_confirmations[order_id]
        
        # Extend expiration time
        pending_confirmation.expires_at += timedelta(seconds=additional_seconds)
        pending_confirmation.ttl_seconds += additional_seconds
        
        logger.info(f"Extended TTL for order {order_id} by {additional_seconds}s")
        
        return True
    
    def get_store_stats(self) -> Dict[str, Any]:
        """Get store statistics."""
        current_time = datetime.now(timezone.utc)
        
        # Count expired confirmations
        expired_count = sum(
            1 for c in self._pending_confirmations.values()
            if c.is_expired()
        )
        
        # Calculate average remaining time
        active_confirmations = [
            c for c in self._pending_confirmations.values()
            if not c.is_expired()
        ]
        
        avg_remaining_time = 0
        if active_confirmations:
            total_remaining = sum(c.get_remaining_time() for c in active_confirmations)
            avg_remaining_time = total_remaining / len(active_confirmations)
        
        return {
            "running": self._running,
            "pending_count": len(self._pending_confirmations),
            "active_count": len(active_confirmations),
            "expired_count": expired_count,
            "results_count": len(self._confirmation_results),
            "avg_remaining_time": avg_remaining_time,
            "statistics": self._stats.copy()
        }
    
    async def _expire_confirmation(self, order_id: str, reason: str) -> None:
        """Expire a pending confirmation."""
        if order_id not in self._pending_confirmations:
            return
        
        pending_confirmation = self._pending_confirmations[order_id]
        
        # Create expiration result
        result = ConfirmationResult(
            order_id=order_id,
            action=ConfirmationAction.REJECT,
            metadata={"expiration_reason": reason}
        )
        
        # Store result
        self._confirmation_results[order_id] = result
        
        # Remove from pending
        del self._pending_confirmations[order_id]
        
        # Update statistics
        self._stats["total_expired"] += 1
        
        logger.info(f"Order {order_id} expired: {reason}")
    
    async def _cleanup_loop(self) -> None:
        """Periodic cleanup of expired confirmations."""
        while self._running:
            try:
                await asyncio.sleep(self.cleanup_interval)
                
                # Find expired confirmations
                expired_ids = []
                for order_id, confirmation in self._pending_confirmations.items():
                    if confirmation.is_expired():
                        expired_ids.append(order_id)
                
                # Expire them
                for order_id in expired_ids:
                    await self._expire_confirmation(order_id, "expired_during_cleanup")
                
                if expired_ids:
                    logger.info(f"Cleaned up {len(expired_ids)} expired confirmations")
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")
    
    async def clear_all(self) -> None:
        """Clear all pending confirmations and results."""
        self._pending_confirmations.clear()
        self._confirmation_results.clear()
        
        logger.info("All pending confirmations and results cleared")
    
    async def get_expiring_soon(self, minutes: int = 5) -> List[PendingConfirmation]:
        """Get confirmations expiring within the specified minutes."""
        threshold = datetime.now(timezone.utc) + timedelta(minutes=minutes)
        
        expiring_soon = [
            c for c in self._pending_confirmations.values()
            if c.expires_at <= threshold and not c.is_expired()
        ]
        
        # Sort by expiration time (earliest first)
        expiring_soon.sort(key=lambda x: x.expires_at)
        
        return expiring_soon
