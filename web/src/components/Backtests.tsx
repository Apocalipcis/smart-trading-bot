import React, { useState, useEffect } from 'react';
import { Play, Trash2, Eye, BarChart3, AlertTriangle, X, Plus, Minus, Download, RefreshCw } from 'lucide-react';
import { BacktestConfig, BacktestResult, TradingPair, TimeframeRole, StrategyMetadata, AvailableTimeframes } from '../types/api';
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

  const [strategies, setStrategies] = useState<StrategyMetadata[]>([]);
  const [availableTimeframes, setAvailableTimeframes] = useState<AvailableTimeframes | null>(null);
  const [selectedTimeframes, setSelectedTimeframes] = useState<string[]>([]);
  const [timeframeRoles, setTimeframeRoles] = useState<Record<string, TimeframeRole>>({});
  const [validationErrors, setValidationErrors] = useState<string[]>([]);
  const [validationWarnings, setValidationWarnings] = useState<string[]>([]);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [backtestsData, pairsData, strategiesData, timeframesData] = await Promise.all([
        apiClient.getBacktests(),
        apiClient.getPairs(),
        apiClient.getStrategies(),
        apiClient.getAvailableTimeframes(),
      ]);
      // Ensure backtests is always an array
      setBacktests(Array.isArray(backtestsData) ? backtestsData : []);
      setPairs(Array.isArray(pairsData) ? pairsData : []);
      setStrategies(Array.isArray(strategiesData) ? strategiesData : []);
      setAvailableTimeframes(timeframesData);
    } catch (error) {
      console.error('Failed to load backtests data:', error);
      // Ensure arrays are set to empty arrays on error
      setBacktests([]);
      setPairs([]);
      setStrategies([]);
      setAvailableTimeframes(null);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Validate form data
    if (selectedTimeframes.length === 0) {
      setValidationErrors(['Please select at least one timeframe']);
      return;
    }
    
    if (Object.keys(timeframeRoles).length !== selectedTimeframes.length) {
      setValidationErrors(['Please assign roles to all selected timeframes']);
      return;
    }
    
    // Update form data with selected timeframes and roles
    const updatedFormData = {
      ...formData,
      pairs: formData.pairs,
      timeframes: selectedTimeframes,
      tf_roles: timeframeRoles,
    };
    
    try {
      const backtest = await apiClient.createBacktest(updatedFormData);
      setBacktests(prev => [backtest, ...prev]);
      setShowForm(false);
      resetForm();
    } catch (error) {
      console.error('Failed to create backtest:', error);
    }
  };

  const resetForm = () => {
    setFormData({
      pairs: [],
      strategy: 'smc',
      timeframes: [],
      tf_roles: {},
      start_date: '',
      end_date: '',
      initial_balance: 10000,
      risk_per_trade: 2,
      leverage: 1,
    });
    setSelectedTimeframes([]);
    setTimeframeRoles({});
    setValidationErrors([]);
    setValidationWarnings([]);
  };

  const handleTimeframeChange = (timeframes: string[]) => {
    setSelectedTimeframes(timeframes);
    
    // Remove roles for removed timeframes
    const newRoles = { ...timeframeRoles };
    Object.keys(newRoles).forEach(tf => {
      if (!timeframes.includes(tf)) {
        delete newRoles[tf];
      }
    });
    setTimeframeRoles(newRoles);
    
    // Clear validation errors
    setValidationErrors([]);
    setValidationWarnings([]);
  };

  const handleRoleChange = (timeframe: string, role: TimeframeRole) => {
    setTimeframeRoles(prev => ({
      ...prev,
      [timeframe]: role
    }));
    
    // Clear validation errors
    setValidationErrors([]);
    setValidationWarnings([]);
  };

  const removeTimeframe = (timeframe: string) => {
    setSelectedTimeframes(prev => prev.filter(tf => tf !== timeframe));
    setTimeframeRoles(prev => {
      const newRoles = { ...prev };
      delete newRoles[timeframe];
      return newRoles;
    });
  };

  const validateConfiguration = async () => {
    if (selectedTimeframes.length === 0) return;
    
    try {
      const validation = await apiClient.validateTimeframeRoles(selectedTimeframes, timeframeRoles);
      
      if (validation.success) {
        setValidationErrors([]);
        setValidationWarnings(validation.data?.warnings || []);
      } else {
        setValidationErrors(validation.data?.errors || []);
        setValidationWarnings(validation.data?.warnings || []);
      }
    } catch (error) {
      console.error('Validation failed:', error);
    }
  };

  useEffect(() => {
    if (selectedTimeframes.length > 0 && Object.keys(timeframeRoles).length === selectedTimeframes.length) {
      validateConfiguration();
    }
  }, [selectedTimeframes, timeframeRoles]);

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
                    {backtest.config.pairs?.join(', ') || backtest.config.pair_id || 'N/A'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-300">
                    {strategies.find(s => s.name.toLowerCase() === backtest.config.strategy)?.name || backtest.config.strategy}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-300">
                    {backtest.config.timeframes?.join(', ') || backtest.config.timeframe || 'N/A'}
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
          <div className="relative top-20 mx-auto p-5 border w-full max-w-2xl shadow-lg rounded-md bg-white dark:bg-gray-800">
            <div className="mt-3">
              <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">New Backtest</h3>
              <form onSubmit={handleSubmit} className="space-y-4">
                {/* Trading Pair - Multi-select */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Trading Pairs
                  </label>
                  <select
                    multiple
                    value={formData.pairs}
                    onChange={(e) => {
                      const selectedOptions = Array.from(e.target.selectedOptions, option => option.value);
                      setFormData(prev => ({ ...prev, pairs: selectedOptions }));
                    }}
                    className="input-field min-h-[80px]"
                    required
                  >
                    {pairs.map((pair) => (
                      <option key={pair.id} value={pair.symbol}>
                        {pair.symbol}
                      </option>
                    ))}
                  </select>
                  <p className="text-xs text-gray-500 mt-1">Hold Ctrl/Cmd to select multiple pairs</p>
                </div>

                {/* Strategy */}
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
                    <option value="">Select a strategy</option>
                    {strategies.map((strategy) => (
                      <option key={strategy.name.toLowerCase()} value={strategy.name.toLowerCase()}>
                        {strategy.name} - {strategy.description}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Timeframes & Roles */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Available Timeframes
                  </label>
                  <select
                    multiple
                    value={selectedTimeframes}
                    onChange={(e) => {
                      const selectedOptions = Array.from(e.target.selectedOptions, option => option.value);
                      handleTimeframeChange(selectedOptions);
                    }}
                    className="input-field min-h-[80px]"
                    required
                  >
                    {availableTimeframes?.timeframes.map((tf) => (
                      <option key={tf} value={tf}>
                        {tf}
                      </option>
                    )) || []}
                  </select>
                  <p className="text-xs text-gray-500 mt-1">Hold Ctrl/Cmd to select multiple timeframes</p>
                </div>

                {/* Selected Timeframes with Role Assignment */}
                {selectedTimeframes.length > 0 && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      Timeframe Role Assignment
                    </label>
                    <div className="space-y-2">
                      {selectedTimeframes.map((timeframe) => (
                        <div key={timeframe} className="flex items-center space-x-3 p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
                          <span className="text-sm font-medium text-gray-700 dark:text-gray-300 min-w-[40px]">
                            {timeframe}
                          </span>
                          <span className="text-sm text-gray-500 dark:text-gray-400">Role:</span>
                          <select
                            value={timeframeRoles[timeframe] || 'LTF'}
                            onChange={(e) => handleRoleChange(timeframe, e.target.value as TimeframeRole)}
                            className="input-field text-sm py-1 px-2 min-w-[80px]"
                          >
                            <option value="LTF">LTF</option>
                            <option value="HTF">HTF</option>
                          </select>
                          <button
                            type="button"
                            onClick={() => removeTimeframe(timeframe)}
                            className="text-red-500 hover:text-red-700 dark:text-red-400 dark:hover:text-red-300"
                          >
                            <Minus className="w-4 h-4" />
                          </button>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Validation Messages */}
                {validationErrors.length > 0 && (
                  <div className="p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
                    <div className="text-sm text-red-800 dark:text-red-200">
                      {validationErrors.map((error, index) => (
                        <div key={index} className="flex items-center">
                          <AlertTriangle className="w-4 h-4 mr-2 flex-shrink-0" />
                          {error}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {validationWarnings.length > 0 && (
                  <div className="p-3 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg">
                    <div className="text-sm text-yellow-800 dark:text-yellow-200">
                      {validationWarnings.map((warning, index) => (
                        <div key={index} className="flex items-center">
                          <AlertTriangle className="w-4 h-4 mr-2 flex-shrink-0" />
                          {warning}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

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

                {/* Actions */}
                <div className="flex justify-end space-x-3 mt-6">
                  <button
                    type="button"
                    onClick={() => {
                      setShowForm(false);
                      resetForm();
                    }}
                    className="btn-secondary"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="btn-primary"
                    disabled={validationErrors.length > 0}
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
                      <span className="text-gray-500 dark:text-gray-400">Pairs:</span>
                      <span className="ml-2 font-medium">{selectedBacktest.config.pairs?.join(', ') || selectedBacktest.config.pair_id || 'N/A'}</span>
                    </div>
                    <div>
                      <span className="text-gray-500 dark:text-gray-400">Strategy:</span>
                      <span className="ml-2 font-medium">{selectedBacktest.config.strategy}</span>
                    </div>
                    <div>
                      <span className="text-gray-500 dark:text-gray-400">Timeframes:</span>
                      <span className="ml-2 font-medium">{selectedBacktest.config.timeframes?.join(', ') || selectedBacktest.config.timeframe || 'N/A'}</span>
                    </div>
                    {selectedBacktest.config.tf_roles && Object.keys(selectedBacktest.config.tf_roles).length > 0 && (
                      <div>
                        <span className="text-gray-500 dark:text-gray-400">Roles:</span>
                        <span className="ml-2 font-medium">
                          {Object.entries(selectedBacktest.config.tf_roles).map(([tf, role]) => `${tf}:${role}`).join(', ')}
                        </span>
                      </div>
                    )}
                    <div>
                      <span className="text-gray-500 dark:text-gray-400">Period:</span>
                      <span className="ml-2 font-medium">
                        {formatDuration(selectedBacktest.config.start_date, selectedBacktest.config.end_date)}
                      </span>
                    </div>
                    <div>
                      <span className="text-gray-500 dark:text-gray-400">Initial Balance:</span>
                      <span className="ml-2 font-medium">${(selectedBacktest.config.initial_balance || selectedBacktest.config.initial_capital || 0).toLocaleString()}</span>
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
