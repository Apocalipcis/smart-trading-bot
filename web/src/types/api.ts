// API Response types
export interface ApiResponse<T> {
  data: T;
  message?: string;
  success: boolean;
}

// Trading Pair types
export interface TradingPair {
  id: string;
  symbol: string;
  base_asset: string;
  quote_asset: string;
  status: 'active' | 'inactive';
  created_at: string;
  updated_at: string;
}

export interface CreatePairRequest {
  symbol: string;
  base_asset: string;
  quote_asset: string;
}

// Signal types
export interface Signal {
  id: string;
  pair_id: string;
  strategy: string;
  side: 'buy' | 'sell';
  entry_price: number;
  stop_loss: number;
  take_profit: number;
  confidence: number;
  timestamp: string;
  status: 'active' | 'executed' | 'cancelled' | 'expired';
}

// Backtest types
export interface BacktestConfig {
  pair_id: string;
  strategy: string;
  timeframe: string;
  start_date: string;
  end_date: string;
  initial_balance: number;
  risk_per_trade: number;
  leverage: number;
}

export interface BacktestResult {
  id: string;
  config: BacktestConfig;
  status: 'running' | 'completed' | 'failed';
  created_at: string;
  completed_at?: string;
  metrics?: BacktestMetrics;
  error?: string;
}

export interface BacktestMetrics {
  total_trades: number;
  winning_trades: number;
  losing_trades: number;
  win_rate: number;
  total_return: number;
  max_drawdown: number;
  sharpe_ratio: number;
  profit_factor: number;
  average_win: number;
  average_loss: number;
  largest_win: number;
  largest_loss: number;
  total_commission: number;
  total_slippage: number;
}

// Order types
export interface Order {
  id: string;
  pair_id: string;
  signal_id: string;
  side: 'buy' | 'sell';
  order_type: 'market' | 'limit' | 'stop_market' | 'stop_limit' | 'trailing_stop';
  quantity: number;
  price?: number;
  stop_price?: number;
  status: 'pending' | 'filled' | 'cancelled' | 'rejected';
  created_at: string;
  filled_at?: string;
  filled_price?: number;
}

export interface CreateOrderRequest {
  signal_id: string;
  pair_id: string;
  side: 'buy' | 'sell';
  order_type: 'market' | 'limit' | 'stop_market' | 'stop_limit' | 'trailing_stop';
  quantity: number;
  price?: number;
  stop_price?: number;
}

// Settings types
export interface Settings {
  trading_enabled: boolean;
  order_confirmation_required: boolean;
  max_open_positions: number;
  risk_per_trade: number;
  default_leverage: number;
  telegram_enabled: boolean;
  telegram_bot_token?: string;
  telegram_chat_id?: string;
  // Backend-specific fields (optional for frontend compatibility)
  max_risk_per_trade?: number;
  min_risk_reward_ratio?: number;
  debug_mode?: boolean;
}

// Status types
export interface SystemStatus {
  status: 'healthy' | 'degraded' | 'unhealthy';
  uptime: number;
  version: string;
  trading_enabled: boolean;
  active_connections: number;
  last_signal_at?: string;
  last_order_at?: string;
}

// Pending confirmation types
export interface PendingConfirmation {
  id: string;
  signal_id: string;
  pair_id: string;
  side: 'buy' | 'sell';
  quantity: number;
  price: number;
  stop_loss: number;
  take_profit: number;
  created_at: string;
  expires_at: string;
}
