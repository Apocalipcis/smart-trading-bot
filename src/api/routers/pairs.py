"""Pairs router for CRUD operations with trading pairs."""

from typing import List, Dict
from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from ..schemas import APIResponse, PaginatedResponse, TradingPair, PairValidationRequest, PairValidationResponse
from ...storage.pairs_service import get_pairs_service
from ...data.pair_validator import get_pair_validator

router = APIRouter(prefix="/pairs", tags=["pairs"])


@router.get("/", response_model=PaginatedResponse)
async def get_pairs(page: int = 1, size: int = 50) -> PaginatedResponse:
    """Get all trading pairs with pagination."""
    pairs_service = await get_pairs_service()
    result = await pairs_service.get_all_pairs(page=page, size=size)
    
    return PaginatedResponse(
        items=result['items'],
        total=result['total'],
        page=result['page'],
        size=result['size'],
        pages=result['pages']
    )


@router.get("/{pair_id}", response_model=TradingPair)
async def get_pair(pair_id: UUID) -> TradingPair:
    """Get a specific trading pair by ID."""
    pairs_service = await get_pairs_service()
    pair = await pairs_service.get_pair_by_id(pair_id)
    
    if not pair:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Trading pair with ID {pair_id} not found"
        )
    
    return pair


@router.post("/", response_model=TradingPair)
async def create_pair(pair: TradingPair) -> TradingPair:
    """Create a new trading pair."""
    # Validate that the pair exists on Binance
    pair_validator = await get_pair_validator()
    if not await pair_validator.is_valid_pair(pair.symbol):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Trading pair {pair.symbol} does not exist on Binance"
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
    
    # Create in database
    try:
        pairs_service = await get_pairs_service()
        created_pair = await pairs_service.create_pair(pair)
        return created_pair
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )


@router.put("/{pair_id}", response_model=TradingPair)
async def update_pair(pair_id: UUID, pair_update: TradingPair) -> TradingPair:
    """Update an existing trading pair."""
    pairs_service = await get_pairs_service()
    
    # Prepare updates (exclude id and symbol from updates)
    updates = {}
    if pair_update.strategy is not None:
        updates['strategy'] = pair_update.strategy
    if pair_update.is_active is not None:
        updates['is_active'] = pair_update.is_active
    if pair_update.base_asset is not None:
        updates['base_asset'] = pair_update.base_asset
    if pair_update.quote_asset is not None:
        updates['quote_asset'] = pair_update.quote_asset
    
    updated_pair = await pairs_service.update_pair(pair_id, updates)
    
    if not updated_pair:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Trading pair with ID {pair_id} not found"
        )
    
    return updated_pair


@router.delete("/{pair_id}", response_model=APIResponse)
async def delete_pair(pair_id: UUID) -> APIResponse:
    """Delete a trading pair."""
    pairs_service = await get_pairs_service()
    
    # Get pair info before deletion
    existing_pair = await pairs_service.get_pair_by_id(pair_id)
    if not existing_pair:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Trading pair with ID {pair_id} not found"
        )
    
    # Delete the pair
    success = await pairs_service.delete_pair(pair_id)
    
    if success:
        return APIResponse(
            success=True,
            message=f"Trading pair {existing_pair.symbol} deleted successfully"
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete trading pair"
        )


@router.patch("/{pair_id}/toggle", response_model=TradingPair)
async def toggle_pair_status(pair_id: UUID) -> TradingPair:
    """Toggle the active status of a trading pair."""
    pairs_service = await get_pairs_service()
    
    toggled_pair = await pairs_service.toggle_pair_status(pair_id)
    
    if not toggled_pair:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Trading pair with ID {pair_id} not found"
        )
    
    return toggled_pair


@router.post("/validate", response_model=PairValidationResponse)
async def validate_pair(request: PairValidationRequest) -> PairValidationResponse:
    """Validate if a trading pair exists on Binance."""
    pair_validator = await get_pair_validator()
    is_valid = await pair_validator.is_valid_pair(request.symbol)
    
    return PairValidationResponse(is_valid=is_valid, symbol=request.symbol)
