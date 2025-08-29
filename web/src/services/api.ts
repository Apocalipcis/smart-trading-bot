import axios from 'axios';
import type { AxiosInstance } from 'axios';
import {
  ApiResponse,
  TradingPair,
  CreatePairRequest,
  Signal,
  BacktestConfig,
  BacktestResult,
  Order,
  CreateOrderRequest,
  Settings,
  SystemStatus,
  PendingConfirmation,
  AvailableTimeframes,
  TimeframeConstraint,
  AvailableTimeframe,
  TimeframeRole,
  StrategyMetadata,
} from '../types/api';

class ApiClient {
  private client: AxiosInstance;
  private baseURL: string;

  constructor() {
    // In development, use relative URLs to work with Vite proxy
    // In production, use the configured API URL or relative URLs for Docker
    this.baseURL = import.meta.env.VITE_API_URL || '';
    
    // For development with proxy, use relative URLs
    if (import.meta.env.DEV && !this.baseURL) {
      this.baseURL = '';
    }
    
    this.client = axios.create({
      baseURL: this.baseURL,
      timeout: 10000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Add request interceptor for logging
    this.client.interceptors.request.use(
      (config) => {
        console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`);
        return config;
      },
      (error) => {
        console.error('API Request Error:', error);
        return Promise.reject(error);
      }
    );

    // Add response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => {
        return response;
      },
      (error) => {
        if (error.response?.status === 403) {
          console.warn('API access forbidden - trading may be disabled:', error.response?.data?.detail || error.message);
        } else {
          console.error('API Response Error:', error.response?.data || error.message);
        }
        return Promise.reject(error);
      }
    );
  }

  // Trading Pairs
  async getPairs(): Promise<TradingPair[]> {
    const response = await this.client.get<ApiResponse<TradingPair[]>>('/api/v1/pairs');
    return response.data.data;
  }

  async createPair(pair: CreatePairRequest): Promise<TradingPair> {
    const response = await this.client.post<ApiResponse<TradingPair>>('/api/v1/pairs', pair);
    return response.data.data;
  }

  async deletePair(pairId: string): Promise<void> {
    await this.client.delete(`/api/v1/pairs/${pairId}`);
  }

  // Signals
  async getSignals(limit?: number): Promise<Signal[]> {
    const params = limit ? { limit } : {};
    const response = await this.client.get<ApiResponse<Signal[]>>('/api/v1/signals', { params });
    return response.data.data;
  }

  // Backtests
  async getBacktests(): Promise<BacktestResult[]> {
    const response = await this.client.get<any>('/api/v1/backtests');
    // Backend returns PaginatedResponse, not ApiResponse
    return response.data.items || [];
  }

  async createBacktest(config: BacktestConfig): Promise<BacktestResult> {
    const response = await this.client.post<any>('/api/v1/backtests', config);
    // Backend returns BacktestResult directly, not wrapped in ApiResponse
    return response.data;
  }

  async getBacktest(backtestId: string): Promise<BacktestResult> {
    const response = await this.client.get<any>(`/api/v1/backtests/${backtestId}`);
    // Backend returns BacktestResult directly, not wrapped in ApiResponse
    return response.data;
  }

  async deleteBacktest(backtestId: string): Promise<void> {
    await this.client.delete(`/api/v1/backtests/${backtestId}`);
  }

  async deleteAllBacktests(): Promise<void> {
    await this.client.delete('/api/v1/backtests');
  }

  // Markets
  async getAvailableTimeframes(): Promise<AvailableTimeframes> {
    const response = await this.client.get<ApiResponse<AvailableTimeframes>>('/api/v1/markets/timeframes');
    return response.data.data;
  }

  async getTimeframeRoleConstraints(): Promise<TimeframeConstraint[]> {
    const response = await this.client.get<ApiResponse<TimeframeConstraint[]>>('/api/v1/markets/timeframes/roles');
    return response.data.data;
  }

  async getTimeframeInfo(timeframe: string): Promise<AvailableTimeframe> {
    const response = await this.client.get<ApiResponse<AvailableTimeframe>>(`/api/v1/markets/timeframes/${timeframe}`);
    return response.data.data;
  }

  async validateTimeframeRoles(timeframes: string[], tfRoles: Record<string, TimeframeRole>): Promise<any> {
    const params = {
      timeframes: timeframes.join(','),
      tf_roles: JSON.stringify(tfRoles)
    };
    const response = await this.client.get<ApiResponse<any>>('/api/v1/markets/timeframes/validate', { params });
    return response.data.data;
  }

  // Strategies
  async getStrategies(): Promise<StrategyMetadata[]> {
    const response = await this.client.get<ApiResponse<StrategyMetadata[]>>('/api/v1/strategies');
    return response.data.data;
  }

  async getStrategy(strategyName: string): Promise<StrategyMetadata> {
    const response = await this.client.get<ApiResponse<StrategyMetadata>>(`/api/v1/strategies/${strategyName}`);
    return response.data.data;
  }

  async validateStrategyRequirements(
    strategyName: string, 
    timeframes: string[], 
    tfRoles: Record<string, TimeframeRole>
  ): Promise<any> {
    const params = {
      timeframes: timeframes.join(','),
      tf_roles: JSON.stringify(tfRoles)
    };
    const response = await this.client.get<ApiResponse<any>>(`/api/v1/strategies/${strategyName}/validate`, { params });
    return response.data.data;
  }

  async getStrategyParameters(strategyName: string): Promise<any> {
    const response = await this.client.get<ApiResponse<any>>(`/api/v1/strategies/${strategyName}/parameters`);
    return response.data.data;
  }

  // Orders
  async getOrders(): Promise<Order[]> {
    const response = await this.client.get<ApiResponse<Order[]>>('/api/v1/orders');
    return response.data.data;
  }

  async createOrder(order: CreateOrderRequest): Promise<Order> {
    const response = await this.client.post<ApiResponse<Order>>('/api/v1/orders', order);
    return response.data.data;
  }

  // Settings
  async getSettings(): Promise<Settings> {
    const response = await this.client.get<ApiResponse<Settings>>('/api/v1/settings');
    return response.data.data;
  }

  async updateSettings(settings: Partial<Settings>): Promise<Settings> {
    const response = await this.client.put<ApiResponse<Settings>>('/api/v1/settings', settings);
    return response.data.data;
  }

  // Status
  async getStatus(): Promise<SystemStatus> {
    const response = await this.client.get<ApiResponse<SystemStatus>>('/api/v1/status/health');
    return response.data.data;
  }

  // Pending Confirmations
  async getPendingConfirmations(): Promise<PendingConfirmation[]> {
    const response = await this.client.get<ApiResponse<PendingConfirmation[]>>('/api/v1/orders/pending');
    return response.data.data;
  }

  async confirmOrder(confirmationId: string): Promise<Order> {
    const response = await this.client.post<ApiResponse<Order>>(`/api/v1/orders/pending/${confirmationId}/confirm`);
    return response.data.data;
  }

  async rejectOrder(confirmationId: string): Promise<void> {
    await this.client.post(`/api/v1/orders/pending/${confirmationId}/reject`);
  }

  // Notifications
  async testNotification(): Promise<void> {
    await this.client.post('/api/v1/notifications/test');
  }

  // SSE for real-time signals
  getSignalsStream(): EventSource {
    return new EventSource(`${this.baseURL}/api/v1/signals/stream`);
  }
}

export const apiClient = new ApiClient();
export default apiClient;
