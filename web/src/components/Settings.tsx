import React, { useState, useEffect } from 'react';
import { Save, TestTube, Bell, Shield, DollarSign } from 'lucide-react';
import { Settings as SettingsType } from '../types/api';
import apiClient from '../services/api';

const Settings: React.FC = () => {
  const [settings, setSettings] = useState<SettingsType | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [testingNotification, setTestingNotification] = useState(false);
  const [formData, setFormData] = useState<Partial<SettingsType>>({});

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      const settingsData = await apiClient.getSettings();
      setSettings(settingsData);
      setFormData(settingsData);
    } catch (error) {
      console.error('Failed to load settings:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    if (!formData) return;
    
    setSaving(true);
    try {
      const updatedSettings = await apiClient.updateSettings(formData);
      setSettings(updatedSettings);
      setFormData(updatedSettings);
    } catch (error) {
      console.error('Failed to save settings:', error);
    } finally {
      setSaving(false);
    }
  };

  const handleTestNotification = async () => {
    setTestingNotification(true);
    try {
      await apiClient.testNotification();
      alert('Test notification sent successfully!');
    } catch (error) {
      console.error('Failed to send test notification:', error);
      alert('Failed to send test notification. Please check your Telegram configuration.');
    } finally {
      setTestingNotification(false);
    }
  };

  const handleInputChange = (field: keyof SettingsType, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Settings</h1>
        <button
          onClick={handleSave}
          disabled={saving}
          className="btn-primary flex items-center justify-center w-full sm:w-auto"
        >
          <Save className="w-4 h-4 mr-2" />
          {saving ? 'Saving...' : 'Save Settings'}
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Trading Settings */}
        <div className="card p-6">
          <div className="flex items-center mb-6">
            <DollarSign className="w-5 h-5 text-primary-600 mr-2 flex-shrink-0" />
            <h2 className="text-lg font-semibold">Trading Settings</h2>
          </div>
          
          <div className="space-y-6">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
              <div className="flex-1 min-w-0">
                <label className="text-sm font-medium text-gray-700 dark:text-gray-300 block">
                  Trading Enabled
                </label>
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                  Enable or disable live trading
                </p>
              </div>
              <div className="flex-shrink-0">
                <button
                  onClick={() => handleInputChange('trading_enabled', !formData.trading_enabled)}
                  className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                    formData.trading_enabled ? 'bg-primary-600' : 'bg-gray-200'
                  }`}
                >
                  <span
                    className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                      formData.trading_enabled ? 'translate-x-6' : 'translate-x-1'
                    }`}
                  />
                </button>
              </div>
            </div>

            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
              <div className="flex-1 min-w-0">
                <label className="text-sm font-medium text-gray-700 dark:text-gray-300 block">
                  Order Confirmation
                </label>
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                  Require manual confirmation for orders
                </p>
              </div>
              <div className="flex-shrink-0">
                <button
                  onClick={() => handleInputChange('order_confirmation_required', !formData.order_confirmation_required)}
                  className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                    formData.order_confirmation_required ? 'bg-primary-600' : 'bg-gray-200'
                  }`}
                >
                  <span
                    className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                      formData.order_confirmation_required ? 'translate-x-6' : 'translate-x-1'
                    }`}
                  />
                </button>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Max Open Positions
              </label>
              <input
                type="number"
                value={formData.max_open_positions || 0}
                onChange={(e) => handleInputChange('max_open_positions', parseInt(e.target.value))}
                className="input-field"
                min="1"
                max="50"
              />
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">
                Maximum number of simultaneous open positions
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Risk per Trade (%)
              </label>
              <input
                type="number"
                value={formData.risk_per_trade || 0}
                onChange={(e) => handleInputChange('risk_per_trade', parseFloat(e.target.value))}
                className="input-field"
                min="0.1"
                max="10"
                step="0.1"
              />
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">
                Percentage of account balance to risk per trade
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Default Leverage
              </label>
              <input
                type="number"
                value={formData.default_leverage || 1}
                onChange={(e) => handleInputChange('default_leverage', parseFloat(e.target.value))}
                className="input-field"
                min="1"
                max="100"
                step="1"
              />
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">
                Default leverage for futures trading
              </p>
            </div>
          </div>
        </div>

        {/* Notification Settings */}
        <div className="card p-6">
          <div className="flex items-center mb-6">
            <Bell className="w-5 h-5 text-primary-600 mr-2 flex-shrink-0" />
            <h2 className="text-lg font-semibold">Notification Settings</h2>
          </div>
          
          <div className="space-y-6">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
              <div className="flex-1 min-w-0">
                <label className="text-sm font-medium text-gray-700 dark:text-gray-300 block">
                  Telegram Notifications
                </label>
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                  Enable Telegram notifications
                </p>
              </div>
              <div className="flex-shrink-0">
                <button
                  onClick={() => handleInputChange('telegram_enabled', !formData.telegram_enabled)}
                  className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                    formData.telegram_enabled ? 'bg-primary-600' : 'bg-gray-200'
                  }`}
                >
                  <span
                    className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                      formData.telegram_enabled ? 'translate-x-6' : 'translate-x-1'
                    }`}
                  />
                </button>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Telegram Bot Token
              </label>
              <input
                type="password"
                value={formData.telegram_bot_token || ''}
                onChange={(e) => handleInputChange('telegram_bot_token', e.target.value)}
                className="input-field"
                placeholder="1234567890:ABCdefGHIjklMNOpqrsTUVwxyz"
              />
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">
                Bot token from @BotFather
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Telegram Chat ID
              </label>
              <input
                type="text"
                value={formData.telegram_chat_id || ''}
                onChange={(e) => handleInputChange('telegram_chat_id', e.target.value)}
                className="input-field"
                placeholder="123456789"
              />
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">
                Your Telegram chat ID
              </p>
            </div>

            <button
              onClick={handleTestNotification}
              disabled={testingNotification || !formData.telegram_enabled}
              className="btn-secondary flex items-center w-full justify-center"
            >
              <TestTube className="w-4 h-4 mr-2" />
              {testingNotification ? 'Sending...' : 'Test Notification'}
            </button>
          </div>
        </div>
      </div>

      {/* Security Settings */}
      <div className="card p-6">
        <div className="flex items-center mb-6">
          <Shield className="w-5 h-5 text-primary-600 mr-2 flex-shrink-0" />
          <h2 className="text-lg font-semibold">Security & Risk Management</h2>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          <div>
            <h3 className="text-md font-medium text-gray-900 dark:text-white mb-4">Risk Management Rules</h3>
            <div className="space-y-3 text-sm text-gray-600 dark:text-gray-400">
              <div className="flex items-start">
                <div className="w-2 h-2 bg-green-500 rounded-full mr-3 mt-2 flex-shrink-0"></div>
                <span>Minimum Risk/Reward ratio: 3:1</span>
              </div>
              <div className="flex items-start">
                <div className="w-2 h-2 bg-green-500 rounded-full mr-3 mt-2 flex-shrink-0"></div>
                <span>Maximum daily loss: 5% of account</span>
              </div>
              <div className="flex items-start">
                <div className="w-2 h-2 bg-green-500 rounded-full mr-3 mt-2 flex-shrink-0"></div>
                <span>Position sizing based on risk percentage</span>
              </div>
              <div className="flex items-start">
                <div className="w-2 h-2 bg-green-500 rounded-full mr-3 mt-2 flex-shrink-0"></div>
                <span>Automatic stop-loss placement</span>
              </div>
            </div>
          </div>
          
          <div>
            <h3 className="text-md font-medium text-gray-900 dark:text-white mb-4">Safety Features</h3>
            <div className="space-y-3 text-sm text-gray-600 dark:text-gray-400">
              <div className="flex items-start">
                <div className="w-2 h-2 bg-blue-500 rounded-full mr-3 mt-2 flex-shrink-0"></div>
                <span>Order confirmation system</span>
              </div>
              <div className="flex items-start">
                <div className="w-2 h-2 bg-blue-500 rounded-full mr-3 mt-2 flex-shrink-0"></div>
                <span>Real-time position monitoring</span>
              </div>
              <div className="flex items-start">
                <div className="w-2 h-2 bg-blue-500 rounded-full mr-3 mt-2 flex-shrink-0"></div>
                <span>Automatic emergency stop</span>
              </div>
              <div className="flex items-start">
                <div className="w-2 h-2 bg-blue-500 rounded-full mr-3 mt-2 flex-shrink-0"></div>
                <span>Comprehensive audit logging</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Current Settings Summary */}
      <div className="card p-6">
        <h2 className="text-lg font-semibold mb-6">Current Configuration</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 text-sm">
          <div className="flex flex-col sm:flex-row sm:items-center gap-2">
            <span className="text-gray-500 dark:text-gray-400">Trading Status:</span>
            <span className={`font-medium ${
              formData.trading_enabled ? 'text-green-600' : 'text-red-600'
            }`}>
              {formData.trading_enabled ? 'Enabled' : 'Disabled'}
            </span>
          </div>
          <div className="flex flex-col sm:flex-row sm:items-center gap-2">
            <span className="text-gray-500 dark:text-gray-400">Order Confirmation:</span>
            <span className={`font-medium ${
              formData.order_confirmation_required ? 'text-green-600' : 'text-yellow-600'
            }`}>
              {formData.order_confirmation_required ? 'Required' : 'Auto'}
            </span>
          </div>
          <div className="flex flex-col sm:flex-row sm:items-center gap-2">
            <span className="text-gray-500 dark:text-gray-400">Max Positions:</span>
            <span className="font-medium">{formData.max_open_positions}</span>
          </div>
          <div className="flex flex-col sm:flex-row sm:items-center gap-2">
            <span className="text-gray-500 dark:text-gray-400">Risk per Trade:</span>
            <span className="font-medium">{formData.risk_per_trade}%</span>
          </div>
          <div className="flex flex-col sm:flex-row sm:items-center gap-2">
            <span className="text-gray-500 dark:text-gray-400">Default Leverage:</span>
            <span className="font-medium">{formData.default_leverage}x</span>
          </div>
          <div className="flex flex-col sm:flex-row sm:items-center gap-2">
            <span className="text-gray-500 dark:text-gray-400">Telegram:</span>
            <span className={`font-medium ${
              formData.telegram_enabled ? 'text-green-600' : 'text-red-600'
            }`}>
              {formData.telegram_enabled ? 'Enabled' : 'Disabled'}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Settings;
