"""Markets router for market data and timeframe information."""

from typing import List
from fastapi import APIRouter, HTTPException, status

from ..schemas import (
    AvailableTimeframes, 
    AvailableTimeframe, 
    TimeframeConstraint, 
    TimeframeRole,
    APIResponse
)

router = APIRouter(prefix="/markets", tags=["markets"])

# Available timeframes with their metadata
AVAILABLE_TIMEFRAMES = [
    AvailableTimeframe(
        timeframe="1m",
        description="1 minute",
        minutes=1,
        supported_roles=[TimeframeRole.LTF],
        is_active=True
    ),
    AvailableTimeframe(
        timeframe="3m",
        description="3 minutes",
        minutes=3,
        supported_roles=[TimeframeRole.LTF],
        is_active=True
    ),
    AvailableTimeframe(
        timeframe="5m",
        description="5 minutes",
        minutes=5,
        supported_roles=[TimeframeRole.LTF],
        is_active=True
    ),
    AvailableTimeframe(
        timeframe="15m",
        description="15 minutes",
        minutes=15,
        supported_roles=[TimeframeRole.LTF, TimeframeRole.HTF],
        is_active=True
    ),
    AvailableTimeframe(
        timeframe="30m",
        description="30 minutes",
        minutes=30,
        supported_roles=[TimeframeRole.LTF, TimeframeRole.HTF],
        is_active=True
    ),
    AvailableTimeframe(
        timeframe="1h",
        description="1 hour",
        minutes=60,
        supported_roles=[TimeframeRole.LTF, TimeframeRole.HTF],
        is_active=True
    ),
    AvailableTimeframe(
        timeframe="2h",
        description="2 hours",
        minutes=120,
        supported_roles=[TimeframeRole.HTF],
        is_active=True
    ),
    AvailableTimeframe(
        timeframe="4h",
        description="4 hours",
        minutes=240,
        supported_roles=[TimeframeRole.HTF],
        is_active=True
    ),
    AvailableTimeframe(
        timeframe="6h",
        description="6 hours",
        minutes=360,
        supported_roles=[TimeframeRole.HTF],
        is_active=True
    ),
    AvailableTimeframe(
        timeframe="8h",
        description="8 hours",
        minutes=480,
        supported_roles=[TimeframeRole.HTF],
        is_active=True
    ),
    AvailableTimeframe(
        timeframe="12h",
        description="12 hours",
        minutes=720,
        supported_roles=[TimeframeRole.HTF],
        is_active=True
    ),
    AvailableTimeframe(
        timeframe="1d",
        description="1 day",
        minutes=1440,
        supported_roles=[TimeframeRole.HTF],
        is_active=True
    ),
    AvailableTimeframe(
        timeframe="3d",
        description="3 days",
        minutes=4320,
        supported_roles=[TimeframeRole.HTF],
        is_active=True
    ),
    AvailableTimeframe(
        timeframe="1w",
        description="1 week",
        minutes=10080,
        supported_roles=[TimeframeRole.HTF],
        is_active=True
    ),
    AvailableTimeframe(
        timeframe="1M",
        description="1 month",
        minutes=43200,
        supported_roles=[TimeframeRole.HTF],
        is_active=True
    ),
]

# Role constraints
ROLE_CONSTRAINTS = [
    TimeframeConstraint(
        role=TimeframeRole.HTF,
        min_timeframe="1h",
        max_timeframe="1d",
        description="Higher timeframes should be 1h or greater for trend analysis"
    ),
    TimeframeConstraint(
        role=TimeframeRole.LTF,
        min_timeframe="1m",
        max_timeframe="30m",
        description="Lower timeframes should be 30m or less for entry/exit timing"
    ),
]


@router.get("/timeframes", response_model=AvailableTimeframes)
async def get_available_timeframes() -> AvailableTimeframes:
    """Get all available timeframes with their metadata and role support."""
    return AvailableTimeframes(
        timeframes=AVAILABLE_TIMEFRAMES,
        default_htf="1h",
        default_ltf="15m",
        role_constraints=ROLE_CONSTRAINTS
    )


@router.get("/timeframes/roles", response_model=List[TimeframeConstraint])
async def get_timeframe_role_constraints() -> List[TimeframeConstraint]:
    """Get timeframe role constraints and validation rules."""
    return ROLE_CONSTRAINTS


@router.get("/timeframes/{timeframe}", response_model=AvailableTimeframe)
async def get_timeframe_info(timeframe: str) -> AvailableTimeframe:
    """Get information about a specific timeframe."""
    for tf in AVAILABLE_TIMEFRAMES:
        if tf.timeframe == timeframe:
            return tf
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Timeframe '{timeframe}' not found"
    )


@router.post("/timeframes/validate")
async def validate_timeframe_roles(
    timeframes: List[str],
    tf_roles: dict
) -> APIResponse:
    """Validate timeframe role assignments."""
    errors = []
    warnings = []
    
    # Check if all timeframes exist
    available_tf_strings = [tf.timeframe for tf in AVAILABLE_TIMEFRAMES]
    for tf in timeframes:
        if tf not in available_tf_strings:
            errors.append(f"Timeframe '{tf}' is not available")
    
    # Check role assignments
    for tf, role in tf_roles.items():
        if tf not in timeframes:
            errors.append(f"Role assigned for non-existent timeframe '{tf}'")
            continue
            
        # Find timeframe info
        tf_info = None
        for atf in AVAILABLE_TIMEFRAMES:
            if atf.timeframe == tf:
                tf_info = atf
                break
        
        if tf_info and role not in tf_info.supported_roles:
            warnings.append(f"Role '{role}' is not typically used for timeframe '{tf}'")
    
    # Check role constraints
    for constraint in ROLE_CONSTRAINTS:
        for tf, role in tf_roles.items():
            if role == constraint.role:
                try:
                    # Validate against min/max constraints
                    tf_minutes = _timeframe_to_minutes(tf)
                    min_minutes = _timeframe_to_minutes(constraint.min_timeframe)
                    max_minutes = _timeframe_to_minutes(constraint.max_timeframe)
                    
                    if tf_minutes < min_minutes:
                        errors.append(f"Timeframe '{tf}' is too small for role '{role}'. Minimum: {constraint.min_timeframe}")
                    elif tf_minutes > max_minutes:
                        errors.append(f"Timeframe '{tf}' is too large for role '{role}'. Maximum: {constraint.max_timeframe}")
                except ValueError:
                    # Invalid timeframe format - this should already be caught by the timeframe existence check
                    # but we'll add it here as a fallback
                    errors.append(f"Invalid timeframe format: '{tf}'")
    
    return APIResponse(
        success=len(errors) == 0,
        data={
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        },
        message="Timeframe role validation completed"
    )


def _timeframe_to_minutes(timeframe: str) -> int:
    """Convert timeframe string to minutes."""
    if timeframe.endswith('m'):
        return int(timeframe[:-1])
    elif timeframe.endswith('h'):
        return int(timeframe[:-1]) * 60
    elif timeframe.endswith('d'):
        return int(timeframe[:-1]) * 1440
    elif timeframe.endswith('w'):
        return int(timeframe[:-1]) * 10080
    elif timeframe.endswith('M'):
        return int(timeframe[:-1]) * 43200
    else:
        raise ValueError(f"Invalid timeframe format: {timeframe}")
