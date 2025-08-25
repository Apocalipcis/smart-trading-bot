# Trading Bot Web Interface

A modern React-based web interface for the Smart Trading Bot, built with TypeScript, Tailwind CSS, and Vite.

## Features

- **Dashboard**: Real-time trading pairs management, live signals, and trading controls
- **Backtests**: Create and manage backtest configurations with detailed results
- **Settings**: Configure trading parameters, risk management, and notifications
- **Dark Mode**: Toggle between light and dark themes
- **Responsive Design**: Works on desktop and mobile devices
- **Real-time Updates**: Live signal streaming via Server-Sent Events

## Development

### Prerequisites

- Node.js 18+ 
- npm or yarn

### Installation

```bash
cd web
npm install
```

### Development Server

```bash
npm run dev
```

The development server will start at `http://localhost:3000`

### Building for Production

```bash
npm run build
```

The built files will be in the `dist/` directory.

## API Integration

The web interface communicates with the FastAPI backend through:

- **REST API**: For CRUD operations on pairs, backtests, settings, etc.
- **Server-Sent Events**: For real-time signal streaming
- **WebSocket**: For live updates (if configured)

## Environment Variables

Create a `.env` file in the web directory:

```env
VITE_API_URL=http://localhost:8000
```

## Docker Integration

The web interface is automatically built and served by nginx in the Docker container. The FastAPI backend runs on port 8000, and nginx serves the web interface on port 80 while proxying API requests to the backend.

## Technologies Used

- **React 18** with TypeScript
- **React Router** for navigation
- **Tailwind CSS** for styling
- **Lucide React** for icons
- **Axios** for HTTP requests
- **Vite** for build tooling

## Project Structure

```
web/
├── src/
│   ├── components/     # React components
│   ├── services/       # API client and services
│   ├── types/          # TypeScript type definitions
│   ├── App.tsx         # Main app component
│   └── main.tsx        # Entry point
├── public/             # Static assets
├── dist/               # Built files (generated)
└── package.json        # Dependencies and scripts
```

## Contributing

1. Follow the existing code style and patterns
2. Use TypeScript for all new code
3. Add proper error handling and loading states
4. Test the interface with different screen sizes
5. Ensure accessibility standards are met
