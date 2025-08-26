"""Pairs router for CRUD operations with trading pairs."""

from typing import List

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


@router.get("/{symbol}", response_model=TradingPair)
async def get_pair(symbol: str) -> TradingPair:
    """Get a specific trading pair by symbol."""
    for pair in _pairs:
        if pair.symbol.upper() == symbol.upper():
            return pair
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Trading pair {symbol} not found"
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
    
    # Add to storage
    _pairs.append(pair)
    return pair


@router.put("/{symbol}", response_model=TradingPair)
async def update_pair(symbol: str, pair_update: TradingPair) -> TradingPair:
    """Update an existing trading pair."""
    for i, existing_pair in enumerate(_pairs):
        if existing_pair.symbol.upper() == symbol.upper():
            # Update the pair
            pair_update.symbol = existing_pair.symbol  # Keep original symbol
            _pairs[i] = pair_update
            return pair_update
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Trading pair {symbol} not found"
    )


@router.delete("/{symbol}", response_model=APIResponse)
async def delete_pair(symbol: str) -> APIResponse:
    """Delete a trading pair."""
    for i, existing_pair in enumerate(_pairs):
        if existing_pair.symbol.upper() == symbol.upper():
            del _pairs[i]
            return APIResponse(
                success=True,
                message=f"Trading pair {symbol} deleted successfully"
            )
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Trading pair {symbol} not found"
    )


@router.patch("/{symbol}/toggle", response_model=TradingPair)
async def toggle_pair_status(symbol: str) -> TradingPair:
    """Toggle the active status of a trading pair."""
    for i, existing_pair in enumerate(_pairs):
        if existing_pair.symbol.upper() == symbol.upper():
            # Toggle the status
            existing_pair.is_active = not existing_pair.is_active
            return existing_pair
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Trading pair {symbol} not found"
    )
