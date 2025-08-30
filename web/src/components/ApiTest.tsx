import React, { useState, useEffect } from 'react';
import { CheckCircle, XCircle, Loader } from 'lucide-react';
import apiClient from '../services/api';

interface ApiStatus {
  status: 'loading' | 'success' | 'error';
  message: string;
  data?: any;
}

const ApiTest: React.FC = () => {
  const [apiStatus, setApiStatus] = useState<ApiStatus>({
    status: 'loading',
    message: 'Testing API connection...'
  });

  useEffect(() => {
    testApiConnection();
  }, []);

  const testApiConnection = async () => {
    try {
      setApiStatus({
        status: 'loading',
        message: 'Testing API connection...'
      });

      const status = await apiClient.getStatus();
      
      setApiStatus({
        status: 'success',
        message: 'API connection successful!',
        data: status
      });
    } catch (error) {
      setApiStatus({
        status: 'error',
        message: `API connection failed: ${error instanceof Error ? error.message : 'Unknown error'}`
      });
    }
  };

  const getStatusIcon = () => {
    switch (apiStatus.status) {
      case 'loading':
        return <Loader className="w-5 h-5 animate-spin text-blue-500" />;
      case 'success':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'error':
        return <XCircle className="w-5 h-5 text-red-500" />;
    }
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold mb-4">API Connection Test</h3>
      
      <div className="flex items-center space-x-3 mb-4">
        {getStatusIcon()}
        <span className="text-sm">{apiStatus.message}</span>
      </div>

      {apiStatus.status === 'success' && apiStatus.data && (
        <div className="bg-gray-50 dark:bg-gray-700 rounded p-3">
          <h4 className="font-medium mb-2">Backend Status:</h4>
          <div className="text-sm space-y-1">
            <div><strong>Status:</strong> {apiStatus.data.status}</div>
            <div><strong>Version:</strong> {apiStatus.data.version}</div>
            <div><strong>Trading Mode:</strong> {apiStatus.data.trading_mode}</div>
            <div><strong>Database:</strong> {apiStatus.data.database_connected ? 'Connected' : 'Disconnected'}</div>
            <div><strong>Exchange:</strong> {apiStatus.data.exchange_connected ? 'Connected' : 'Disconnected'}</div>
          </div>
        </div>
      )}

      <button
        onClick={testApiConnection}
        className="mt-4 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 transition-colors"
      >
        Test Again
      </button>
    </div>
  );
};

export default ApiTest;
