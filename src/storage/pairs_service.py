"""Service for managing trading pairs in the database."""

import logging
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4

from .db import get_db_manager
from ..api.schemas import TradingPair

logger = logging.getLogger(__name__)


class PairsService:
    """Service for managing trading pairs in the database."""
    
    async def create_pair(self, pair: TradingPair) -> TradingPair:
        """
        Create a new trading pair in the database.
        
        Args:
            pair: Trading pair to create
            
        Returns:
            TradingPair: Created trading pair with ID
            
        Raises:
            ValueError: If pair already exists
        """
        db = await get_db_manager()
        
        # Check if pair already exists
        existing = await self.get_pair_by_symbol(pair.symbol)
        if existing:
            raise ValueError(f"Trading pair {pair.symbol} already exists")
        
        # Prepare data for database
        pair_data = {
            'id': str(pair.id),
            'symbol': pair.symbol.upper(),
            'base_asset': pair.base_asset or '',
            'quote_asset': pair.quote_asset or '',
            'strategy': pair.strategy,
            'is_active': pair.is_active,
            'exchange': 'binance_futures',  # Default exchange
            'created_at': pair.created_at.isoformat(),
            'updated_at': pair.updated_at.isoformat()
        }
        
        # Insert into database
        query = """
            INSERT INTO pairs (
                id, symbol, base_asset, quote_asset, strategy, 
                is_active, exchange, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        await db.execute_insert(query, tuple(pair_data.values()))
        logger.info(f"Created trading pair: {pair.symbol}")
        
        return pair
    
    async def get_pair_by_id(self, pair_id: UUID) -> Optional[TradingPair]:
        """
        Get a trading pair by ID.
        
        Args:
            pair_id: Trading pair ID
            
        Returns:
            Optional[TradingPair]: Trading pair if found, None otherwise
        """
        db = await get_db_manager()
        
        query = "SELECT * FROM pairs WHERE id = ?"
        results = await db.execute_query(query, (str(pair_id),))
        
        if not results:
            return None
        
        return self._row_to_trading_pair(results[0])
    
    async def get_pair_by_symbol(self, symbol: str) -> Optional[TradingPair]:
        """
        Get a trading pair by symbol.
        
        Args:
            symbol: Trading pair symbol
            
        Returns:
            Optional[TradingPair]: Trading pair if found, None otherwise
        """
        db = await get_db_manager()
        
        query = "SELECT * FROM pairs WHERE symbol = ?"
        results = await db.execute_query(query, (symbol.upper(),))
        
        if not results:
            return None
        
        return self._row_to_trading_pair(results[0])
    
    async def get_all_pairs(self, page: int = 1, size: int = 50) -> Dict[str, Any]:
        """
        Get all trading pairs with pagination.
        
        Args:
            page: Page number (1-based)
            size: Page size
            
        Returns:
            Dict[str, Any]: Paginated results with total count
        """
        db = await get_db_manager()
        
        # Get total count
        count_query = "SELECT COUNT(*) FROM pairs"
        count_result = await db.execute_query(count_query)
        total = count_result[0]['COUNT(*)'] if count_result else 0
        
        # Calculate pagination
        offset = (page - 1) * size
        
        # Get paginated results
        query = "SELECT * FROM pairs ORDER BY created_at DESC LIMIT ? OFFSET ?"
        results = await db.execute_query(query, (size, offset))
        
        # Convert to TradingPair objects
        pairs = [self._row_to_trading_pair(row) for row in results]
        
        return {
            'items': pairs,
            'total': total,
            'page': page,
            'size': size,
            'pages': (total + size - 1) // size
        }
    
    async def update_pair(self, pair_id: UUID, updates: Dict[str, Any]) -> Optional[TradingPair]:
        """
        Update a trading pair.
        
        Args:
            pair_id: Trading pair ID
            updates: Fields to update
            
        Returns:
            Optional[TradingPair]: Updated trading pair if found, None otherwise
        """
        db = await get_db_manager()
        
        # Check if pair exists
        existing = await self.get_pair_by_id(pair_id)
        if not existing:
            return None
        
        # Prepare update query
        set_clauses = []
        params = []
        
        for field, value in updates.items():
            if field in ['strategy', 'is_active', 'base_asset', 'quote_asset']:
                set_clauses.append(f"{field} = ?")
                params.append(value)
        
        if not set_clauses:
            return existing
        
        # Add updated_at timestamp
        set_clauses.append("updated_at = ?")
        params.append(datetime.now(timezone.utc).isoformat())
        
        # Add pair_id to params
        params.append(str(pair_id))
        
        # Execute update
        query = f"UPDATE pairs SET {', '.join(set_clauses)} WHERE id = ?"
        await db.execute_update(query, tuple(params))
        
        logger.info(f"Updated trading pair: {existing.symbol}")
        
        # Return updated pair
        return await self.get_pair_by_id(pair_id)
    
    async def delete_pair(self, pair_id: UUID) -> bool:
        """
        Delete a trading pair.
        
        Args:
            pair_id: Trading pair ID
            
        Returns:
            bool: True if deleted, False if not found
        """
        db = await get_db_manager()
        
        # Check if pair exists
        existing = await self.get_pair_by_id(pair_id)
        if not existing:
            return False
        
        # Delete from database
        query = "DELETE FROM pairs WHERE id = ?"
        await db.execute_update(query, (str(pair_id),))
        
        logger.info(f"Deleted trading pair: {existing.symbol}")
        return True
    
    async def toggle_pair_status(self, pair_id: UUID) -> Optional[TradingPair]:
        """
        Toggle the active status of a trading pair.
        
        Args:
            pair_id: Trading pair ID
            
        Returns:
            Optional[TradingPair]: Updated trading pair if found, None otherwise
        """
        existing = await self.get_pair_by_id(pair_id)
        if not existing:
            return None
        
        # Toggle status
        new_status = not existing.is_active
        updates = {'is_active': new_status}
        
        return await self.update_pair(pair_id, updates)
    
    def _row_to_trading_pair(self, row: Dict[str, Any]) -> TradingPair:
        """Convert database row to TradingPair object."""
        from datetime import datetime
        
        # Parse datetime strings
        created_at = datetime.fromisoformat(row['created_at'].replace('Z', '+00:00'))
        updated_at = datetime.fromisoformat(row['updated_at'].replace('Z', '+00:00'))
        
        return TradingPair(
            id=UUID(row['id']),
            symbol=row['symbol'],
            base_asset=row['base_asset'],
            quote_asset=row['quote_asset'],
            strategy=row['strategy'],
            is_active=bool(row['is_active']),
            created_at=created_at,
            updated_at=updated_at
        )


# Global service instance
_pairs_service: Optional[PairsService] = None


async def get_pairs_service() -> PairsService:
    """Get the global pairs service instance."""
    global _pairs_service
    if _pairs_service is None:
        _pairs_service = PairsService()
    return _pairs_service
