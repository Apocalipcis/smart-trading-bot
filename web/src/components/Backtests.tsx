import React, { useState, useEffect } from 'react';
import { Play, Trash2, Eye, BarChart3, AlertTriangle, X, Plus, Minus, Download, RefreshCw, Calendar } from 'lucide-react';
import { BacktestConfig, BacktestResult, TradingPair, TimeframeRole, StrategyMetadata, AvailableTimeframes, SMCConfiguration } from '../types/api';
import apiClient from '../services/api';
import SMCConfigurationComponent from './SMCConfiguration';

const Backtests: React.FC = () => {
  const [backtests, setBacktests] = useState<BacktestResult[]>([]);
  const [pairs, setPairs] = useState<TradingPair[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [selectedBacktest, setSelectedBacktest] = useState<BacktestResult | null>(null);
  const [formData, setFormData] = useState<BacktestConfig>({
    pairs: [],
    strategy: 'SMC',
    timeframes: [],
    tf_roles: {},
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

  const [smcConfiguration, setSmcConfiguration] = useState<SMCConfiguration | undefined>(undefined);
  const [showSMCConfig, setShowSMCConfig] = useState(false);
  const [smcValidationErrors, setSmcValidationErrors] = useState<string[]>([]);
  const [smcValidationWarnings, setSmcValidationWarnings] = useState<string[]>([]);

  // Helper functions to safely extract backtest data
  const getBacktestPairs = (backtest: BacktestResult): string => {
    // Try new structure first, then legacy structure
    const pairs = backtest.pairs || backtest.config?.pairs || backtest.config?.pair_id;
    if (Array.isArray(pairs)) {
      return pairs.join(', ');
    }
    return pairs || 'N/A';
  };

  const getBacktestStrategy = (backtest: BacktestResult): string => {
    // Try new structure first, then legacy structure
    return backtest.strategy || backtest.config?.strategy || 'N/A';
  };

  const getBacktestTimeframes = (backtest: BacktestResult): string => {
    // Try new structure first, then legacy structure
    const timeframes = backtest.timeframes || backtest.config?.timeframes || backtest.config?.timeframe;
    if (Array.isArray(timeframes)) {
      return timeframes.join(', ');
    }
    return timeframes || 'N/A';
  };

  const getBacktestStartDate = (backtest: BacktestResult): string => {
    return backtest.start_date || backtest.config?.start_date || '';
  };

  const getBacktestEndDate = (backtest: BacktestResult): string => {
    return backtest.end_date || backtest.config?.end_date || '';
  };

  const getBacktestStatus = (backtest: BacktestResult): string => {
    return backtest.status || 'completed';
  };

  const getBacktestMetrics = (backtest: BacktestResult) => {
    // Try new structure first, then legacy structure
    return backtest.metrics || {
      total_return: backtest.total_return || 0,
      win_rate: backtest.win_rate || 0,
      total_trades: backtest.total_trades || 0,
      profitable_trades: backtest.profitable_trades || 0,
      max_drawdown: backtest.max_drawdown || 0,
      sharpe_ratio: backtest.sharpe_ratio || 0
    };
  };

  // Quick date selection utility functions
  const getDateDaysAgo = (days: number): string => {
    const date = new Date();
    date.setDate(date.getDate() - days);
    return date.toISOString().split('T')[0];
  };

  const getTodayDate = (): string => {
    return new Date().toISOString().split('T')[0];
  };

  const handleQuickDateSelect = (days: number) => {
    const startDate = getDateDaysAgo(days);
    const endDate = getTodayDate();
    setFormData(prev => ({
      ...prev,
      start_date: startDate,
      end_date: endDate
    }));
  };

  const handleTodaySelect = () => {
    const today = getTodayDate();
    setFormData(prev => ({
      ...prev,
      start_date: today,
      end_date: today
    }));
  };

  const handleResetDates = () => {
    setFormData(prev => ({
      ...prev,
      start_date: '',
      end_date: ''
    }));
  };

  const getSelectedPeriodText = (): string => {
    if (formData.start_date && formData.end_date) {
      const start = new Date(formData.start_date);
      const end = new Date(formData.end_date);
      const diffTime = Math.abs(end.getTime() - start.getTime());
      const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
      return `${diffDays} day${diffDays > 1 ? 's' : ''} period`;
    }
    return '';
  };

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

  const resetForm = () => {
    setFormData({
      pairs: [],
      strategy: 'SMC',
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
    setSmcConfiguration(undefined);
    setSmcValidationErrors([]);
    setSmcValidationWarnings([]);
  };

  // SMC Configuration handlers
  const handleSMCConfigurationChange = (config: SMCConfiguration) => {
    setSmcConfiguration(config);
    // Update form data with SMC configuration
    setFormData(prev => ({
      ...prev,
      smc_configuration: config
    }));
  };

  const handleSMCValidationChange = (isValid: boolean, errors: string[], warnings: string[]) => {
    setSmcValidationErrors(errors);
    setSmcValidationWarnings(warnings);
  };

  const toggleSMCConfiguration = () => {
    setShowSMCConfig(!showSMCConfig);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Validate form data
    if (selectedTimeframes.length === 0) {
      setValidationErrors(['Please select at least one timeframe']);
      return;
    }
    
    // Check if all selected timeframes have roles assigned
    const missingRoles = selectedTimeframes.filter(tf => !timeframeRoles[tf]);
    if (missingRoles.length > 0) {
      setValidationErrors([`Please assign roles to the following timeframes: ${missingRoles.join(', ')}`]);
      return;
    }
    
    // Validate SMC configuration if SMC strategy is selected
    if (formData.strategy === 'SMC' && smcConfiguration) {
      if (smcValidationErrors.length > 0) {
        setValidationErrors([...validationErrors, ...smcValidationErrors]);
        return;
      }
    }
    
    // Update form data with selected timeframes and roles
    const updatedFormData = {
      ...formData,
      pairs: formData.pairs,
      timeframes: selectedTimeframes,
      tf_roles: timeframeRoles,
      smc_configuration: smcConfiguration, // Include SMC configuration
      // Ensure dates are in ISO format
      start_date: formData.start_date ? new Date(formData.start_date).toISOString() : '',
      end_date: formData.end_date ? new Date(formData.end_date).toISOString() : '',
      // Remove any undefined or null values
    };
    
    // Ensure we have all required fields for new format
    if (!updatedFormData.pairs || updatedFormData.pairs.length === 0) {
      setValidationErrors(['Please select at least one trading pair']);
      return;
    }
    
    if (!updatedFormData.timeframes || updatedFormData.timeframes.length === 0) {
      setValidationErrors(['Please select at least one timeframe']);
      return;
    }
    
    if (!updatedFormData.tf_roles || Object.keys(updatedFormData.tf_roles).length === 0) {
      setValidationErrors(['Please assign roles to all selected timeframes']);
      return;
    }
    
    // Clean up the data - remove undefined/null values
    Object.keys(updatedFormData).forEach(key => {
      if ((updatedFormData as any)[key] === undefined || (updatedFormData as any)[key] === null) {
        delete (updatedFormData as any)[key];
      }
    });
    
    try {
      console.log('Creating backtest with data:', JSON.stringify(updatedFormData, null, 2));
      const backtest = await apiClient.createBacktest(updatedFormData);
      setBacktests(prev => [backtest, ...prev]);
      setShowForm(false);
      resetForm();
    } catch (error: any) {
      console.error('Failed to create backtest:', error);
      console.error('Error response:', error.response?.data);
      console.error('Error status:', error.response?.status);
      
      if (error.response?.data?.detail) {
        // Handle both string and object detail responses
        const detail = error.response.data.detail;
        console.error('Error detail:', detail);
        if (typeof detail === 'string') {
          setValidationErrors([detail]);
        } else if (detail && typeof detail === 'object') {
          // Handle structured error response
          const errors = detail.errors || detail.message || [];
          const errorMessages = Array.isArray(errors) ? errors : [String(errors)];
          setValidationErrors(errorMessages);
        } else {
          setValidationErrors(['Failed to create backtest. Please check your configuration.']);
        }
      } else if (error.message) {
        setValidationErrors([error.message]);
      } else {
        setValidationErrors(['Failed to create backtest. Please check your configuration.']);
      }
    }
  };

  const handleTimeframeChange = (timeframes: string[]) => {
    setSelectedTimeframes(timeframes);
    
    // Update roles: remove roles for removed timeframes and add default roles for new timeframes
    const newRoles = { ...timeframeRoles };
    
    // Remove roles for timeframes that are no longer selected
    Object.keys(newRoles).forEach(tf => {
      if (!timeframes.includes(tf)) {
        delete newRoles[tf];
      }
    });
    
    // Add default role (LTF) for newly selected timeframes that don't have roles
    timeframes.forEach(tf => {
      if (!newRoles[tf]) {
        newRoles[tf] = 'LTF';
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
    
    // Check for missing roles first
    const missingRoles = selectedTimeframes.filter(tf => !timeframeRoles[tf]);
    if (missingRoles.length > 0) {
      setValidationErrors([`Please assign roles to the following timeframes: ${missingRoles.join(', ')}`]);
      return;
    }
    
    try {
      const validation = await apiClient.validateTimeframeRoles(selectedTimeframes, timeframeRoles);
      
      if (validation.success) {
        setValidationErrors([]);
        setValidationWarnings(validation.data?.warnings || []);
      } else {
        const errors = validation.data?.errors || [];
        const warnings = validation.data?.warnings || [];
        setValidationErrors(Array.isArray(errors) ? errors : [String(errors)]);
        setValidationWarnings(Array.isArray(warnings) ? warnings : [String(warnings)]);
      }
    } catch (error: any) {
      console.error('Validation failed:', error);
      if (error.response?.status === 404) {
        // Validation endpoint not found, skip validation
        console.warn('Validation endpoint not available, skipping validation');
        setValidationErrors([]);
        setValidationWarnings([]);
      } else {
        setValidationErrors(['Validation failed. Please check your configuration.']);
      }
    }
  };

  useEffect(() => {
    if (selectedTimeframes.length > 0 && selectedTimeframes.every(tf => timeframeRoles[tf])) {
      validateConfiguration();
    } else if (selectedTimeframes.length > 0) {
      // Show real-time validation for missing roles
      const missingRoles = selectedTimeframes.filter(tf => !timeframeRoles[tf]);
      if (missingRoles.length > 0) {
        setValidationErrors([`Please assign roles to the following timeframes: ${missingRoles.join(', ')}`]);
      } else {
        setValidationErrors([]);
      }
    } else {
      setValidationErrors([]);
      setValidationWarnings([]);
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
    if (!startDate) return 'N/A';
    try {
      const start = new Date(startDate);
      const end = endDate ? new Date(endDate) : new Date();
      const diff = end.getTime() - start.getTime();
      const days = Math.floor(diff / (1000 * 60 * 60 * 24));
      const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
      return `${days}d ${hours}h`;
    } catch (error) {
      return 'N/A';
    }
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
                    {getBacktestPairs(backtest)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-300">
                    {strategies.find(s => s.name === getBacktestStrategy(backtest))?.name || getBacktestStrategy(backtest)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-300">
                    {getBacktestTimeframes(backtest)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-300">
                    {formatDuration(getBacktestStartDate(backtest), getBacktestEndDate(backtest))}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                      getBacktestStatus(backtest) === 'completed' 
                        ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                        : getBacktestStatus(backtest) === 'running'
                        ? 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200'
                        : 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
                    }`}>
                      {getBacktestStatus(backtest)}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-300">
                    {getBacktestMetrics(backtest).total_return >= 0 ? (
                      <span className="text-green-600">
                        {getBacktestMetrics(backtest).total_return >= 0 ? '+' : ''}{getBacktestMetrics(backtest).total_return.toFixed(2)}%
                      </span>
                    ) : (
                      <span className="text-red-600">
                        {getBacktestMetrics(backtest).total_return.toFixed(2)}%
                      </span>
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
                      <option key={strategy.name} value={strategy.name}>
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
                    {loading ? (
                      <option disabled>Loading timeframes...</option>
                    ) : availableTimeframes?.timeframes && availableTimeframes.timeframes.length > 0 ? (
                      availableTimeframes.timeframes.map((tf) => (
                        <option key={tf.timeframe} value={tf.timeframe}>
                          {tf.timeframe} - {tf.description}
                        </option>
                      ))
                    ) : (
                      <option disabled>No timeframes available</option>
                    )}
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
                        <div key={timeframe} className={`flex items-center space-x-3 p-3 rounded-lg ${
                          !timeframeRoles[timeframe] 
                            ? 'bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800' 
                            : 'bg-gray-50 dark:bg-gray-700'
                        }`}>
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
                          {!timeframeRoles[timeframe] && (
                            <span className="text-xs text-red-600 dark:text-red-400 flex items-center">
                              <AlertTriangle className="w-3 h-3 mr-1" />
                              Role required
                            </span>
                          )}
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

                {/* SMC Configuration */}
                {formData.strategy === 'SMC' && (
                  <div className="mt-4 p-4 border border-gray-200 dark:border-gray-700 rounded-lg">
                    <div className="flex items-center justify-between mb-3">
                      <h4 className="text-md font-medium text-gray-900 dark:text-white">SMC Strategy Configuration</h4>
                      <button
                        type="button"
                        onClick={toggleSMCConfiguration}
                        className="px-3 py-1 text-sm font-medium rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-600 transition-colors"
                      >
                        {showSMCConfig ? 'Hide Advanced Config' : 'Show Advanced Config'}
                      </button>
                    </div>
                    
                                         {showSMCConfig && (
                       <SMCConfigurationComponent
                         value={smcConfiguration}
                         onChange={handleSMCConfigurationChange}
                         onValidationChange={handleSMCValidationChange}
                       />
                     )}
                    
                    {!showSMCConfig && (
                      <div className="text-sm text-gray-600 dark:text-gray-400">
                        Click "Show Advanced Config" to configure SMC strategy parameters, indicators, filters, and risk management settings.
                      </div>
                    )}
                  </div>
                )}

                {/* Validation Messages */}
                {validationErrors.length > 0 && (
                  <div className="p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
                    <div className="text-sm text-red-800 dark:text-red-200">
                      {validationErrors.map((error, index) => (
                        <div key={index} className="flex items-start">
                          <AlertTriangle className="w-4 h-4 mr-2 flex-shrink-0 mt-0.5" />
                          <span>{error}</span>
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

                {/* Quick Date Selection */}
                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Quick Date Selection
                  </label>
                  <div className="grid grid-cols-3 sm:grid-cols-6 gap-2">
                    <button
                      type="button"
                      onClick={handleTodaySelect}
                      className="px-3 py-2 text-sm font-medium rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-green-50 hover:border-green-300 hover:text-green-700 dark:hover:bg-green-900/20 dark:hover:border-green-600 dark:hover:text-green-400 transition-all duration-200"
                      title="Today only"
                    >
                      Today
                    </button>
                    {[7, 14, 21, 30].map((days) => (
                      <button
                        key={days}
                        type="button"
                        onClick={() => handleQuickDateSelect(days)}
                        className="px-3 py-2 text-sm font-medium rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-blue-50 hover:border-blue-300 hover:text-blue-700 dark:hover:bg-blue-900/20 dark:hover:border-blue-600 dark:hover:text-blue-400 transition-all duration-200"
                        title={`Last ${days} day${days > 1 ? 's' : ''}`}
                      >
                        {days} Day{days > 1 ? 's' : ''}
                      </button>
                    ))}
                  </div>
                  {formData.start_date && formData.end_date && (
                    <div className="mt-3 p-3 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center text-sm text-blue-700 dark:text-blue-300">
                          <Calendar className="w-4 h-4 mr-2" />
                          <span className="font-medium">{getSelectedPeriodText()}</span>
                          <span className="mx-2">•</span>
                          <span>{formData.start_date} to {formData.end_date}</span>
                        </div>
                        <button
                          type="button"
                          onClick={handleResetDates}
                          className="px-3 py-1 text-sm font-medium rounded-md border border-blue-300 dark:border-blue-600 bg-white dark:bg-gray-700 text-blue-600 dark:text-blue-400 hover:bg-red-50 hover:border-red-300 hover:text-red-600 dark:hover:bg-red-900/20 dark:hover:border-red-600 dark:hover:text-red-400 transition-all duration-200"
                          title="Clear dates"
                        >
                          Reset
                        </button>
                      </div>
                    </div>
                  )}
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
                      <span className="ml-2 font-medium">{getBacktestPairs(selectedBacktest)}</span>
                    </div>
                    <div>
                      <span className="text-gray-500 dark:text-gray-400">Strategy:</span>
                      <span className="ml-2 font-medium">{getBacktestStrategy(selectedBacktest)}</span>
                    </div>
                    <div>
                      <span className="text-gray-500 dark:text-gray-400">Timeframes:</span>
                      <span className="ml-2 font-medium">{getBacktestTimeframes(selectedBacktest)}</span>
                    </div>
                    {(selectedBacktest.config?.tf_roles || selectedBacktest.tf_roles) && Object.keys(selectedBacktest.config?.tf_roles || selectedBacktest.tf_roles || {}).length > 0 && (
                      <div>
                        <span className="text-gray-500 dark:text-gray-400">Roles:</span>
                        <span className="ml-2 font-medium">
                          {Object.entries(selectedBacktest.config?.tf_roles || selectedBacktest.tf_roles || {}).map(([tf, role]) => `${tf}: ${role}`).join(', ')}
                        </span>
                      </div>
                    )}
                    <div>
                      <span className="text-gray-500 dark:text-gray-400">Period:</span>
                      <span className="ml-2 font-medium">
                        {formatDuration(getBacktestStartDate(selectedBacktest), getBacktestEndDate(selectedBacktest))}
                      </span>
                    </div>
                                          <div>
                        <span className="text-gray-500 dark:text-gray-400">Initial Balance:</span>
                        <span className="ml-2 font-medium">${(selectedBacktest.config?.initial_balance || selectedBacktest.initial_balance || 0).toLocaleString()}</span>
                      </div>
                      <div>
                        <span className="text-gray-500 dark:text-gray-400">Risk per Trade:</span>
                        <span className="ml-2 font-medium">{selectedBacktest.config?.risk_per_trade || 2}%</span>
                      </div>
                  </div>
                </div>

                {/* Performance Metrics */}
                <div className="mb-6">
                  <h3 className="text-lg font-semibold mb-3">Performance Metrics</h3>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="bg-gray-50 p-3 rounded">
                      <div className="text-sm text-gray-600">Total Return</div>
                      <div className={`text-lg font-semibold ${selectedBacktest.total_return >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                        {selectedBacktest.total_return >= 0 ? '+' : ''}{selectedBacktest.total_return.toFixed(2)}%
                      </div>
                    </div>
                    <div className="bg-gray-50 p-3 rounded">
                      <div className="text-sm text-gray-600">Win Rate</div>
                      <div className="text-lg font-semibold">{selectedBacktest.win_rate.toFixed(1)}%</div>
                    </div>
                    <div className="bg-gray-50 p-3 rounded">
                      <div className="text-sm text-gray-600">Total Trades</div>
                      <div className="text-lg font-semibold">{selectedBacktest.total_trades}</div>
                    </div>
                    <div className="bg-gray-50 p-3 rounded">
                      <div className="text-sm text-gray-600">Max Drawdown</div>
                      <div className="text-lg font-semibold text-red-600">{selectedBacktest.max_drawdown.toFixed(2)}%</div>
                    </div>
                  </div>
                </div>

                {/* Trade History */}
                {selectedBacktest.trades && selectedBacktest.trades.length > 0 && (
                  <div className="mb-6">
                    <h3 className="text-lg font-semibold mb-3">Trade History</h3>
                    <div className="space-y-3 max-h-96 overflow-y-auto">
                      {selectedBacktest.trades.map((trade, index) => (
                        <div key={index} className="border rounded-lg p-4 bg-gray-50">
                          <div className="flex justify-between items-start mb-2">
                            <div className="flex items-center space-x-2">
                              <span className={`px-2 py-1 rounded text-xs font-medium ${
                                trade.side === 'long' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                              }`}>
                                {trade.side.toUpperCase()}
                              </span>
                              <span className={`px-2 py-1 rounded text-xs font-medium ${
                                trade.exit_reason === 'Take Profit' ? 'bg-blue-100 text-blue-800' :
                                trade.exit_reason === 'Stop Loss' ? 'bg-red-100 text-red-800' :
                                'bg-gray-100 text-gray-800'
                              }`}>
                                {trade.exit_reason}
                              </span>
                            </div>
                            <span className={`text-sm font-medium ${
                              trade.pnl >= 0 ? 'text-green-600' : 'text-red-600'
                            }`}>
                              {trade.pnl >= 0 ? '+' : ''}${trade.pnl.toFixed(2)} ({trade.return_pct >= 0 ? '+' : ''}{trade.return_pct.toFixed(2)}%)
                            </span>
                          </div>
                          
                          <div className="grid grid-cols-2 gap-4 text-sm">
                            <div>
                              <span className="text-gray-600">Entry:</span> ${trade.entry_price.toFixed(2)}
                            </div>
                            <div>
                              <span className="text-gray-600">Exit:</span> ${trade.exit_price.toFixed(2)}
                            </div>
                            <div>
                              <span className="text-gray-600">Stop Loss:</span> ${trade.stop_loss?.toFixed(2) || 'N/A'}
                            </div>
                            <div>
                              <span className="text-gray-600">Take Profit:</span> ${trade.take_profit?.toFixed(2) || 'N/A'}
                            </div>
                            <div>
                              <span className="text-gray-600">Size:</span> {Math.abs(trade.size).toFixed(4)}
                            </div>
                            <div>
                              <span className="text-gray-600">Duration:</span> {trade.duration_hours.toFixed(1)}h
                            </div>
                          </div>
                          
                          {trade.metadata && Object.keys(trade.metadata).length > 0 && (
                            <div className="mt-2 pt-2 border-t">
                              <div className="text-xs text-gray-600 mb-1">Signal Details:</div>
                              <div className="text-xs space-x-2">
                                {Object.entries(trade.metadata).map(([key, value]) => (
                                  <span key={key} className="inline-block bg-gray-200 px-2 py-1 rounded">
                                    {key}: {typeof value === 'number' ? value.toFixed(2) : value}
                                  </span>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* No Trades Message */}
                {(!selectedBacktest.trades || selectedBacktest.trades.length === 0) && (
                  <div className="mb-6">
                    <h3 className="text-lg font-semibold mb-3">Trade History</h3>
                    <div className="text-gray-500 text-center py-4">
                      No trades were executed during this backtest period.
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
