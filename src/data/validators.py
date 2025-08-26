"""
Binance exchange validations for price, quantity, and order rules.
"""
import math
from typing import Dict, Any, Optional, Tuple
from pydantic import BaseModel, Field


class SymbolInfo(BaseModel):
    """Symbol information with validation rules."""
    symbol: str
    status: str
    base_asset: str
    quote_asset: str
    price_precision: int
    quantity_precision: int
    base_asset_precision: int
    quote_precision: int
    min_notional: float
    tick_size: float
    step_size: float
    min_qty: float
    max_qty: float
    min_price: float
    max_price: float


class BinanceValidator:
    """Validates Binance exchange rules and constraints."""
    
    def __init__(self):
        self._symbol_info: Dict[str, SymbolInfo] = {}
    
    def set_symbol_info(self, symbol: str, info: Dict[str, Any]) -> None:
        """Set symbol information from exchange info response."""
        filters = {f['filterType']: f for f in info.get('filters', [])}
        
        price_filter = filters.get('PRICE_FILTER', {})
        lot_size_filter = filters.get('LOT_SIZE', {})
        notional_filter = filters.get('MIN_NOTIONAL', {})
        
        symbol_info = SymbolInfo(
            symbol=info['symbol'],
            status=info['status'],
            base_asset=info['baseAsset'],
            quote_asset=info['quoteAsset'],
            price_precision=info['pricePrecision'],
            quantity_precision=info['quantityPrecision'],
            base_asset_precision=info['baseAssetPrecision'],
            quote_precision=info['quotePrecision'],
            min_notional=float(notional_filter.get('minNotional', 0)),
            tick_size=float(price_filter.get('tickSize', 0.00000001)),
            step_size=float(lot_size_filter.get('stepSize', 0.00000001)),
            min_qty=float(lot_size_filter.get('minQty', 0)),
            max_qty=float(lot_size_filter.get('maxQty', float('inf'))),
            min_price=float(price_filter.get('minPrice', 0)),
            max_price=float(price_filter.get('maxPrice', float('inf')))
        )
        
        self._symbol_info[symbol.upper()] = symbol_info
    
    def get_symbol_info(self, symbol: str) -> Optional[SymbolInfo]:
        """Get symbol information."""
        return self._symbol_info.get(symbol.upper())
    
    def validate_price(self, symbol: str, price: float) -> Tuple[bool, str]:
        """Validate price against exchange rules."""
        info = self.get_symbol_info(symbol)
        if not info:
            return False, f"Symbol {symbol} not found"
        
        # Check price range
        if price < info.min_price:
            return False, f"Price {price} below minimum {info.min_price}"
        if price > info.max_price:
            return False, f"Price {price} above maximum {info.max_price}"
        
        # Check tick size alignment
        if not self._is_valid_tick_size(price, info.tick_size):
            return False, f"Price {price} not aligned with tick size {info.tick_size}"
        
        return True, "Price valid"
    
    def validate_quantity(self, symbol: str, quantity: float) -> Tuple[bool, str]:
        """Validate quantity against exchange rules."""
        info = self.get_symbol_info(symbol)
        if not info:
            return False, f"Symbol {symbol} not found"
        
        # Check quantity range
        if quantity < info.min_qty:
            return False, f"Quantity {quantity} below minimum {info.min_qty}"
        if quantity > info.max_qty:
            return False, f"Quantity {quantity} above maximum {info.max_qty}"
        
        # Check step size alignment
        if not self._is_valid_step_size(quantity, info.step_size):
            return False, f"Quantity {quantity} not aligned with step size {info.step_size}"
        
        return True, "Quantity valid"
    
    def validate_notional(self, symbol: str, price: float, quantity: float) -> Tuple[bool, str]:
        """Validate notional value against minimum requirements."""
        info = self.get_symbol_info(symbol)
        if not info:
            return False, f"Symbol {symbol} not found"
        
        notional = price * quantity
        if notional < info.min_notional:
            return False, f"Notional {notional} below minimum {info.min_notional}"
        
        return True, "Notional valid"
    
    def validate_order(self, symbol: str, price: float, quantity: float) -> Tuple[bool, str]:
        """Validate complete order parameters."""
        # Validate price
        price_valid, price_msg = self.validate_price(symbol, price)
        if not price_valid:
            return False, price_msg
        
        # Validate quantity
        qty_valid, qty_msg = self.validate_quantity(symbol, quantity)
        if not qty_valid:
            return False, qty_msg
        
        # Validate notional
        notional_valid, notional_msg = self.validate_notional(symbol, price, quantity)
        if not notional_valid:
            return False, notional_msg
        
        return True, "Order valid"
    
    def normalize_price(self, symbol: str, price: float) -> float:
        """Normalize price to valid tick size."""
        info = self.get_symbol_info(symbol)
        if not info:
            return price
        
        tick_size = info.tick_size
        normalized = round(price / tick_size) * tick_size
        return round(normalized, info.price_precision)
    
    def normalize_quantity(self, symbol: str, quantity: float) -> float:
        """Normalize quantity to valid step size."""
        info = self.get_symbol_info(symbol)
        if not info:
            return quantity
        
        step_size = info.step_size
        normalized = round(quantity / step_size) * step_size
        return round(normalized, info.quantity_precision)
    
    def _is_valid_tick_size(self, price: float, tick_size: float) -> bool:
        """Check if price aligns with tick size."""
        if tick_size == 0:
            return True
        return abs(price - round(price / tick_size) * tick_size) < 1e-10
    
    def _is_valid_step_size(self, quantity: float, step_size: float) -> bool:
        """Check if quantity aligns with step size."""
        if step_size == 0:
            return True
        return abs(quantity - round(quantity / step_size) * step_size) < 1e-10
    
    def get_precision_info(self, symbol: str) -> Optional[Dict[str, int]]:
        """Get precision information for a symbol."""
        info = self.get_symbol_info(symbol)
        if not info:
            return None
        
        return {
            'price_precision': info.price_precision,
            'quantity_precision': info.quantity_precision,
            'base_asset_precision': info.base_asset_precision,
            'quote_precision': info.quote_precision
        }
