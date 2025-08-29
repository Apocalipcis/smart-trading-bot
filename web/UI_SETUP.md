# UI Backend Integration Setup

This guide explains how to configure the React frontend to work with the FastAPI backend.

## Quick Start

### Option 1: Development Script (Recommended)
```bash
# From the project root
./scripts/dev.sh
```

This script will:
- Set up Python virtual environment
- Install dependencies
- Start backend on port 8000
- Start frontend on port 3000
- Configure proxy automatically

### Option 2: Manual Setup

#### 1. Start Backend
```bash
# From project root
source venv/bin/activate
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
```

#### 2. Start Frontend
```bash
# From web directory
cd web
npm install
npm run dev
```

### Option 3: Docker Development
```bash
# From project root
docker-compose -f docker-compose.dev-full.yml up --build
```

## Configuration

### Environment Variables

The frontend uses the following environment variables:

- `VITE_API_URL`: Backend API URL (optional, defaults to relative URLs)

For development with proxy (recommended), leave `VITE_API_URL` unset.

### Vite Proxy Configuration

The `vite.config.ts` includes proxy configuration that forwards `/api` requests to the backend:

```typescript
proxy: {
  '/api': {
    target: 'http://localhost:8000',
    changeOrigin: true,
    secure: false,
  },
}
```

## API Integration

### API Client

The frontend uses an Axios-based API client (`src/services/api.ts`) that:

- Automatically handles proxy configuration
- Includes request/response interceptors for logging
- Provides type-safe API calls
- Supports Server-Sent Events for real-time updates

### Available Endpoints

The frontend integrates with all backend endpoints:

- **Trading Pairs**: `/api/v1/pairs`
- **Signals**: `/api/v1/signals` (including SSE stream)
- **Backtests**: `/api/v1/backtests`
- **Settings**: `/api/v1/settings`
- **Orders**: `/api/v1/orders`
- **Status**: `/api/v1/status/health`
- **Strategies**: `/api/v1/strategies`
- **Markets**: `/api/v1/markets`

### Testing API Connection

The Dashboard includes an API connection test component that:

- Tests backend connectivity on load
- Shows backend status information
- Provides manual retry functionality
- Displays connection errors

## Development Workflow

### Hot Reload

Both frontend and backend support hot reload:

- **Backend**: Uses uvicorn with `--reload` flag
- **Frontend**: Vite development server with HMR

### Debugging

#### Frontend Debugging
- Open browser DevTools
- Check Network tab for API requests
- Check Console for errors

#### Backend Debugging
- Backend logs appear in terminal
- API documentation: http://localhost:8000/docs
- Health check: http://localhost:8000/api/v1/status/health

### Common Issues

#### CORS Errors
- Backend CORS is configured to allow all origins
- If issues persist, check proxy configuration

#### API Connection Failed
- Ensure backend is running on port 8000
- Check firewall settings
- Verify proxy configuration in Vite

#### Build Issues
```bash
# Clean and reinstall
cd web
rm -rf node_modules package-lock.json
npm install
```

## Production Deployment

### Docker Production
The production Dockerfile includes nginx configuration that:

- Serves the frontend on port 80
- Proxies API requests to the backend
- Handles SSE connections properly

### Manual Deployment
```bash
# Build frontend
cd web
npm run build

# Serve with nginx or similar
# Configure nginx to proxy /api to backend
```

## Troubleshooting

### Backend Not Starting
```bash
# Check if port 8000 is available
lsof -i :8000

# Check Python environment
source venv/bin/activate
python -c "import uvicorn; print('uvicorn available')"
```

### Frontend Not Starting
```bash
# Check Node.js version (requires 18+)
node --version

# Check if port 3000 is available
lsof -i :3000

# Reinstall dependencies
cd web
rm -rf node_modules package-lock.json
npm install
```

### API Requests Failing
```bash
# Test backend directly
curl http://localhost:8000/api/v1/status/health

# Test through proxy
curl http://localhost:3000/api/v1/status/health

# Check browser network tab for specific errors
```

## Additional Resources

- [API Documentation](../API.md)
- [Backend Setup](../README.md)
- [Docker Configuration](../INFRASTRUCTURE.md)
