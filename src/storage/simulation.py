"""Simulation database schema and storage."""

import asyncio
import json
import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import Dict, List, Optional, Any
from pathlib import Path

from pydantic import BaseModel, Field

from ..orders.types import Order, OrderStatus, OrderSide
from ..simulation.portfolio import Position, Trade, PortfolioSnapshot

logger = logging.getLogger(__name__)


class SimulationOrder(BaseModel):
    """Simulation order model for database storage."""
    id: str = Field(..., description="Simulation order ID")
    pair: str = Field(..., description="Trading pair")
    side: str = Field(..., description="Order side")
    order_type: str = Field(..., description="Order type")
    quantity: str = Field(..., description="Order quantity as string")
    price: Optional[str] = Field(None, description="Order price as string")
    stop_price: Optional[str] = Field(None, description="Stop price as string")
    status: str = Field(..., description="Order status")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    filled_at: Optional[datetime] = Field(None, description="Fill timestamp")
    filled_quantity: str = Field(default="0", description="Filled quantity as string")
    average_price: Optional[str] = Field(None, description="Average fill price as string")
    commission: str = Field(default="0", description="Commission as string")
    metadata: str = Field(default="{}", description="Metadata as JSON string")


class SimulationTrade(BaseModel):
    """Simulation trade model for database storage."""
    id: str = Field(..., description="Trade ID")
    pair: str = Field(..., description="Trading pair")
    side: str = Field(..., description="Trade side")
    quantity: str = Field(..., description="Trade quantity as string")
    price: str = Field(..., description="Trade price as string")
    commission: str = Field(..., description="Commission as string")
    timestamp: datetime = Field(..., description="Trade timestamp")
    order_id: str = Field(..., description="Related order ID")
    position_id: Optional[str] = Field(None, description="Related position ID")


class SimulationPosition(BaseModel):
    """Simulation position model for database storage."""
    id: str = Field(..., description="Position ID")
    pair: str = Field(..., description="Trading pair")
    side: str = Field(..., description="Position side")
    quantity: str = Field(..., description="Position quantity as string")
    average_price: str = Field(..., description="Average price as string")
    unrealized_pnl: str = Field(default="0", description="Unrealized P&L as string")
    realized_pnl: str = Field(default="0", description="Realized P&L as string")
    stop_loss: Optional[str] = Field(None, description="Stop loss as string")
    take_profit: Optional[str] = Field(None, description="Take profit as string")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class SimulationSnapshot(BaseModel):
    """Simulation portfolio snapshot model for database storage."""
    id: str = Field(..., description="Snapshot ID")
    timestamp: datetime = Field(..., description="Snapshot timestamp")
    total_value: str = Field(..., description="Total portfolio value as string")
    cash: str = Field(..., description="Available cash as string")
    positions_value: str = Field(..., description="Positions value as string")
    unrealized_pnl: str = Field(..., description="Unrealized P&L as string")
    realized_pnl: str = Field(..., description="Realized P&L as string")
    total_pnl: str = Field(..., description="Total P&L as string")
    return_pct: str = Field(..., description="Return percentage as string")


class SimulationStorage:
    """Database storage for simulation data."""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
    
    async def initialize(self) -> None:
        """Initialize simulation database tables."""
        async with self.db_manager.get_connection() as conn:
            await self._create_simulation_tables(conn)
            await self._create_simulation_indexes(conn)
    
    async def _create_simulation_tables(self, conn) -> None:
        """Create simulation-specific tables."""
        
        # Simulation orders table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS orders_sim (
                id TEXT PRIMARY KEY,
                pair TEXT NOT NULL,
                side TEXT NOT NULL,
                order_type TEXT NOT NULL,
                quantity TEXT NOT NULL,
                price TEXT,
                stop_price TEXT,
                status TEXT NOT NULL,
                created_at TIMESTAMP NOT NULL,
                updated_at TIMESTAMP NOT NULL,
                filled_at TIMESTAMP,
                filled_quantity TEXT DEFAULT '0',
                average_price TEXT,
                commission TEXT DEFAULT '0',
                metadata TEXT DEFAULT '{}'
            )
        """)
        
        # Simulation trades table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS trades_sim (
                id TEXT PRIMARY KEY,
                pair TEXT NOT NULL,
                side TEXT NOT NULL,
                quantity TEXT NOT NULL,
                price TEXT NOT NULL,
                commission TEXT NOT NULL,
                timestamp TIMESTAMP NOT NULL,
                order_id TEXT NOT NULL,
                position_id TEXT,
                FOREIGN KEY (order_id) REFERENCES orders_sim (id)
            )
        """)
        
        # Simulation positions table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS positions_sim (
                id TEXT PRIMARY KEY,
                pair TEXT NOT NULL,
                side TEXT NOT NULL,
                quantity TEXT NOT NULL,
                average_price TEXT NOT NULL,
                unrealized_pnl TEXT DEFAULT '0',
                realized_pnl TEXT DEFAULT '0',
                stop_loss TEXT,
                take_profit TEXT,
                created_at TIMESTAMP NOT NULL,
                updated_at TIMESTAMP NOT NULL
            )
        """)
        
        # Simulation portfolio snapshots table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS equity_snapshots_sim (
                id TEXT PRIMARY KEY,
                timestamp TIMESTAMP NOT NULL,
                total_value TEXT NOT NULL,
                cash TEXT NOT NULL,
                positions_value TEXT NOT NULL,
                unrealized_pnl TEXT NOT NULL,
                realized_pnl TEXT NOT NULL,
                total_pnl TEXT NOT NULL,
                return_pct TEXT NOT NULL
            )
        """)
        
        # Simulation configuration table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS simulation_config (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TIMESTAMP NOT NULL
            )
        """)
        
        conn.commit()
    
    async def _create_simulation_indexes(self, conn) -> None:
        """Create indexes for simulation tables."""
        
        # Orders indexes
        conn.execute("CREATE INDEX IF NOT EXISTS idx_orders_sim_pair ON orders_sim (pair)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_orders_sim_status ON orders_sim (status)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_orders_sim_created ON orders_sim (created_at)")
        
        # Trades indexes
        conn.execute("CREATE INDEX IF NOT EXISTS idx_trades_sim_pair ON trades_sim (pair)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_trades_sim_timestamp ON trades_sim (timestamp)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_trades_sim_order_id ON trades_sim (order_id)")
        
        # Positions indexes
        conn.execute("CREATE INDEX IF NOT EXISTS idx_positions_sim_pair ON positions_sim (pair)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_positions_sim_updated ON positions_sim (updated_at)")
        
        # Snapshots indexes
        conn.execute("CREATE INDEX IF NOT EXISTS idx_snapshots_sim_timestamp ON equity_snapshots_sim (timestamp)")
        
        conn.commit()
    
    async def save_order(self, order: Order) -> None:
        """Save a simulation order to the database."""
        sim_order = SimulationOrder(
            id=order.id,
            pair=order.pair,
            side=order.side.value,
            order_type=order.order_type.value,
            quantity=str(order.quantity),
            price=str(order.price) if order.price else None,
            stop_price=str(order.stop_price) if order.stop_price else None,
            status=order.status.value,
            created_at=order.created_at,
            updated_at=order.updated_at,
            filled_at=order.filled_at,
            filled_quantity=str(order.filled_quantity),
            average_price=str(order.average_price) if order.average_price else None,
            commission=str(order.commission),
            metadata=json.dumps(order.metadata)
        )
        
        async with self.db_manager.get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO orders_sim 
                (id, pair, side, order_type, quantity, price, stop_price, status,
                 created_at, updated_at, filled_at, filled_quantity, average_price, commission, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                sim_order.id, sim_order.pair, sim_order.side, sim_order.order_type,
                sim_order.quantity, sim_order.price, sim_order.stop_price, sim_order.status,
                sim_order.created_at, sim_order.updated_at, sim_order.filled_at,
                sim_order.filled_quantity, sim_order.average_price, sim_order.commission,
                sim_order.metadata
            ))
            conn.commit()
    
    async def save_trade(self, trade: Trade) -> None:
        """Save a simulation trade to the database."""
        sim_trade = SimulationTrade(
            id=trade.id,
            pair=trade.pair,
            side=trade.side.value,
            quantity=str(trade.quantity),
            price=str(trade.price),
            commission=str(trade.commission),
            timestamp=trade.timestamp,
            order_id=trade.order_id,
            position_id=trade.position_id
        )
        
        async with self.db_manager.get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO trades_sim 
                (id, pair, side, quantity, price, commission, timestamp, order_id, position_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                sim_trade.id, sim_trade.pair, sim_trade.side, sim_trade.quantity,
                sim_trade.price, sim_trade.commission, sim_trade.timestamp,
                sim_trade.order_id, sim_trade.position_id
            ))
            conn.commit()
    
    async def save_position(self, position: Position) -> None:
        """Save a simulation position to the database."""
        position_id = f"{position.pair}_{position.side.value}"
        
        sim_position = SimulationPosition(
            id=position_id,
            pair=position.pair,
            side=position.side.value,
            quantity=str(position.quantity),
            average_price=str(position.average_price),
            unrealized_pnl=str(position.unrealized_pnl),
            realized_pnl=str(position.realized_pnl),
            stop_loss=str(position.stop_loss) if position.stop_loss else None,
            take_profit=str(position.take_profit) if position.take_profit else None,
            created_at=position.created_at,
            updated_at=position.updated_at
        )
        
        async with self.db_manager.get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO positions_sim 
                (id, pair, side, quantity, average_price, unrealized_pnl, realized_pnl,
                 stop_loss, take_profit, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                sim_position.id, sim_position.pair, sim_position.side, sim_position.quantity,
                sim_position.average_price, sim_position.unrealized_pnl, sim_position.realized_pnl,
                sim_position.stop_loss, sim_position.take_profit, sim_position.created_at,
                sim_position.updated_at
            ))
            conn.commit()
    
    async def save_snapshot(self, snapshot: PortfolioSnapshot) -> None:
        """Save a portfolio snapshot to the database."""
        snapshot_id = f"snapshot_{snapshot.timestamp.isoformat()}"
        
        sim_snapshot = SimulationSnapshot(
            id=snapshot_id,
            timestamp=snapshot.timestamp,
            total_value=str(snapshot.total_value),
            cash=str(snapshot.cash),
            positions_value=str(snapshot.positions_value),
            unrealized_pnl=str(snapshot.unrealized_pnl),
            realized_pnl=str(snapshot.realized_pnl),
            total_pnl=str(snapshot.total_pnl),
            return_pct=str(snapshot.return_pct)
        )
        
        async with self.db_manager.get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO equity_snapshots_sim 
                (id, timestamp, total_value, cash, positions_value, unrealized_pnl, realized_pnl, total_pnl, return_pct)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                sim_snapshot.id, sim_snapshot.timestamp, sim_snapshot.total_value,
                sim_snapshot.cash, sim_snapshot.positions_value, sim_snapshot.unrealized_pnl,
                sim_snapshot.realized_pnl, sim_snapshot.total_pnl, sim_snapshot.return_pct
            ))
            conn.commit()
    
    async def get_orders(self, status: Optional[OrderStatus] = None) -> List[Order]:
        """Get simulation orders from the database."""
        async with self.db_manager.get_connection() as conn:
            if status:
                cursor = conn.execute(
                    "SELECT * FROM orders_sim WHERE status = ? ORDER BY created_at DESC",
                    (status.value,)
                )
            else:
                cursor = conn.execute("SELECT * FROM orders_sim ORDER BY created_at DESC")
            
            rows = cursor.fetchall()
            orders = []
            
            for row in rows:
                order = Order(
                    id=row[0],
                    pair=row[1],
                    side=OrderSide(row[2]),
                    order_type=OrderType(row[3]),
                    quantity=Decimal(row[4]),
                    price=Decimal(row[5]) if row[5] else None,
                    stop_price=Decimal(row[6]) if row[6] else None,
                    status=OrderStatus(row[7]),
                    created_at=datetime.fromisoformat(row[8]),
                    updated_at=datetime.fromisoformat(row[9]),
                    filled_at=datetime.fromisoformat(row[10]) if row[10] else None,
                    filled_quantity=Decimal(row[11]),
                    average_price=Decimal(row[12]) if row[12] else None,
                    commission=Decimal(row[13]),
                    metadata=json.loads(row[14])
                )
                orders.append(order)
            
            return orders
    
    async def get_trades(self) -> List[Trade]:
        """Get simulation trades from the database."""
        async with self.db_manager.get_connection() as conn:
            cursor = conn.execute("SELECT * FROM trades_sim ORDER BY timestamp DESC")
            rows = cursor.fetchall()
            trades = []
            
            for row in rows:
                trade = Trade(
                    id=row[0],
                    pair=row[1],
                    side=OrderSide(row[2]),
                    quantity=Decimal(row[3]),
                    price=Decimal(row[4]),
                    commission=Decimal(row[5]),
                    timestamp=datetime.fromisoformat(row[6]),
                    order_id=row[7],
                    position_id=row[8]
                )
                trades.append(trade)
            
            return trades
    
    async def get_positions(self) -> List[Position]:
        """Get simulation positions from the database."""
        async with self.db_manager.get_connection() as conn:
            cursor = conn.execute("SELECT * FROM positions_sim ORDER BY updated_at DESC")
            rows = cursor.fetchall()
            positions = []
            
            for row in rows:
                position = Position(
                    pair=row[1],
                    side=OrderSide(row[2]),
                    quantity=Decimal(row[3]),
                    average_price=Decimal(row[4]),
                    unrealized_pnl=Decimal(row[5]),
                    realized_pnl=Decimal(row[6]),
                    stop_loss=Decimal(row[7]) if row[7] else None,
                    take_profit=Decimal(row[8]) if row[8] else None,
                    created_at=datetime.fromisoformat(row[9]),
                    updated_at=datetime.fromisoformat(row[10])
                )
                positions.append(position)
            
            return positions
    
    async def get_snapshots(self, limit: int = 1000) -> List[PortfolioSnapshot]:
        """Get portfolio snapshots from the database."""
        async with self.db_manager.get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM equity_snapshots_sim ORDER BY timestamp DESC LIMIT ?",
                (limit,)
            )
            rows = cursor.fetchall()
            snapshots = []
            
            for row in rows:
                snapshot = PortfolioSnapshot(
                    timestamp=datetime.fromisoformat(row[1]),
                    total_value=Decimal(row[2]),
                    cash=Decimal(row[3]),
                    positions_value=Decimal(row[4]),
                    unrealized_pnl=Decimal(row[5]),
                    realized_pnl=Decimal(row[6]),
                    total_pnl=Decimal(row[7]),
                    return_pct=Decimal(row[8])
                )
                snapshots.append(snapshot)
            
            return snapshots
    
    async def clear_simulation_data(self) -> None:
        """Clear all simulation data."""
        async with self.db_manager.get_connection() as conn:
            conn.execute("DELETE FROM orders_sim")
            conn.execute("DELETE FROM trades_sim")
            conn.execute("DELETE FROM positions_sim")
            conn.execute("DELETE FROM equity_snapshots_sim")
            conn.commit()
            logger.info("Cleared all simulation data")
