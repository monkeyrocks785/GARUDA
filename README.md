# GARUDA

**AI-powered Geospatial Intelligence and Monitoring Platform**

GARUDA is a production-ready platform designed for satellite imagery analysis, GIS operations, AI/ML model integration, remote sensing, time-series forecasting, and geospatial dashboards.

## Tech Stack

### Backend
- Python 3.12+
- FastAPI
- SQLAlchemy + Alembic
- SQLite
- Loguru (logging)
- Pydantic (validation)

### Frontend
- React 18
- TypeScript
- Vite
- TailwindCSS
- React Router
- Zustand (state)
- TanStack Query (data fetching)

## Installation

### Prerequisites
- Python 3.12+
- Node.js 18+
- npm or yarn

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
venv\Scripts\activate     # Windows
# source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -e ".[dev]"

# Copy environment variables
copy ..\.env.example ..\.env

# Run database migrations
python migrate.py

# Start development server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

The frontend will be available at `http://localhost:5173` and will proxy API requests to the backend at `http://localhost:8000`.

## API Documentation

Once the backend is running:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- OpenAPI Schema: http://localhost:8000/openapi.json

## Folder Structure

```
GARUDA/
├── backend/                    # Python FastAPI backend
│   ├── api/v1/                 # API endpoint definitions
│   ├── core/                   # Core utilities (logging, etc.)
│   ├── config/                 # Configuration management
│   ├── database/               # Database connection & setup
│   ├── models/                 # SQLAlchemy models
│   ├── repositories/           # Data access layer
│   ├── services/               # Business logic layer
│   ├── workers/                # Background workers
│   ├── scheduler/              # Task scheduling
│   ├── storage/                # File storage utilities
│   ├── geo/                    # Geospatial processing (future)
│   ├── ai/                     # AI/ML integration (future)
│   ├── reports/                # Report generation (future)
│   ├── utils/                  # Shared utilities
│   ├── tests/                  # Test suite
│   ├── migrations/             # Alembic migrations
│   └── main.py                 # Application entry point
├── frontend/                   # React TypeScript frontend
│   └── src/
│       ├── components/         # Reusable UI components
│       ├── pages/              # Page components
│       ├── layouts/            # Layout components
│       ├── hooks/              # Custom React hooks
│       ├── services/           # API service layer
│       ├── store/              # Zustand state stores
│       ├── types/              # TypeScript type definitions
│       ├── utils/              # Utility functions
│       └── styles/             # Global styles
├── storage/                    # Persistent storage
│   ├── projects/               # Project data
│   ├── cache/                  # Cache files
│   ├── models/                 # ML model storage
│   ├── temp/                   # Temporary files
│   ├── exports/                # Exported files
│   └── logs/                   # Application logs
├── config/                     # Shared configuration
├── scripts/                    # Utility scripts
├── docker/                     # Docker configurations (future)
├── docs/                       # Documentation
├── .github/                    # GitHub workflows (future)
├── pyproject.toml              # Python project config
└── README.md
```

## Development Guidelines

### Code Style
- **Backend**: Black formatter, isort, Ruff linter, mypy type checking
- **Frontend**: ESLint with TypeScript rules

### Running Code Quality Tools

```bash
# Backend
cd backend
black .
isort .
ruff check .
mypy .

# Frontend
cd frontend
npm run lint
```

### Architecture Principles
- Clean Architecture with clear separation of concerns
- Repository pattern for data access
- Service layer for business logic
- Dependency injection throughout
- No circular dependencies

### Configuration
- All settings via environment variables
- `.env` file for local development
- Pydantic validation for all config values

## Testing

```bash
# Backend tests
cd backend
pytest

# With coverage
pytest --cov=. --cov-report=html
```

## Logging

Logs are written to `storage/logs/`:
- `backend.log` - General application logs
- `errors.log` - Error-only logs
- `worker.log` - Background worker logs

## License

MIT
