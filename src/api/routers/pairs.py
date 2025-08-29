"""Pairs router for CRUD operations with trading pairs."""

from typing import List
from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from ..schemas import APIResponse, PaginatedResponse, TradingPair

router = APIRouter(prefix="/pairs", tags=["pairs"])

# In-memory storage for pairs (will be replaced with database)
_pairs: List[TradingPair] = []


@router.get("/", response_model=PaginatedResponse)
async def get_pairs(page: int = 1, size: int = 50) -> PaginatedResponse:
    """Get all trading pairs with pagination."""
    start_idx = (page - 1) * size
    end_idx = start_idx + size
    
    total = len(_pairs)
    items = _pairs[start_idx:end_idx]
    pages = (total + size - 1) // size
    
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        size=size,
        pages=pages
    )


@router.get("/{pair_id}", response_model=TradingPair)
async def get_pair(pair_id: UUID) -> TradingPair:
    """Get a specific trading pair by ID."""
    for pair in _pairs:
        if pair.id == pair_id:
            return pair
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Trading pair with ID {pair_id} not found"
    )


@router.post("/", response_model=TradingPair)
async def create_pair(pair: TradingPair) -> TradingPair:
    """Create a new trading pair."""
    # Check if pair already exists
    for existing_pair in _pairs:
        if existing_pair.symbol.upper() == pair.symbol.upper():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Trading pair {pair.symbol} already exists"
            )
    
    # Auto-extract base_asset and quote_asset from symbol if not provided
    if not pair.base_asset or not pair.quote_asset:
        # Try to extract from symbol (e.g., BTCUSDT -> BTC, USDT)
        symbol = pair.symbol.upper()
        if len(symbol) >= 6:  # Minimum length for a valid pair
            # Common patterns: BTCUSDT, ETHUSDT, etc.
            if symbol.endswith('USDT'):
                base_asset = symbol[:-4]
                quote_asset = 'USDT'
            elif symbol.endswith('BTC'):
                base_asset = symbol[:-3]
                quote_asset = 'BTC'
            elif symbol.endswith('ETH'):
                base_asset = symbol[:-3]
                quote_asset = 'ETH'
            else:
                # Fallback: split in the middle
                mid = len(symbol) // 2
                base_asset = symbol[:mid]
                quote_asset = symbol[mid:]
        else:
            base_asset = symbol
            quote_asset = 'USDT'  # Default quote asset
        
        # Update the pair with extracted values
        pair.base_asset = base_asset
        pair.quote_asset = quote_asset
    
    # Add to storage
    _pairs.append(pair)
    return pair


@router.put("/{pair_id}", response_model=TradingPair)
async def update_pair(pair_id: UUID, pair_update: TradingPair) -> TradingPair:
    """Update an existing trading pair."""
    for i, existing_pair in enumerate(_pairs):
        if existing_pair.id == pair_id:
            # Update the pair but keep the original ID and symbol
            pair_update.id = existing_pair.id
            pair_update.symbol = existing_pair.symbol
            _pairs[i] = pair_update
            return pair_update
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Trading pair with ID {pair_id} not found"
    )


@router.delete("/{pair_id}", response_model=APIResponse)
async def delete_pair(pair_id: UUID) -> APIResponse:
    """Delete a trading pair."""
    for i, existing_pair in enumerate(_pairs):
        if existing_pair.id == pair_id:
            del _pairs[i]
            return APIResponse(
                success=True,
                message=f"Trading pair {existing_pair.symbol} deleted successfully"
            )
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Trading pair with ID {pair_id} not found"
    )


@router.patch("/{pair_id}/toggle", response_model=TradingPair)
async def toggle_pair_status(pair_id: UUID) -> TradingPair:
    """Toggle the active status of a trading pair."""
    for i, existing_pair in enumerate(_pairs):
        if existing_pair.id == pair_id:
            # Toggle the status
            existing_pair.is_active = not existing_pair.is_active
            return existing_pair
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Trading pair with ID {pair_id} not found"
    )
