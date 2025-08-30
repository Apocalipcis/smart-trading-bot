import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/Layout';
import Dashboard from './components/Dashboard';
import Backtests from './components/Backtests';
import Settings from './components/Settings';
import ErrorBoundary from './components/ErrorBoundary';

// Suppress React Router v7 warnings
const router = {
  future: {
    v7_startTransition: true,
    v7_relativeSplatPath: true
  }
};

const App: React.FC = () => {
  return (
    <Router {...router}>
      <Layout>
        <Routes>
          <Route path="/" element={
            <ErrorBoundary>
              <Dashboard />
            </ErrorBoundary>
          } />
          <Route path="/backtests" element={<Backtests />} />
          <Route path="/settings" element={<Settings />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Layout>
    </Router>
  );
};

export default App;
