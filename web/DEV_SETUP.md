# Development Setup Guide

## Quick Start

### Option 1: Using the dev script (Recommended)
```bash
# From the project root directory
./scripts/dev.sh
```

This script will:
- Set up Python virtual environment
- Install dependencies
- Start backend on port 8000
- Start frontend on port 3000
- Configure proxy automatically

### Option 2: Manual setup

#### 1. Start Backend
```bash
# From project root
source venv/bin/activate  # On Windows: venv\Scripts\activate
PYTHONPATH=. uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
```

#### 2. Start Frontend
```bash
# From web directory
cd web
npm install
npm run dev
```

## Configuration

### Environment Variables
The frontend uses these environment variables:
- `VITE_API_URL`: Backend API URL (defaults to http://localhost:8000)
- `VITE_DEV_MODE`: Development mode flag
- `VITE_LOG_LEVEL`: Logging level

### Vite Proxy
The frontend proxies `/api` requests to the backend:
- Target: http://localhost:8000
- Port: 3000 (frontend)
- Backend: 8000

## Troubleshooting

### Common Issues

1. **Backend won't start**
   - Ensure you're in the project root directory
   - Check if `pyproject.toml` exists
   - Verify Python virtual environment is activated

2. **Frontend can't connect to backend**
   - Check if backend is running on port 8000
   - Verify Vite proxy configuration
   - Check browser console for errors

3. **Module import errors**
   - Ensure all `__init__.py` files exist
   - Check PYTHONPATH is set correctly
   - Run from project root directory

### Ports
- Frontend: 3000
- Backend: 8000
- Make sure these ports are available

## Development Workflow

1. Start backend first
2. Start frontend
3. Check browser console for errors
4. Use browser dev tools for debugging
5. Check terminal logs for both services
