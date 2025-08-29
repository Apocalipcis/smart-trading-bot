"""Position sizing calculations based on risk management."""

import logging
from decimal import Decimal, ROUND_DOWN
from enum import Enum
from typing import Dict, Optional, Union

from pydantic import BaseModel, Field, field_validator, validator

logger = logging.getLogger(__name__)


class RiskModel(str, Enum):
    """Risk model enumeration."""
    FIXED_RISK = "fixed_risk"
    KELLY_CRITERION = "kelly_criterion"
    VOLATILITY_ADJUSTED = "volatility_adjusted"


class PositionSizer(BaseModel):
    """Position sizing calculator with risk management."""
    
    account_balance: Decimal = Field(..., description="Current account balance")
    risk_percentage: Decimal = Field(..., ge=0, le=100, description="Risk percentage per trade")
    max_leverage: int = Field(default=125, ge=1, le=125, description="Maximum leverage")
    min_position_size: Decimal = Field(default=Decimal('0.001'), description="Minimum position size")
    max_position_size: Optional[Decimal] = Field(None, description="Maximum position size")
    risk_model: RiskModel = Field(default=RiskModel.FIXED_RISK, description="Risk model to use")
    
    # Kelly criterion parameters
    win_rate: Optional[Decimal] = Field(None, ge=0, le=100, description="Expected win rate")
    avg_win: Optional[Decimal] = Field(None, description="Average win amount")
    avg_loss: Optional[Decimal] = Field(None, description="Average loss amount")
    
    # Volatility parameters
    volatility: Optional[Decimal] = Field(None, description="Asset volatility")
    target_volatility: Optional[Decimal] = Field(None, description="Target portfolio volatility")
    
    @field_validator('account_balance', 'risk_percentage', 'min_position_size', 'max_position_size', 
               'win_rate', 'avg_win', 'avg_loss', 'volatility', 'target_volatility', mode='before')
    @classmethod
    def validate_decimal(cls, v):
        """Convert to Decimal if string or float."""
        if v is None:
            return v
        return Decimal(str(v))
    
    @field_validator('risk_percentage')
    @classmethod
    def validate_risk_percentage(cls, v):
        """Ensure risk percentage is reasonable."""
        if v > 10:  # Max 10% risk per trade
            logger.warning(f"Risk percentage {v}% is high, consider reducing")
        return v
    
    def calculate_position_size(
        self,
        entry_price: Union[Decimal, float, str],
        stop_loss: Union[Decimal, float, str],
        leverage: int = 1,
        pair_info: Optional[Dict] = None
    ) -> Dict[str, Union[Decimal, str]]:
        """
        Calculate position size based on risk parameters.
        
        Args:
            entry_price: Entry price for the trade
            stop_loss: Stop loss price
            leverage: Leverage to use (1-125)
            pair_info: Exchange pair information (min_qty, step_size, etc.)
            
        Returns:
            Dict with position size and metadata
        """
        entry_price = Decimal(str(entry_price))
        stop_loss = Decimal(str(stop_loss))
        
        # Validate inputs
        if entry_price <= 0 or stop_loss <= 0:
            raise ValueError("Entry price and stop loss must be positive")
        
        if leverage < 1 or leverage > self.max_leverage:
            raise ValueError(f"Leverage must be between 1 and {self.max_leverage}")
        
        # Calculate risk amount
        risk_amount = self.account_balance * (self.risk_percentage / 100)
        
        # Calculate position size based on risk model
        if self.risk_model == RiskModel.FIXED_RISK:
            position_size = self._calculate_fixed_risk(entry_price, stop_loss, risk_amount)
        elif self.risk_model == RiskModel.KELLY_CRITERION:
            position_size = self._calculate_kelly_criterion(entry_price, stop_loss, risk_amount)
        elif self.risk_model == RiskModel.VOLATILITY_ADJUSTED:
            position_size = self._calculate_volatility_adjusted(entry_price, stop_loss, risk_amount)
        else:
            raise ValueError(f"Unknown risk model: {self.risk_model}")
        
        # Apply leverage
        leveraged_size = position_size * leverage
        
        # Apply size constraints
        final_size = self._apply_size_constraints(leveraged_size, pair_info)
        
        # Calculate actual risk
        actual_risk = self._calculate_actual_risk(entry_price, stop_loss, final_size)
        actual_risk_percentage = (actual_risk / self.account_balance) * 100
        
        return {
            "position_size": final_size,
            "risk_amount": actual_risk,
            "risk_percentage": actual_risk_percentage,
            "leverage": leverage,
            "entry_price": entry_price,
            "stop_loss": stop_loss,
            "risk_model": self.risk_model.value,
            "margin_required": (final_size * entry_price) / leverage,
            "notional_value": final_size * entry_price
        }
    
    def _calculate_fixed_risk(
        self, 
        entry_price: Decimal, 
        stop_loss: Decimal, 
        risk_amount: Decimal
    ) -> Decimal:
        """Calculate position size using fixed risk model."""
        # Calculate price difference
        if entry_price > stop_loss:  # Long position
            price_diff = entry_price - stop_loss
        else:  # Short position
            price_diff = stop_loss - entry_price
        
        if price_diff == 0:
            raise ValueError("Entry price and stop loss cannot be the same")
        
        # Position size = Risk amount / Price difference
        position_size = risk_amount / price_diff
        
        return position_size
    
    def _calculate_kelly_criterion(
        self, 
        entry_price: Decimal, 
        stop_loss: Decimal, 
        risk_amount: Decimal
    ) -> Decimal:
        """Calculate position size using Kelly criterion."""
        if not all([self.win_rate, self.avg_win, self.avg_loss]):
            logger.warning("Kelly criterion parameters not set, falling back to fixed risk")
            return self._calculate_fixed_risk(entry_price, stop_loss, risk_amount)
        
        # Kelly fraction = (bp - q) / b
        # where: b = odds received, p = probability of win, q = probability of loss
        win_prob = self.win_rate / 100
        loss_prob = 1 - win_prob
        
        # Calculate odds (avg_win / avg_loss)
        odds = self.avg_win / self.avg_loss
        
        # Kelly fraction
        kelly_fraction = (odds * win_prob - loss_prob) / odds
        
        # Apply Kelly fraction to fixed risk calculation
        base_size = self._calculate_fixed_risk(entry_price, stop_loss, risk_amount)
        kelly_size = base_size * kelly_fraction
        
        # Cap at 25% of account to be conservative
        max_kelly = self.account_balance * Decimal('0.25') / entry_price
        return min(kelly_size, max_kelly)
    
    def _calculate_volatility_adjusted(
        self, 
        entry_price: Decimal, 
        stop_loss: Decimal, 
        risk_amount: Decimal
    ) -> Decimal:
        """Calculate position size using volatility-adjusted model."""
        if not self.volatility or not self.target_volatility:
            logger.warning("Volatility parameters not set, falling back to fixed risk")
            return self._calculate_fixed_risk(entry_price, stop_loss, risk_amount)
        
        # Calculate base position size
        base_size = self._calculate_fixed_risk(entry_price, stop_loss, risk_amount)
        
        # Adjust for volatility
        volatility_ratio = self.target_volatility / self.volatility
        adjusted_size = base_size * volatility_ratio
        
        return adjusted_size
    
    def _apply_size_constraints(
        self, 
        position_size: Decimal, 
        pair_info: Optional[Dict] = None
    ) -> Decimal:
        """Apply size constraints based on exchange limits and user preferences."""
        final_size = position_size
        
        # Apply minimum size constraint
        if final_size < self.min_position_size:
            logger.warning(f"Position size {final_size} below minimum {self.min_position_size}")
            final_size = self.min_position_size
        
        # Apply maximum size constraint
        if self.max_position_size and final_size > self.max_position_size:
            logger.warning(f"Position size {final_size} above maximum {self.max_position_size}")
            final_size = self.max_position_size
        
        # Apply exchange constraints if available
        if pair_info:
            min_qty = pair_info.get('min_qty')
            step_size = pair_info.get('step_size')
            
            if min_qty and final_size < Decimal(str(min_qty)):
                logger.warning(f"Position size {final_size} below exchange minimum {min_qty}")
                final_size = Decimal(str(min_qty))
            
            if step_size:
                # Round down to nearest step size
                step_size = Decimal(str(step_size))
                final_size = (final_size // step_size) * step_size
        
        return final_size
    
    def _calculate_actual_risk(
        self, 
        entry_price: Decimal, 
        stop_loss: Decimal, 
        position_size: Decimal
    ) -> Decimal:
        """Calculate actual risk amount for the position."""
        if entry_price > stop_loss:  # Long position
            price_diff = entry_price - stop_loss
        else:  # Short position
            price_diff = stop_loss - entry_price
        
        return position_size * price_diff
    
    def calculate_margin_requirement(
        self, 
        position_size: Decimal, 
        entry_price: Decimal, 
        leverage: int
    ) -> Decimal:
        """Calculate margin requirement for the position."""
        notional_value = position_size * entry_price
        margin_required = notional_value / leverage
        return margin_required
    
    def validate_margin_sufficiency(
        self, 
        margin_required: Decimal, 
        available_balance: Optional[Decimal] = None
    ) -> bool:
        """Validate if there's sufficient margin for the position."""
        balance = available_balance or self.account_balance
        return margin_required <= balance
    
    def get_risk_summary(self) -> Dict[str, Union[Decimal, str]]:
        """Get a summary of current risk parameters."""
        return {
            "account_balance": self.account_balance,
            "risk_percentage": self.risk_percentage,
            "max_leverage": self.max_leverage,
            "risk_model": self.risk_model.value,
            "max_risk_per_trade": self.account_balance * (self.risk_percentage / 100),
            "min_position_size": self.min_position_size,
            "max_position_size": self.max_position_size
        }
