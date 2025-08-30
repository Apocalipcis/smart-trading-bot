import React, { useState, useEffect } from 'react';
import { Plus, Trash2, Play, Pause, CheckCircle, XCircle, AlertTriangle } from 'lucide-react';
import { TradingPair, Signal, Settings, PendingConfirmation } from '../types/api';
import apiClient from '../services/api';
import ApiTest from './ApiTest';

const Dashboard: React.FC = () => {
  const [pairs, setPairs] = useState<TradingPair[]>([]);
  const [signals, setSignals] = useState<Signal[]>([]);
  const [settings, setSettings] = useState<Settings | null>(null);
  const [pendingConfirmations, setPendingConfirmations] = useState<PendingConfirmation[] | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [newPair, setNewPair] = useState({ symbol: '', strategy: '' });
  const [availableStrategies, setAvailableStrategies] = useState<string[]>([]);
  const [showAddPair, setShowAddPair] = useState(false);
  const [retryCount, setRetryCount] = useState(0);
  const [connectionStatus, setConnectionStatus] = useState<'connected' | 'connecting' | 'disconnected'>('connecting');

  useEffect(() => {
    loadData();
    setupSignalStream();
    loadStrategies();
  }, []);

  const loadData = async () => {
    try {
      setError(null);
      const [pairsData, signalsData, settingsData] = await Promise.all([
        apiClient.getPairs(),
        apiClient.getSignals(10),
        apiClient.getSettings(),
      ]);
      
      setPairs(pairsData || []);
      setSignals(signalsData || []);
      setSettings(settingsData);
      
      // Try to load pending confirmations separately to handle potential 403 errors
      try {
        const pendingData = await apiClient.getPendingConfirmations();
        setPendingConfirmations(pendingData || []);
      } catch (pendingError) {
        console.warn('Could not load pending confirmations (trading may be disabled):', pendingError);
        setPendingConfirmations([]);
      }
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
      setError('Failed to load dashboard data. Please check your connection and try again.');
      // Set default empty arrays to prevent undefined errors
      setPairs([]);
      setSignals([]);
      setPendingConfirmations([]);
    } finally {
      setLoading(false);
    }
  };

  const loadStrategies = async () => {
    try {
      const strategies = await apiClient.getStrategies();
      setAvailableStrategies(strategies.map(s => s.name));
    } catch (error) {
      console.error('Failed to load strategies:', error);
      // Set default strategies if API fails
      setAvailableStrategies(['SMC']);
    }
  };

  const setupSignalStream = () => {
    const eventSource = apiClient.getSignalsStream();
    
    eventSource.onmessage = (event) => {
      try {
        const signal: Signal = JSON.parse(event.data);
        setSignals(prev => [signal, ...(prev || []).slice(0, 9)]);
      } catch (error) {
        console.error('Failed to parse signal data:', error);
      }
    };

    eventSource.onerror = (error) => {
      console.error('Signal stream error:', error);
      eventSource.close();
      // Reconnect after 5 seconds
      setTimeout(setupSignalStream, 5000);
    };

    return () => eventSource.close();
  };

  const handleAddPair = async () => {
    try {
      const pair = await apiClient.createPair(newPair);
      setPairs(prev => [...prev, pair]);
      setNewPair({ symbol: '', strategy: '' });
      setShowAddPair(false);
    } catch (error) {
      console.error('Failed to add pair:', error);
    }
  };

  const handleDeletePair = async (pairId: string) => {
    try {
      await apiClient.deletePair(pairId);
      setPairs(prev => prev.filter(p => p.id !== pairId));
    } catch (error) {
      console.error('Failed to delete pair:', error);
    }
  };

  const handleConfirmOrder = async (confirmationId: string) => {
    try {
      await apiClient.confirmOrder(confirmationId);
      setPendingConfirmations(prev => {
        if (!prev) return [];
        return prev.filter(p => p.id !== confirmationId);
      });
    } catch (error) {
      console.error('Failed to confirm order:', error);
    }
  };

  const handleRejectOrder = async (confirmationId: string) => {
    try {
      await apiClient.rejectOrder(confirmationId);
      setPendingConfirmations(prev => {
        if (!prev) return [];
        return prev.filter(p => p.id !== confirmationId);
      });
    } catch (error) {
      console.error('Failed to reject order:', error);
    }
  };

  const toggleTrading = async () => {
    if (!settings) return;
    
    try {
      const updatedSettings = await apiClient.updateSettings({
        trading_enabled: !settings.trading_enabled
      });
      setSettings(updatedSettings);
    } catch (error) {
      console.error('Failed to toggle trading:', error);
    }
  };

  const toggleOrderConfirmation = async () => {
    if (!settings) return;
    
    try {
      const updatedSettings = await apiClient.updateSettings({
        order_confirmation_required: !settings.order_confirmation_required
      });
      setSettings(updatedSettings);
    } catch (error) {
      console.error('Failed to toggle order confirmation:', error);
    }
  };

  const handleRetry = () => {
    setRetryCount(prev => prev + 1);
    if (retryCount < 3) {
      loadData();
    } else {
      setConnectionStatus('disconnected');
    }
  };

  const refreshSettings = async () => {
    try {
      console.log('🔄 Refreshing settings...');
      const updatedSettings = await apiClient.getSettings();
      console.log('✅ Settings refreshed:', updatedSettings);
      setSettings(updatedSettings);
    } catch (error) {
      console.error('❌ Failed to refresh settings:', error);
    }
  };

  // Refresh settings when component mounts and periodically
  useEffect(() => {
    console.log('🚀 Dashboard mounted, refreshing settings...');
    refreshSettings();
    const interval = setInterval(() => {
      console.log('⏰ Periodic settings refresh...');
      refreshSettings();
    }, 5000); // Refresh every 5 seconds
    return () => clearInterval(interval);
  }, []);

  // Track settings state changes
  useEffect(() => {
    console.log('📊 Dashboard settings state changed:', settings);
  }, [settings]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600 dark:text-gray-400">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center max-w-md">
          <div className="text-red-500 mb-4">
            <svg className="w-16 h-16 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
          </div>
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">Connection Error</h2>
          <p className="text-gray-600 dark:text-gray-400 mb-4">{error}</p>
          <div className="flex items-center justify-center space-x-4">
            <button
              onClick={handleRetry}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              Retry ({retryCount}/3)
            </button>
            <div className={`w-3 h-3 rounded-full ${connectionStatus === 'connected' ? 'bg-green-500' : connectionStatus === 'connecting' ? 'bg-yellow-500' : 'bg-red-500'}`}></div>
            <span className="text-sm text-gray-500 capitalize">{connectionStatus}</span>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Dashboard</h1>
        <div className="flex items-center space-x-4">
          <button
            onClick={() => setShowAddPair(true)}
            className="btn-primary flex items-center"
          >
            <Plus className="w-4 h-4 mr-2" />
            Add Pair
          </button>
        </div>
      </div>

      {/* API Connection Test */}
      <ApiTest />

      {/* Trading Controls */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="card p-6">
          <h2 className="text-lg font-semibold mb-4">Trading Controls</h2>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">Trading Enabled</span>
              <button
                onClick={toggleTrading}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                  settings?.trading_enabled ? 'bg-primary-600' : 'bg-gray-200'
                }`}
              >
                <span
                  className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                    settings?.trading_enabled ? 'translate-x-6' : 'translate-x-1'
                  }`}
                />
              </button>
            </div>
            
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">Order Confirmation Required</span>
              <button
                onClick={toggleOrderConfirmation}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                  settings?.order_confirmation_required ? 'bg-primary-600' : 'bg-gray-200'
                }`}
              >
                <span
                  className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                    settings?.order_confirmation_required ? 'translate-x-6' : 'translate-x-1'
                  }`}
                />
              </button>
            </div>
          </div>
        </div>

        <div className="card p-6">
          <h2 className="text-lg font-semibold mb-4">System Status</h2>
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600 dark:text-gray-400">Active Pairs</span>
              <span className="font-medium">{pairs?.filter(p => p.status === 'active').length || 0}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600 dark:text-gray-400">Recent Signals</span>
              <span className="font-medium">{signals?.length || 0}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600 dark:text-gray-400">Pending Orders</span>
              <span className="font-medium">{pendingConfirmations?.length || 0}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Trading Pairs */}
      <div className="card">
        <div className="p-6 border-b border-gray-200 dark:border-gray-700">
          <h2 className="text-lg font-semibold">Trading Pairs</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50 dark:bg-gray-700">
              <tr>
                                 <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                   Symbol
                 </th>
                 <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                   Strategy
                 </th>
                 <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                   Status
                 </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
              {pairs?.map((pair) => (
                <tr key={pair.id}>
                                     <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900 dark:text-white">
                     {pair.symbol}
                   </td>
                   <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-300">
                     {pair.base_asset}/{pair.quote_asset}
                   </td>
                   <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                      pair.status === 'active' 
                        ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                        : 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
                    }`}>
                      {pair.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-300">
                    <button
                      onClick={() => handleDeletePair(pair.id)}
                      className="text-red-600 hover:text-red-900 dark:hover:text-red-400"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Recent Signals */}
      <div className="card">
        <div className="p-6 border-b border-gray-200 dark:border-gray-700">
          <h2 className="text-lg font-semibold">Recent Signals</h2>
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
                  Side
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  Entry Price
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  Confidence
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  Status
                </th>
              </tr>
            </thead>
            <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
              {signals?.map((signal) => (
                <tr key={signal.id}>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900 dark:text-white">
                    {signal.pair_id}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-300">
                    {signal.strategy}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                      signal.side === 'buy' 
                        ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                        : 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
                    }`}>
                      {signal.side.toUpperCase()}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-300">
                    ${signal.entry_price.toFixed(2)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-300">
                    {(signal.confidence * 100).toFixed(1)}%
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                      signal.status === 'active' 
                        ? 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200'
                        : signal.status === 'executed'
                        ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                        : 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200'
                    }`}>
                      {signal.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Pending Confirmations */}
      {pendingConfirmations && pendingConfirmations.length > 0 && (
        <div className="card">
          <div className="p-6 border-b border-gray-200 dark:border-gray-700">
            <h2 className="text-lg font-semibold">Pending Order Confirmations</h2>
          </div>
          <div className="p-6">
            <div className="space-y-4">
              {pendingConfirmations?.map((confirmation) => (
                <div key={confirmation.id} className="flex items-center justify-between p-4 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg">
                  <div className="flex-1">
                    <div className="flex items-center space-x-4">
                      <AlertTriangle className="w-5 h-5 text-yellow-600" />
                      <div>
                        <p className="text-sm font-medium text-gray-900 dark:text-white">
                          {confirmation.side.toUpperCase()} {confirmation.pair_id}
                        </p>
                        <p className="text-sm text-gray-500 dark:text-gray-400">
                          Entry: ${confirmation.price} | SL: ${confirmation.stop_loss} | TP: ${confirmation.take_profit}
                        </p>
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => handleConfirmOrder(confirmation.id)}
                      className="btn-primary flex items-center"
                    >
                      <CheckCircle className="w-4 h-4 mr-1" />
                      Confirm
                    </button>
                    <button
                      onClick={() => handleRejectOrder(confirmation.id)}
                      className="btn-danger flex items-center"
                    >
                      <XCircle className="w-4 h-4 mr-1" />
                      Reject
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Add Pair Modal */}
      {showAddPair && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white dark:bg-gray-800">
            <div className="mt-3">
                             <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">Add New Trading Pair</h3>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Symbol (Name)
                  </label>
                  <input
                    type="text"
                    value={newPair.symbol}
                    onChange={(e) => setNewPair(prev => ({ ...prev, symbol: e.target.value }))}
                    className="input-field"
                    placeholder="BTCUSDT"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Strategy
                  </label>
                  <select
                    value={newPair.strategy}
                    onChange={(e) => setNewPair(prev => ({ ...prev, strategy: e.target.value }))}
                    className="input-field"
                  >
                    <option value="">Select Strategy</option>
                    {availableStrategies.map(strategy => (
                      <option key={strategy} value={strategy}>
                        {strategy}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
              <div className="flex justify-end space-x-3 mt-6">
                <button
                  onClick={() => setShowAddPair(false)}
                  className="btn-secondary"
                >
                  Cancel
                </button>
                <button
                  onClick={handleAddPair}
                  className="btn-primary"
                  disabled={!newPair.symbol || !newPair.strategy}
                >
                  Add Trading Pair
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Dashboard;
