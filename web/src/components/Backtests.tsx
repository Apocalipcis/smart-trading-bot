import React, { useState, useEffect } from 'react';
import { Play, Trash2, Eye, BarChart3, AlertTriangle, X } from 'lucide-react';
import { BacktestConfig, BacktestResult, TradingPair } from '../types/api';
import apiClient from '../services/api';

const Backtests: React.FC = () => {
  const [backtests, setBacktests] = useState<BacktestResult[]>([]);
  const [pairs, setPairs] = useState<TradingPair[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [selectedBacktest, setSelectedBacktest] = useState<BacktestResult | null>(null);
  const [formData, setFormData] = useState<BacktestConfig>({
    pair_id: '',
    strategy: 'smc',
    timeframe: '1h',
    start_date: '',
    end_date: '',
    initial_balance: 10000,
    risk_per_trade: 2,
    leverage: 1,
  });

  const strategies = [
    { value: 'smc', label: 'Smart Money Concepts (SMC)' },
    { value: 'rsi', label: 'RSI Strategy' },
    { value: 'macd', label: 'MACD Strategy' },
  ];

  const timeframes = [
    { value: '1m', label: '1 Minute' },
    { value: '5m', label: '5 Minutes' },
    { value: '15m', label: '15 Minutes' },
    { value: '1h', label: '1 Hour' },
    { value: '4h', label: '4 Hours' },
    { value: '1d', label: '1 Day' },
  ];

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [backtestsData, pairsData] = await Promise.all([
        apiClient.getBacktests(),
        apiClient.getPairs(),
      ]);
      // Ensure backtests is always an array
      setBacktests(Array.isArray(backtestsData) ? backtestsData : []);
      setPairs(Array.isArray(pairsData) ? pairsData : []);
    } catch (error) {
      console.error('Failed to load backtests data:', error);
      // Ensure arrays are set to empty arrays on error
      setBacktests([]);
      setPairs([]);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const backtest = await apiClient.createBacktest(formData);
      setBacktests(prev => [backtest, ...prev]);
      setShowForm(false);
      setFormData({
        pair_id: '',
        strategy: 'smc',
        timeframe: '1h',
        start_date: '',
        end_date: '',
        initial_balance: 10000,
        risk_per_trade: 2,
        leverage: 1,
      });
    } catch (error) {
      console.error('Failed to create backtest:', error);
    }
  };

  const handleDelete = async (backtestId: string) => {
    try {
      await apiClient.deleteBacktest(backtestId);
      setBacktests(prev => prev.filter(b => b.id !== backtestId));
    } catch (error) {
      console.error('Failed to delete backtest:', error);
    }
  };

  const handleDeleteAll = async () => {
    if (window.confirm('Are you sure you want to delete all backtests?')) {
      try {
        await apiClient.deleteAllBacktests();
        setBacktests([]);
      } catch (error) {
        console.error('Failed to delete all backtests:', error);
      }
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  const formatDuration = (startDate: string, endDate?: string) => {
    const start = new Date(startDate);
    const end = endDate ? new Date(endDate) : new Date();
    const diff = end.getTime() - start.getTime();
    const days = Math.floor(diff / (1000 * 60 * 60 * 24));
    const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
    return `${days}d ${hours}h`;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Backtests</h1>
        <div className="flex items-center space-x-4">
          <button
            onClick={() => setShowForm(true)}
            className="btn-primary flex items-center"
          >
            <Play className="w-4 h-4 mr-2" />
            New Backtest
          </button>
          {backtests.length > 0 && (
            <button
              onClick={handleDeleteAll}
              className="btn-danger flex items-center"
            >
              <Trash2 className="w-4 h-4 mr-2" />
              Delete All
            </button>
          )}
        </div>
      </div>

      {/* Backtests Table */}
      <div className="card">
        <div className="p-6 border-b border-gray-200 dark:border-gray-700">
          <h2 className="text-lg font-semibold">Backtest Results</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50 dark:bg-gray-700">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  Pair
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  Strategy
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  Timeframe
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  Period
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  Return
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
              {backtests.map((backtest) => (
                <tr key={backtest.id}>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900 dark:text-white">
                    {backtest.config.pair_id}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-300">
                    {strategies.find(s => s.value === backtest.config.strategy)?.label || backtest.config.strategy}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-300">
                    {timeframes.find(t => t.value === backtest.config.timeframe)?.label || backtest.config.timeframe}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-300">
                    {formatDuration(backtest.config.start_date, backtest.config.end_date)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                      backtest.status === 'completed' 
                        ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                        : backtest.status === 'running'
                        ? 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200'
                        : 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
                    }`}>
                      {backtest.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-300">
                    {backtest.metrics ? (
                      <span className={backtest.metrics.total_return >= 0 ? 'text-green-600' : 'text-red-600'}>
                        {backtest.metrics.total_return >= 0 ? '+' : ''}{backtest.metrics.total_return.toFixed(2)}%
                      </span>
                    ) : (
                      '-'
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-300">
                    <div className="flex items-center space-x-2">
                      <button
                        onClick={() => setSelectedBacktest(backtest)}
                        className="text-primary-600 hover:text-primary-900 dark:hover:text-primary-400"
                        title="View Details"
                      >
                        <Eye className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => handleDelete(backtest.id)}
                        className="text-red-600 hover:text-red-900 dark:hover:text-red-400"
                        title="Delete"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {backtests.length === 0 && (
            <div className="text-center py-8 text-gray-500 dark:text-gray-400">
              No backtests found. Create your first backtest to get started.
            </div>
          )}
        </div>
      </div>

      {/* New Backtest Form Modal */}
      {showForm && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-full max-w-md shadow-lg rounded-md bg-white dark:bg-gray-800">
            <div className="mt-3">
              <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">New Backtest</h3>
              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Trading Pair
                  </label>
                  <select
                    value={formData.pair_id}
                    onChange={(e) => setFormData(prev => ({ ...prev, pair_id: e.target.value }))}
                    className="input-field"
                    required
                  >
                    <option value="">Select a pair</option>
                    {pairs.map((pair) => (
                      <option key={pair.id} value={pair.id}>
                        {pair.symbol}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Strategy
                  </label>
                  <select
                    value={formData.strategy}
                    onChange={(e) => setFormData(prev => ({ ...prev, strategy: e.target.value }))}
                    className="input-field"
                    required
                  >
                    {strategies.map((strategy) => (
                      <option key={strategy.value} value={strategy.value}>
                        {strategy.label}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Timeframe
                  </label>
                  <select
                    value={formData.timeframe}
                    onChange={(e) => setFormData(prev => ({ ...prev, timeframe: e.target.value }))}
                    className="input-field"
                    required
                  >
                    {timeframes.map((timeframe) => (
                      <option key={timeframe.value} value={timeframe.value}>
                        {timeframe.label}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Start Date
                    </label>
                    <input
                      type="date"
                      value={formData.start_date}
                      onChange={(e) => setFormData(prev => ({ ...prev, start_date: e.target.value }))}
                      className="input-field"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      End Date
                    </label>
                    <input
                      type="date"
                      value={formData.end_date}
                      onChange={(e) => setFormData(prev => ({ ...prev, end_date: e.target.value }))}
                      className="input-field"
                      required
                    />
                  </div>
                </div>

                <div className="grid grid-cols-3 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Initial Balance
                    </label>
                    <input
                      type="number"
                      value={formData.initial_balance}
                      onChange={(e) => setFormData(prev => ({ ...prev, initial_balance: parseFloat(e.target.value) }))}
                      className="input-field"
                      min="100"
                      step="100"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Risk per Trade (%)
                    </label>
                    <input
                      type="number"
                      value={formData.risk_per_trade}
                      onChange={(e) => setFormData(prev => ({ ...prev, risk_per_trade: parseFloat(e.target.value) }))}
                      className="input-field"
                      min="0.1"
                      max="10"
                      step="0.1"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Leverage
                    </label>
                    <input
                      type="number"
                      value={formData.leverage}
                      onChange={(e) => setFormData(prev => ({ ...prev, leverage: parseFloat(e.target.value) }))}
                      className="input-field"
                      min="1"
                      max="100"
                      step="1"
                      required
                    />
                  </div>
                </div>

                <div className="flex justify-end space-x-3 mt-6">
                  <button
                    type="button"
                    onClick={() => setShowForm(false)}
                    className="btn-secondary"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="btn-primary"
                  >
                    Start Backtest
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}

      {/* Backtest Details Modal */}
      {selectedBacktest && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-full max-w-2xl shadow-lg rounded-md bg-white dark:bg-gray-800">
            <div className="mt-3">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-medium text-gray-900 dark:text-white">Backtest Details</h3>
                <button
                  onClick={() => setSelectedBacktest(null)}
                  className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                >
                  <X className="w-6 h-6" />
                </button>
              </div>

              <div className="space-y-6">
                {/* Configuration */}
                <div>
                  <h4 className="text-md font-medium text-gray-900 dark:text-white mb-3">Configuration</h4>
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="text-gray-500 dark:text-gray-400">Pair:</span>
                      <span className="ml-2 font-medium">{selectedBacktest.config.pair_id}</span>
                    </div>
                    <div>
                      <span className="text-gray-500 dark:text-gray-400">Strategy:</span>
                      <span className="ml-2 font-medium">{selectedBacktest.config.strategy}</span>
                    </div>
                    <div>
                      <span className="text-gray-500 dark:text-gray-400">Timeframe:</span>
                      <span className="ml-2 font-medium">{selectedBacktest.config.timeframe}</span>
                    </div>
                    <div>
                      <span className="text-gray-500 dark:text-gray-400">Period:</span>
                      <span className="ml-2 font-medium">
                        {formatDuration(selectedBacktest.config.start_date, selectedBacktest.config.end_date)}
                      </span>
                    </div>
                    <div>
                      <span className="text-gray-500 dark:text-gray-400">Initial Balance:</span>
                      <span className="ml-2 font-medium">${selectedBacktest.config.initial_balance.toLocaleString()}</span>
                    </div>
                    <div>
                      <span className="text-gray-500 dark:text-gray-400">Risk per Trade:</span>
                      <span className="ml-2 font-medium">{selectedBacktest.config.risk_per_trade}%</span>
                    </div>
                  </div>
                </div>

                {/* Metrics */}
                {selectedBacktest.metrics && (
                  <div>
                    <h4 className="text-md font-medium text-gray-900 dark:text-white mb-3">Performance Metrics</h4>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                      <div className="text-center p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
                        <div className="text-2xl font-bold text-gray-900 dark:text-white">
                          {selectedBacktest.metrics.total_return >= 0 ? '+' : ''}{selectedBacktest.metrics.total_return.toFixed(2)}%
                        </div>
                        <div className="text-sm text-gray-500 dark:text-gray-400">Total Return</div>
                      </div>
                      <div className="text-center p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
                        <div className="text-2xl font-bold text-gray-900 dark:text-white">
                          {selectedBacktest.metrics.win_rate.toFixed(1)}%
                        </div>
                        <div className="text-sm text-gray-500 dark:text-gray-400">Win Rate</div>
                      </div>
                      <div className="text-center p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
                        <div className="text-2xl font-bold text-gray-900 dark:text-white">
                          {selectedBacktest.metrics.total_trades}
                        </div>
                        <div className="text-sm text-gray-500 dark:text-gray-400">Total Trades</div>
                      </div>
                      <div className="text-center p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
                        <div className="text-2xl font-bold text-gray-900 dark:text-white">
                          {selectedBacktest.metrics.max_drawdown.toFixed(2)}%
                        </div>
                        <div className="text-sm text-gray-500 dark:text-gray-400">Max Drawdown</div>
                      </div>
                    </div>
                  </div>
                )}

                {/* Error */}
                {selectedBacktest.error && (
                  <div className="p-4 bg-red-50 dark:bg-red-900/20 rounded-lg">
                    <div className="flex items-center">
                      <AlertTriangle className="w-5 h-5 text-red-600 mr-2" />
                      <span className="text-red-800 dark:text-red-200">{selectedBacktest.error}</span>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Backtests;
