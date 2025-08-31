# Web Frontend Package

A modern React-based web application for the Smart Trading Bot that provides an intuitive dashboard for monitoring, controlling, and analyzing trading operations.

## 🚀 Quick Start

### What This Package Does
- **Trading Dashboard**: Real-time monitoring of portfolio, positions, and performance
- **Strategy Management**: View and configure trading strategies
- **Backtesting Interface**: Run and analyze backtest results
- **Signal Monitoring**: Real-time trading signal alerts and management
- **Responsive Design**: Modern UI that works on desktop and mobile devices

### Start the Development Server
```bash
# From the web directory
cd web

# Install dependencies
npm install

# Start development server
npm run dev
```

### Access the Application
- **Development**: http://localhost:5173
- **Production**: http://localhost:3000 (when built)

## 📦 Installation & Setup

### Prerequisites
- Node.js 18+ 
- npm 9+ or yarn 1.22+
- Modern web browser

### Dependencies
```bash
# Core dependencies
npm install react react-dom react-router-dom
npm install @tanstack/react-query axios
npm install recharts @mui/material @emotion/react @emotion/styled

# Development dependencies
npm install -D @types/react @types/react-dom typescript
npm install -D vite @vitejs/plugin-react eslint prettier
```

### Environment Variables
Create a `.env` file in the web directory:

```env
# API Configuration
VITE_API_BASE_URL=http://localhost:8000
VITE_API_TIMEOUT=30000
VITE_WS_URL=ws://localhost:8000/ws

# Feature Flags
VITE_ENABLE_SIMULATION=true
VITE_ENABLE_BACKTESTING=true
VITE_ENABLE_SIGNALS=true

# UI Configuration
VITE_THEME=dark
VITE_DEFAULT_CURRENCY=USD
VITE_REFRESH_INTERVAL=5000
```

## 🎯 Basic Usage

### Dashboard Overview

The main dashboard provides:
- **Portfolio Summary**: Total value, P&L, and performance metrics
- **Active Positions**: Current open positions with real-time updates
- **Recent Trades**: Latest trade history and execution details
- **Market Overview**: Key market indicators and trends
- **Quick Actions**: Start/stop simulation, run backtests, etc.

### Navigation

```typescript
// Main navigation structure
const navigation = [
  { path: '/', label: 'Dashboard', icon: 'dashboard' },
  { path: '/portfolio', label: 'Portfolio', icon: 'account_balance' },
  { path: '/signals', label: 'Signals', icon: 'trending_up' },
  { path: '/backtests', label: 'Backtests', icon: 'analytics' },
  { path: '/strategies', label: 'Strategies', icon: 'psychology' },
  { path: '/settings', label: 'Settings', icon: 'settings' }
];
```

### Real-time Updates

```typescript
// WebSocket connection for real-time data
const useWebSocket = (url: string) => {
  const [data, setData] = useState(null);
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    const ws = new WebSocket(url);
    
    ws.onopen = () => setIsConnected(true);
    ws.onmessage = (event) => setData(JSON.parse(event.data));
    ws.onclose = () => setIsConnected(false);

    return () => ws.close();
  }, [url]);

  return { data, isConnected };
};
```

## 🛠️ Core Components

### 1. App Layout

Main application structure:

```typescript
// src/App.tsx
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ThemeProvider } from '@mui/material/styles';

const App = () => {
  const queryClient = new QueryClient();
  
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider theme={theme}>
        <BrowserRouter>
          <Layout>
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/portfolio" element={<Portfolio />} />
              <Route path="/signals" element={<Signals />} />
              <Route path="/backtests" element={<Backtests />} />
              <Route path="/strategies" element={<Strategies />} />
              <Route path="/settings" element={<Settings />} />
            </Routes>
          </Layout>
        </BrowserRouter>
      </ThemeProvider>
    </QueryClientProvider>
  );
};
```

### 2. Dashboard Component

Main dashboard view:

```typescript
// src/components/Dashboard/Dashboard.tsx
import { PortfolioSummary } from './PortfolioSummary';
import { ActivePositions } from './ActivePositions';
import { RecentTrades } from './RecentTrades';
import { MarketOverview } from './MarketOverview';
import { QuickActions } from './QuickActions';

const Dashboard = () => {
  const { data: portfolio } = usePortfolio();
  const { data: positions } = usePositions();
  const { data: trades } = useRecentTrades();

  return (
    <div className="dashboard">
      <PortfolioSummary portfolio={portfolio} />
      <div className="dashboard-grid">
        <ActivePositions positions={positions} />
        <RecentTrades trades={trades} />
        <MarketOverview />
        <QuickActions />
      </div>
    </div>
  );
};
```

### 3. Portfolio Component

Portfolio management and analysis:

```typescript
// src/components/Portfolio/Portfolio.tsx
import { PortfolioChart } from './PortfolioChart';
import { PositionList } from './PositionList';
import { PerformanceMetrics } from './PerformanceMetrics';
import { TradeHistory } from './TradeHistory';

const Portfolio = () => {
  const { data: portfolio } = usePortfolio();
  const { data: positions } = usePositions();
  const { data: performance } = usePerformance();

  return (
    <div className="portfolio">
      <PortfolioChart data={portfolio?.equity_curve} />
      <div className="portfolio-details">
        <PerformanceMetrics metrics={performance} />
        <PositionList positions={positions} />
        <TradeHistory />
      </div>
    </div>
  );
};
```

### 4. Signals Component

Trading signal management:

```typescript
// src/components/Signals/Signals.tsx
import { SignalList } from './SignalList';
import { SignalFilters } from './SignalFilters';
import { SignalDetails } from './SignalDetails';
import { SignalActions } from './SignalActions';

const Signals = () => {
  const [filters, setFilters] = useState({});
  const { data: signals } = useSignals(filters);
  const [selectedSignal, setSelectedSignal] = useState(null);

  return (
    <div className="signals">
      <SignalFilters filters={filters} onFiltersChange={setFilters} />
      <div className="signals-content">
        <SignalList 
          signals={signals} 
          onSignalSelect={setSelectedSignal} 
        />
        {selectedSignal && (
          <SignalDetails 
            signal={selectedSignal} 
            actions={<SignalActions signal={selectedSignal} />}
          />
        )}
      </div>
    </div>
  );
};
```

### 5. Backtests Component

Backtesting interface:

```typescript
// src/components/Backtests/Backtests.tsx
import { BacktestForm } from './BacktestForm';
import { BacktestResults } from './BacktestResults';
import { BacktestCharts } from './BacktestCharts';
import { BacktestMetrics } from './BacktestMetrics';

const Backtests = () => {
  const [activeBacktest, setActiveBacktest] = useState(null);
  const { data: backtests } = useBacktests();
  const runBacktest = useRunBacktest();

  const handleRunBacktest = async (config) => {
    const result = await runBacktest.mutateAsync(config);
    setActiveBacktest(result);
  };

  return (
    <div className="backtests">
      <BacktestForm onRunBacktest={handleRunBacktest} />
      <div className="backtests-content">
        <BacktestResults 
          backtests={backtests} 
          onSelect={setActiveBacktest} 
        />
        {activeBacktest && (
          <>
            <BacktestCharts backtest={activeBacktest} />
            <BacktestMetrics backtest={activeBacktest} />
          </>
        )}
      </div>
    </div>
  );
};
```

## 📊 Data Management

### API Integration

```typescript
// src/api/client.ts
import axios from 'axios';

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  timeout: import.meta.env.VITE_API_TIMEOUT,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Handle unauthorized access
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);
```

### React Query Hooks

```typescript
// src/hooks/usePortfolio.ts
import { useQuery } from '@tanstack/react-query';
import { getPortfolio } from '../api/portfolio';

export const usePortfolio = () => {
  return useQuery({
    queryKey: ['portfolio'],
    queryFn: getPortfolio,
    refetchInterval: 5000, // Refresh every 5 seconds
    staleTime: 1000, // Consider data stale after 1 second
  });
};

// src/hooks/usePositions.ts
export const usePositions = () => {
  return useQuery({
    queryKey: ['positions'],
    queryFn: getPositions,
    refetchInterval: 3000, // Refresh every 3 seconds
  });
};

// src/hooks/useSignals.ts
export const useSignals = (filters = {}) => {
  return useQuery({
    queryKey: ['signals', filters],
    queryFn: () => getSignals(filters),
    refetchInterval: 10000, // Refresh every 10 seconds
  });
};
```

### State Management

```typescript
// src/store/portfolioSlice.ts
import { createSlice, PayloadAction } from '@reduxjs/toolkit';

interface PortfolioState {
  totalValue: number;
  cash: number;
  positionsValue: number;
  unrealizedPnl: number;
  realizedPnl: number;
  loading: boolean;
  error: string | null;
}

const initialState: PortfolioState = {
  totalValue: 0,
  cash: 0,
  positionsValue: 0,
  unrealizedPnl: 0,
  realizedPnl: 0,
  loading: false,
  error: null,
};

const portfolioSlice = createSlice({
  name: 'portfolio',
  initialState,
  reducers: {
    setPortfolio: (state, action: PayloadAction<Portfolio>) => {
      state.totalValue = action.payload.totalValue;
      state.cash = action.payload.cash;
      state.positionsValue = action.payload.positionsValue;
      state.unrealizedPnl = action.payload.unrealizedPnl;
      state.realizedPnl = action.payload.realizedPnl;
    },
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.loading = action.payload;
    },
    setError: (state, action: PayloadAction<string>) => {
      state.error = action.payload;
    },
  },
});
```

## 🎨 UI Components

### Material-UI Integration

```typescript
// src/theme/index.ts
import { createTheme } from '@mui/material/styles';

export const theme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: '#2196f3',
      light: '#64b5f6',
      dark: '#1976d2',
    },
    secondary: {
      main: '#f50057',
      light: '#ff5983',
      dark: '#c51162',
    },
    background: {
      default: '#121212',
      paper: '#1e1e1e',
    },
  },
  typography: {
    fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
    h1: {
      fontSize: '2.5rem',
      fontWeight: 500,
    },
    h2: {
      fontSize: '2rem',
      fontWeight: 500,
    },
  },
  components: {
    MuiCard: {
      styleOverrides: {
        root: {
          backgroundColor: '#1e1e1e',
          borderRadius: 8,
        },
      },
    },
  },
});
```

### Custom Components

```typescript
// src/components/common/DataCard.tsx
import { Card, CardContent, CardHeader, Typography } from '@mui/material';

interface DataCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon?: React.ReactNode;
  color?: 'primary' | 'secondary' | 'success' | 'error' | 'warning';
}

export const DataCard = ({ title, value, subtitle, icon, color = 'primary' }: DataCardProps) => {
  return (
    <Card className={`data-card data-card--${color}`}>
      <CardHeader
        avatar={icon}
        title={title}
        subheader={subtitle}
        className="data-card__header"
      />
      <CardContent>
        <Typography variant="h4" component="div" className="data-card__value">
          {value}
        </Typography>
      </CardContent>
    </Card>
  );
};

// src/components/common/Chart.tsx
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

interface ChartProps {
  data: Array<{ timestamp: string; value: number }>;
  title: string;
  color?: string;
}

export const Chart = ({ data, title, color = '#2196f3' }: ChartProps) => {
  return (
    <div className="chart">
      <Typography variant="h6" className="chart__title">
        {title}
      </Typography>
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="timestamp" />
          <YAxis />
          <Tooltip />
          <Line type="monotone" dataKey="value" stroke={color} strokeWidth={2} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};
```

## 🔧 Configuration

### Vite Configuration

```typescript
// vite.config.ts
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
      '@components': path.resolve(__dirname, './src/components'),
      '@hooks': path.resolve(__dirname, './src/hooks'),
      '@api': path.resolve(__dirname, './src/api'),
      '@store': path.resolve(__dirname, './src/store'),
      '@utils': path.resolve(__dirname, './src/utils'),
    },
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/ws': {
        target: 'ws://localhost:8000',
        ws: true,
      },
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom'],
          ui: ['@mui/material', '@emotion/react'],
          charts: ['recharts'],
        },
      },
    },
  },
});
```

### ESLint Configuration

```json
// .eslintrc.json
{
  "extends": [
    "eslint:recommended",
    "@typescript-eslint/recommended",
    "plugin:react/recommended",
    "plugin:react-hooks/recommended"
  ],
  "parser": "@typescript-eslint/parser",
  "plugins": ["@typescript-eslint", "react", "react-hooks"],
  "rules": {
    "react/react-in-jsx-scope": "off",
    "react/prop-types": "off",
    "@typescript-eslint/explicit-module-boundary-types": "off",
    "@typescript-eslint/no-unused-vars": ["error", { "argsIgnorePattern": "^_" }]
  },
  "settings": {
    "react": {
      "version": "detect"
    }
  }
}
```

### TypeScript Configuration

```json
// tsconfig.json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,
    "baseUrl": ".",
    "paths": {
      "@/*": ["src/*"],
      "@components/*": ["src/components/*"],
      "@hooks/*": ["src/hooks/*"],
      "@api/*": ["src/api/*"],
      "@store/*": ["src/store/*"],
      "@utils/*": ["src/utils/*"]
    }
  },
  "include": ["src"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
```

## 🚨 Error Handling

### Error Boundaries

```typescript
// src/components/ErrorBoundary/ErrorBoundary.tsx
import React, { Component, ErrorInfo, ReactNode } from 'react';
import { Alert, Button, Container, Typography } from '@mui/material';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Error caught by boundary:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <Container maxWidth="md" sx={{ mt: 4 }}>
          <Alert severity="error" sx={{ mb: 2 }}>
            <Typography variant="h6" gutterBottom>
              Something went wrong
            </Typography>
            <Typography variant="body2" sx={{ mb: 2 }}>
              {this.state.error?.message}
            </Typography>
            <Button 
              variant="contained" 
              onClick={() => window.location.reload()}
            >
              Reload Page
            </Button>
          </Alert>
        </Container>
      );
    }

    return this.props.children;
  }
}
```

### API Error Handling

```typescript
// src/hooks/useApiError.ts
import { useCallback } from 'react';
import { useSnackbar } from 'notistack';

export const useApiError = () => {
  const { enqueueSnackbar } = useSnackbar();

  const handleError = useCallback((error: any) => {
    let message = 'An unexpected error occurred';
    let severity: 'error' | 'warning' = 'error';

    if (error.response) {
      const { status, data } = error.response;
      
      switch (status) {
        case 400:
          message = data?.message || 'Invalid request';
          break;
        case 401:
          message = 'Authentication required';
          severity = 'warning';
          break;
        case 403:
          message = 'Access denied';
          break;
        case 404:
          message = 'Resource not found';
          break;
        case 429:
          message = 'Too many requests';
          severity = 'warning';
          break;
        case 500:
          message = 'Server error';
          break;
        default:
          message = data?.message || `HTTP ${status} error`;
      }
    } else if (error.request) {
      message = 'Network error - please check your connection';
    } else if (error.message) {
      message = error.message;
    }

    enqueueSnackbar(message, { variant: severity });
  }, [enqueueSnackbar]);

  return { handleError };
};
```

## 📊 Performance Optimization

### Code Splitting

```typescript
// src/App.tsx
import { lazy, Suspense } from 'react';
import { CircularProgress } from '@mui/material';

// Lazy load components
const Dashboard = lazy(() => import('./components/Dashboard/Dashboard'));
const Portfolio = lazy(() => import('./components/Portfolio/Portfolio'));
const Signals = lazy(() => import('./components/Signals/Signals'));
const Backtests = lazy(() => import('./components/Backtests/Backtests'));

// Loading component
const LoadingSpinner = () => (
  <div className="loading-spinner">
    <CircularProgress />
  </div>
);

// Wrap routes with Suspense
<Suspense fallback={<LoadingSpinner />}>
  <Routes>
    <Route path="/" element={<Dashboard />} />
    <Route path="/portfolio" element={<Portfolio />} />
    <Route path="/signals" element={<Signals />} />
    <Route path="/backtests" element={<Backtests />} />
  </Routes>
</Suspense>
```

### Memoization

```typescript
// src/components/Portfolio/PortfolioChart.tsx
import { memo, useMemo } from 'react';

interface PortfolioChartProps {
  data: Array<{ timestamp: string; value: number }>;
  width: number;
  height: number;
}

export const PortfolioChart = memo(({ data, width, height }: PortfolioChartProps) => {
  // Memoize processed data
  const processedData = useMemo(() => {
    return data.map(item => ({
      ...item,
      timestamp: new Date(item.timestamp).toLocaleDateString(),
      value: Number(item.value.toFixed(2))
    }));
  }, [data]);

  // Memoize chart configuration
  const chartConfig = useMemo(() => ({
    width,
    height,
    margin: { top: 20, right: 30, left: 20, bottom: 5 }
  }), [width, height]);

  return (
    <ResponsiveContainer width="100%" height={height}>
      <LineChart data={processedData} {...chartConfig}>
        {/* Chart components */}
      </LineChart>
    </ResponsiveContainer>
  );
});

PortfolioChart.displayName = 'PortfolioChart';
```

## 🧪 Testing

### Component Testing

```typescript
// src/components/DataCard/DataCard.test.tsx
import { render, screen } from '@testing-library/react';
import { DataCard } from './DataCard';

describe('DataCard', () => {
  it('renders title and value correctly', () => {
    render(
      <DataCard 
        title="Total Value" 
        value="$10,000" 
        subtitle="Portfolio total"
      />
    );

    expect(screen.getByText('Total Value')).toBeInTheDocument();
    expect(screen.getByText('$10,000')).toBeInTheDocument();
    expect(screen.getByText('Portfolio total')).toBeInTheDocument();
  });

  it('applies correct color class', () => {
    render(
      <DataCard 
        title="Test" 
        value="100" 
        color="success"
      />
    );

    const card = screen.getByText('Test').closest('.data-card');
    expect(card).toHaveClass('data-card--success');
  });
});
```

### Hook Testing

```typescript
// src/hooks/usePortfolio.test.ts
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { usePortfolio } from './usePortfolio';
import { getPortfolio } from '../api/portfolio';

// Mock API
jest.mock('../api/portfolio');
const mockGetPortfolio = getPortfolio as jest.MockedFunction<typeof getPortfolio>;

const wrapper = ({ children }: { children: React.ReactNode }) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  });
  return (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );
};

describe('usePortfolio', () => {
  it('fetches portfolio data successfully', async () => {
    const mockPortfolio = {
      totalValue: 10000,
      cash: 5000,
      positionsValue: 5000,
    };

    mockGetPortfolio.mockResolvedValue(mockPortfolio);

    const { result } = renderHook(() => usePortfolio(), { wrapper });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.data).toEqual(mockPortfolio);
  });
});
```

## 🔒 Security

### Input Validation

```typescript
// src/utils/validation.ts
import * as yup from 'yup';

export const backtestSchema = yup.object({
  symbol: yup.string().required('Symbol is required'),
  strategy: yup.string().required('Strategy is required'),
  startDate: yup.date().required('Start date is required'),
  endDate: yup.date().required('End date is required'),
  timeframes: yup.array().of(yup.string()).min(1, 'At least one timeframe is required'),
  initialBalance: yup.number().positive('Initial balance must be positive').required(),
  commission: yup.number().min(0, 'Commission must be non-negative').max(0.1, 'Commission too high'),
});

export const signalSchema = yup.object({
  symbol: yup.string().required('Symbol is required'),
  side: yup.string().oneOf(['long', 'short'], 'Invalid side').required(),
  entry: yup.number().positive('Entry price must be positive').required(),
  stopLoss: yup.number().positive('Stop loss must be positive').required(),
  takeProfit: yup.number().positive('Take profit must be positive').required(),
  confidence: yup.number().min(0, 'Confidence must be non-negative').max(1, 'Confidence must be <= 1').required(),
});
```

### XSS Prevention

```typescript
// src/utils/sanitization.ts
import DOMPurify from 'dompurify';

export const sanitizeHtml = (html: string): string => {
  return DOMPurify.sanitize(html, {
    ALLOWED_TAGS: ['b', 'i', 'em', 'strong', 'a'],
    ALLOWED_ATTR: ['href'],
  });
};

export const sanitizeInput = (input: string): string => {
  return input.replace(/[<>]/g, '');
};
```

## 📊 Monitoring

### Performance Monitoring

```typescript
// src/utils/performance.ts
export const measurePerformance = (name: string, fn: () => void) => {
  const start = performance.now();
  fn();
  const end = performance.now();
  
  console.log(`${name} took ${end - start} milliseconds`);
  
  // Send to analytics if needed
  if (window.gtag) {
    window.gtag('event', 'performance_measure', {
      event_category: 'performance',
      event_label: name,
      value: Math.round(end - start),
    });
  }
};

export const trackPageLoad = () => {
  window.addEventListener('load', () => {
    const navigation = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
    const loadTime = navigation.loadEventEnd - navigation.loadEventStart;
    
    console.log(`Page load time: ${loadTime} milliseconds`);
  });
};
```

### Error Tracking

```typescript
// src/utils/errorTracking.ts
export const trackError = (error: Error, context?: Record<string, any>) => {
  console.error('Error tracked:', error, context);
  
  // Send to error tracking service
  if (window.gtag) {
    window.gtag('event', 'exception', {
      description: error.message,
      fatal: false,
      ...context,
    });
  }
};

export const setupErrorTracking = () => {
  window.addEventListener('error', (event) => {
    trackError(event.error, {
      filename: event.filename,
      lineno: event.lineno,
      colno: event.colno,
    });
  });

  window.addEventListener('unhandledrejection', (event) => {
    trackError(new Error(event.reason), {
      type: 'unhandledrejection',
    });
  });
};
```

## 🤝 Contributing

### Adding New Features

1. Create feature branch from main
2. Implement new functionality
3. Add comprehensive tests
4. Update documentation
5. Submit pull request

### Code Style

```bash
# Format code
npm run format

# Lint code
npm run lint

# Fix linting issues
npm run lint:fix

# Type check
npm run type-check
```

### Testing

```bash
# Run tests
npm test

# Run tests with coverage
npm run test:coverage

# Run tests in watch mode
npm run test:watch

# Run e2e tests
npm run test:e2e
```

## 📝 License

This package is part of the Smart Trading Bot project and follows the same license terms.

---

**Happy Trading! 🚀**

*Remember: Always test UI components thoroughly and ensure responsive design works across all devices.*
