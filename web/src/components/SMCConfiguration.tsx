import React, { useState, useEffect } from 'react';
import { Settings, Download, Upload, Save, AlertTriangle, CheckCircle, X } from 'lucide-react';
import { SMCConfiguration, SMCPreset } from '../types/api';
import apiClient from '../services/api';

interface SMCConfigurationProps {
  value?: SMCConfiguration;
  onChange: (config: SMCConfiguration) => void;
  onValidationChange: (isValid: boolean, errors: string[], warnings: string[]) => void;
}

const SMCConfiguration: React.FC<SMCConfigurationProps> = ({ value, onChange, onValidationChange }) => {
  const [availablePresets, setAvailablePresets] = useState<string[]>([]);
  const [selectedPreset, setSelectedPreset] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [validationResult, setValidationResult] = useState<{ valid: boolean; errors: string[]; warnings: string[] }>({
    valid: false,
    errors: [],
    warnings: []
  });

  // Default SMC configuration
  const defaultConfig: SMCConfiguration = {
    name: 'Custom SMC',
    description: 'Custom SMC configuration',
    htf_timeframe: '4h',
    ltf_timeframe: '15m',
    scalping_mode: false,
    indicators: {
      rsi: { enabled: true, period: 14, overbought: 70, oversold: 30 },
      macd: { enabled: true, fast_period: 12, slow_period: 26, signal_period: 9 },
      bbands: { enabled: true, period: 20, deviation: 2.0 },
      stochastic: { enabled: false, k_period: 14, d_period: 3, overbought: 80, oversold: 20 },
      volume: { enabled: true, period: 20 },
      atr: { enabled: true, period: 14 }
    },
    filters: {
      rsi: { enabled: true, min_confidence: 0.6, overbought: 70, oversold: 30 },
      volume: { enabled: true, min_volume_ratio: 1.2 },
      bbands: { enabled: true, position_threshold: 0.2 },
      macd: { enabled: true, signal_cross: true },
      stochastic: { enabled: false, overbought: 80, oversold: 20 },
      min_filters_required: 3
    },
    smc_elements: {
      order_blocks: { enabled: true, lookback_bars: 25, volume_threshold: 2.0 },
      fair_value_gaps: { enabled: true, min_gap_pct: 1.0 },
      liquidity_pools: { enabled: true, swing_threshold: 0.03 },
      break_of_structure: { enabled: true, confirmation_bars: 3 }
    },
    risk_management: {
      risk_per_trade: 0.01,
      min_risk_reward: 3.0,
      max_positions: 2,
      sl_buffer_atr: 0.2
    }
  };

  const [config, setConfig] = useState<SMCConfiguration>(value || defaultConfig);

  useEffect(() => {
    loadAvailablePresets();
  }, []);

  useEffect(() => {
    if (value) {
      setConfig(value);
    }
  }, [value]);

  useEffect(() => {
    validateConfiguration();
  }, [config]);

  const loadAvailablePresets = async () => {
    try {
      setLoading(true);
      const presets = await apiClient.getSMCPresets();
      setAvailablePresets(presets);
    } catch (error) {
      console.error('Failed to load SMC presets:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadPreset = async (presetName: string) => {
    try {
      setLoading(true);
      const presetData = await apiClient.getSMCPreset(presetName);
      setConfig(presetData);
      setSelectedPreset(presetName);
      onChange(presetData);
    } catch (error) {
      console.error(`Failed to load preset ${presetName}:`, error);
    } finally {
      setLoading(false);
    }
  };

  const validateConfiguration = async () => {
    try {
      const result = await apiClient.validateSMCConfiguration(config);
      setValidationResult(result);
      onValidationChange(result.valid, result.errors, result.warnings);
    } catch (error) {
      console.error('Failed to validate SMC configuration:', error);
      const errorResult = { valid: false, errors: ['Validation failed'], warnings: [] };
      setValidationResult(errorResult);
      onValidationChange(false, errorResult.errors, errorResult.warnings);
    }
  };

  const updateConfig = (updates: Partial<SMCConfiguration>) => {
    const newConfig = { ...config, ...updates };
    setConfig(newConfig);
    onChange(newConfig);
  };

  const updateIndicator = (indicatorName: string, updates: any) => {
    const newIndicators = { ...config.indicators };
    newIndicators[indicatorName as keyof typeof newIndicators] = { ...newIndicators[indicatorName as keyof typeof newIndicators], ...updates };
    updateConfig({ indicators: newIndicators });
  };

  const updateFilter = (filterName: string, updates: any) => {
    const newFilters = { ...config.filters };
    newFilters[filterName as keyof typeof newFilters] = { ...newFilters[filterName as keyof typeof newFilters], ...updates };
    updateConfig({ filters: newFilters });
  };

  const updateSMCElement = (elementName: string, updates: any) => {
    const newElements = { ...config.smc_elements };
    newElements[elementName as keyof typeof newElements] = { ...newElements[elementName as keyof typeof newElements], ...updates };
    updateConfig({ smc_elements: newElements });
  };

  const updateRiskManagement = (updates: any) => {
    updateConfig({ risk_management: { ...config.risk_management, ...updates } });
  };

  const resetToDefault = () => {
    setConfig(defaultConfig);
    setSelectedPreset('');
    onChange(defaultConfig);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <Settings className="w-5 h-5 text-blue-600" />
          <h3 className="text-lg font-semibold">SMC Strategy Configuration</h3>
        </div>
        <div className="flex items-center space-x-2">
          <button
            onClick={resetToDefault}
            className="px-3 py-1 text-sm font-medium rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-600 transition-colors"
          >
            Reset to Default
          </button>
        </div>
      </div>

      {/* Preset Selection */}
      <div className="bg-gray-50 dark:bg-gray-800 p-4 rounded-lg">
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          Load Preset Configuration
        </label>
        <div className="flex space-x-2">
          <select
            value={selectedPreset}
            onChange={(e) => {
              setSelectedPreset(e.target.value);
              if (e.target.value) {
                loadPreset(e.target.value);
              }
            }}
            className="flex-1 input-field"
            disabled={loading}
          >
            <option value="">Select a preset...</option>
            {availablePresets.map((preset) => (
              <option key={preset} value={preset}>
                {preset.charAt(0).toUpperCase() + preset.slice(1)} SMC
              </option>
            ))}
          </select>
          {loading && <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600"></div>}
        </div>
      </div>

      {/* Configuration Name and Description */}
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Configuration Name
          </label>
          <input
            type="text"
            value={config.name}
            onChange={(e) => updateConfig({ name: e.target.value })}
            className="input-field"
            placeholder="Enter configuration name"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Description
          </label>
          <input
            type="text"
            value={config.description}
            onChange={(e) => updateConfig({ description: e.target.value })}
            className="input-field"
            placeholder="Enter description"
          />
        </div>
      </div>

      {/* Timeframes and Scalping Mode */}
      <div className="grid grid-cols-3 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            HTF Timeframe
          </label>
          <select
            value={config.htf_timeframe}
            onChange={(e) => updateConfig({ htf_timeframe: e.target.value })}
            className="input-field"
          >
            <option value="1h">1h</option>
            <option value="4h">4h</option>
            <option value="1d">1d</option>
          </select>
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            LTF Timeframe
          </label>
          <select
            value={config.ltf_timeframe}
            onChange={(e) => updateConfig({ ltf_timeframe: e.target.value })}
            className="input-field"
          >
            <option value="5m">5m</option>
            <option value="15m">15m</option>
            <option value="30m">30m</option>
            <option value="1h">1h</option>
          </select>
        </div>
        <div className="flex items-center">
          <label className="flex items-center space-x-2">
            <input
              type="checkbox"
              checked={config.scalping_mode}
              onChange={(e) => updateConfig({ scalping_mode: e.target.checked })}
              className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            />
            <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Scalping Mode</span>
          </label>
        </div>
      </div>

      {/* Validation Status */}
      {validationResult.errors.length > 0 || validationResult.warnings.length > 0 ? (
        <div className={`p-4 rounded-lg ${
          validationResult.errors.length > 0 
            ? 'bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800' 
            : 'bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800'
        }`}>
          <div className="flex items-start space-x-2">
            {validationResult.errors.length > 0 ? (
              <AlertTriangle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
            ) : (
              <AlertTriangle className="w-5 h-5 text-yellow-600 flex-shrink-0 mt-0.5" />
            )}
            <div className="flex-1">
              {validationResult.errors.length > 0 && (
                <div className="mb-2">
                  <h4 className="text-sm font-medium text-red-800 dark:text-red-200">Errors:</h4>
                  <ul className="text-sm text-red-700 dark:text-red-300 list-disc list-inside">
                    {validationResult.errors.map((error, index) => (
                      <li key={index}>{error}</li>
                    ))}
                  </ul>
                </div>
              )}
              {validationResult.warnings.length > 0 && (
                <div>
                  <h4 className="text-sm font-medium text-yellow-800 dark:text-yellow-200">Warnings:</h4>
                  <ul className="text-sm text-yellow-700 dark:text-yellow-300 list-disc list-inside">
                    {validationResult.warnings.map((warning, index) => (
                      <li key={index}>{warning}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </div>
        </div>
      ) : (
        <div className="p-4 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg">
          <div className="flex items-center space-x-2">
            <CheckCircle className="w-5 h-5 text-green-600" />
            <span className="text-sm font-medium text-green-800 dark:text-green-200">
              Configuration is valid
            </span>
          </div>
        </div>
      )}

      {/* Indicators Configuration */}
      <div className="bg-white dark:bg-gray-800 p-6 rounded-lg border border-gray-200 dark:border-gray-700">
        <h4 className="text-lg font-semibold mb-4">Technical Indicators</h4>
        <div className="grid grid-cols-2 gap-6">
          {/* RSI */}
          <div className="space-y-3">
            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                checked={config.indicators.rsi.enabled}
                onChange={(e) => updateIndicator('rsi', { enabled: e.target.checked })}
                className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
              <span className="font-medium">RSI</span>
            </div>
            {config.indicators.rsi.enabled && (
              <div className="grid grid-cols-3 gap-2 ml-6">
                <input
                  type="number"
                  value={config.indicators.rsi.period || 14}
                  onChange={(e) => updateIndicator('rsi', { period: parseInt(e.target.value) })}
                  className="input-field text-sm"
                  placeholder="Period"
                />
                <input
                  type="number"
                  value={config.indicators.rsi.overbought || 70}
                  onChange={(e) => updateIndicator('rsi', { overbought: parseInt(e.target.value) })}
                  className="input-field text-sm"
                  placeholder="Overbought"
                />
                <input
                  type="number"
                  value={config.indicators.rsi.oversold || 30}
                  onChange={(e) => updateIndicator('rsi', { oversold: parseInt(e.target.value) })}
                  className="input-field text-sm"
                  placeholder="Oversold"
                />
              </div>
            )}
          </div>

          {/* MACD */}
          <div className="space-y-3">
            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                checked={config.indicators.macd.enabled}
                onChange={(e) => updateIndicator('macd', { enabled: e.target.checked })}
                className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
              <span className="font-medium">MACD</span>
            </div>
            {config.indicators.macd.enabled && (
              <div className="grid grid-cols-3 gap-2 ml-6">
                <input
                  type="number"
                  value={config.indicators.macd.fast_period || 12}
                  onChange={(e) => updateIndicator('macd', { fast_period: parseInt(e.target.value) })}
                  className="input-field text-sm"
                  placeholder="Fast"
                />
                <input
                  type="number"
                  value={config.indicators.macd.slow_period || 26}
                  onChange={(e) => updateIndicator('macd', { slow_period: parseInt(e.target.value) })}
                  className="input-field text-sm"
                  placeholder="Slow"
                />
                <input
                  type="number"
                  value={config.indicators.macd.signal_period || 9}
                  onChange={(e) => updateIndicator('macd', { signal_period: parseInt(e.target.value) })}
                  className="input-field text-sm"
                  placeholder="Signal"
                />
              </div>
            )}
          </div>

          {/* Bollinger Bands */}
          <div className="space-y-3">
            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                checked={config.indicators.bbands.enabled}
                onChange={(e) => updateIndicator('bbands', { enabled: e.target.checked })}
                className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
              <span className="font-medium">Bollinger Bands</span>
            </div>
            {config.indicators.bbands.enabled && (
              <div className="grid grid-cols-2 gap-2 ml-6">
                <input
                  type="number"
                  value={config.indicators.bbands.period || 20}
                  onChange={(e) => updateIndicator('bbands', { period: parseInt(e.target.value) })}
                  className="input-field text-sm"
                  placeholder="Period"
                />
                <input
                  type="number"
                  step="0.1"
                  value={config.indicators.bbands.deviation || 2.0}
                  onChange={(e) => updateIndicator('bbands', { deviation: parseFloat(e.target.value) })}
                  className="input-field text-sm"
                  placeholder="Deviation"
                />
              </div>
            )}
          </div>

          {/* Volume */}
          <div className="space-y-3">
            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                checked={config.indicators.volume.enabled}
                onChange={(e) => updateIndicator('volume', { enabled: e.target.checked })}
                className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
              <span className="font-medium">Volume</span>
            </div>
            {config.indicators.volume.enabled && (
              <div className="ml-6">
                <input
                  type="number"
                  value={config.indicators.volume.period || 20}
                  onChange={(e) => updateIndicator('volume', { period: parseInt(e.target.value) })}
                  className="input-field text-sm"
                  placeholder="Period"
                />
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Risk Management */}
      <div className="bg-white dark:bg-gray-800 p-6 rounded-lg border border-gray-200 dark:border-gray-700">
        <h4 className="text-lg font-semibold mb-4">Risk Management</h4>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Risk per Trade (%)
            </label>
            <input
              type="number"
              step="0.001"
              value={config.risk_management.risk_per_trade * 100}
              onChange={(e) => updateRiskManagement({ risk_per_trade: parseFloat(e.target.value) / 100 })}
              className="input-field"
              min="0.1"
              max="10"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Min Risk-Reward Ratio
            </label>
            <input
              type="number"
              step="0.1"
              value={config.risk_management.min_risk_reward}
              onChange={(e) => updateRiskManagement({ min_risk_reward: parseFloat(e.target.value) })}
              className="input-field"
              min="1.0"
              max="10.0"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Max Positions
            </label>
            <input
              type="number"
              value={config.risk_management.max_positions}
              onChange={(e) => updateRiskManagement({ max_positions: parseInt(e.target.value) })}
              className="input-field"
              min="1"
              max="10"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              SL Buffer (ATR)
            </label>
            <input
              type="number"
              step="0.1"
              value={config.risk_management.sl_buffer_atr}
              onChange={(e) => updateRiskManagement({ sl_buffer_atr: parseFloat(e.target.value) })}
              className="input-field"
              min="0.1"
              max="2.0"
            />
          </div>
        </div>
      </div>

      {/* SMC Elements */}
      <div className="bg-white dark:bg-gray-800 p-6 rounded-lg border border-gray-200 dark:border-gray-700">
        <h4 className="text-lg font-semibold mb-4">SMC Elements</h4>
        <div className="grid grid-cols-2 gap-6">
          {/* Order Blocks */}
          <div className="space-y-3">
            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                checked={config.smc_elements.order_blocks.enabled}
                onChange={(e) => updateSMCElement('order_blocks', { enabled: e.target.checked })}
                className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
              <span className="font-medium">Order Blocks</span>
            </div>
            {config.smc_elements.order_blocks.enabled && (
              <div className="grid grid-cols-2 gap-2 ml-6">
                <input
                  type="number"
                  value={config.smc_elements.order_blocks.lookback_bars || 25}
                  onChange={(e) => updateSMCElement('order_blocks', { lookback_bars: parseInt(e.target.value) })}
                  className="input-field text-sm"
                  placeholder="Lookback"
                />
                <input
                  type="number"
                  step="0.1"
                  value={config.smc_elements.order_blocks.volume_threshold || 2.0}
                  onChange={(e) => updateSMCElement('order_blocks', { volume_threshold: parseFloat(e.target.value) })}
                  className="input-field text-sm"
                  placeholder="Volume Threshold"
                />
              </div>
            )}
          </div>

          {/* Fair Value Gaps */}
          <div className="space-y-3">
            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                checked={config.smc_elements.fair_value_gaps.enabled}
                onChange={(e) => updateSMCElement('fair_value_gaps', { enabled: e.target.checked })}
                className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
              <span className="font-medium">Fair Value Gaps</span>
            </div>
            {config.smc_elements.fair_value_gaps.enabled && (
              <div className="ml-6">
                <input
                  type="number"
                  step="0.1"
                  value={config.smc_elements.fair_value_gaps.min_gap_pct || 1.0}
                  onChange={(e) => updateSMCElement('fair_value_gaps', { min_gap_pct: parseFloat(e.target.value) })}
                  className="input-field text-sm"
                  placeholder="Min Gap %"
                />
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default SMCConfiguration;
