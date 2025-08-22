"""Mock SMC (Smart Money Concepts) engine for view-only mode."""

import logging
from typing import List, Dict, Any
from datetime import datetime, timedelta
import random

logger = logging.getLogger(__name__)


class MockSMCEngine:
    """Mock SMC engine for generating sample signals in view-only mode."""
    
    def __init__(self):
        self.signal_types = ['BOS', 'CHOCH', 'FVG', 'SWEEP']
        self.directions = ['LONG', 'SHORT']
        
    def generate_sample_signals(self, symbol: str, timeframe: str, count: int = 5) -> List[Dict[str, Any]]:
        """Generate sample SMC signals for demonstration."""
        signals = []
        
        for i in range(count):
            # Generate random signal
            signal_type = random.choice(self.signal_types)
            direction = random.choice(self.directions)
            
            # Generate timestamp (recent past)
            hours_ago = random.randint(1, 24)
            timestamp = datetime.utcnow() - timedelta(hours=hours_ago)
            
            # Generate mock price data
            base_price = 50000 if symbol == 'BTCUSDT' else 3000 if symbol == 'ETHUSDT' else 300
            price_variation = random.uniform(0.95, 1.05)
            price = base_price * price_variation
            
            signal = {
                'id': f"signal_{symbol}_{timeframe}_{i}_{int(timestamp.timestamp())}",
                'symbol': symbol,
                'timeframe': timeframe,
                'type': signal_type,
                'direction': direction,
                'price': round(price, 2),
                'timestamp': timestamp.isoformat(),
                'strength': random.choice(['WEAK', 'MEDIUM', 'STRONG']),
                'confidence': round(random.uniform(0.6, 0.95), 2),
                'description': f"{signal_type} signal detected for {symbol} on {timeframe} timeframe"
            }
            
            signals.append(signal)
            
        return signals
        
    def analyze_candles(self, candles: List[Any]) -> List[Dict[str, Any]]:
        """Mock candle analysis (returns sample signals)."""
        if not candles:
            return []
            
        # Extract symbol and timeframe from first candle
        symbol = candles[0].symbol if hasattr(candles[0], 'symbol') else 'BTCUSDT'
        timeframe = candles[0].timeframe if hasattr(candles[0], 'timeframe') else '1h'
        
        # Generate 2-3 sample signals
        signal_count = random.randint(2, 3)
        return self.generate_sample_signals(symbol, timeframe, signal_count)
        
    def get_signal_statistics(self) -> Dict[str, Any]:
        """Get mock signal statistics."""
        return {
            'total_signals': 42,
            'long_signals': 23,
            'short_signals': 19,
            'win_rate': 0.68,
            'avg_confidence': 0.78,
            'strong_signals': 15,
            'medium_signals': 20,
            'weak_signals': 7
        }
