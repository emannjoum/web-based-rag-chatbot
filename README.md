# MedAtlas

Medical RAG chatbot that answers health questions using retrieved context from trusted sources (primarily for now from Altibbi), with citations and optional source-alignment scoring (RAGAS).

The repository contains a FastAPI backend, a React frontend, and Docker Compose configuration for local development and deployment.

## Repository layout

```
.
├── backend/                 Python API and RAG pipeline
│   ├── src/chatbot/         Application source (package name: chatbot)
│   ├── alembic/             MySQL schema migrations
│   ├── Dockerfile
│   └── pyproject.toml
├── frontend/                React UI (see frontend/README.md)
├── docker-compose.yml       MongoDB, Redis, MySQL, backend, frontend
└── .env.example             Environment variable template
```

## Architecture

### Services (Docker Compose)

| Service  | Port (host) | Purpose                          |
|----------|-------------|----------------------------------|
| frontend | 5173        | React app (nginx)                |
| backend  | 8000        | FastAPI API                      |
| mongo    | 27017       | Chat message persistence         |
| redis    | 6379        | Session list / message cache     |
| mysql    | 3307        | User accounts (maps to 3306 in container) |

### Data stores

| Data              | Store   | Notes                                      |
|-------------------|---------|--------------------------------------------|
| User accounts     | MySQL   | Email, password hash, display name         |
| Chat sessions     | MongoDB | Messages scoped by `user_id`               |
| Recent history    | Redis   | Cache only; MongoDB is source of truth     |

User records live in MySQL. Chat history lives in MongoDB. Each chat document includes a `user_id` linking it to the authenticated user.

### Backend layers

The Python code under `backend/src/chatbot/` follows a layered layout:

| Layer          | Path              | Responsibility                          |
|----------------|-------------------|-----------------------------------------|
| Presentation   | `presentation/`   | FastAPI routes, request/response schemas |
| Application    | `application/`    | Use cases (chat, sessions, auth)        |
| Domain         | `domain/`         | RAG pipeline, prompts, business rules   |
| Infrastructure | `infrastructure/` | Mongo, MySQL, Redis, LLM, search, RAGAS |

A typical chat request flows: frontend -> `chat_router` -> `ChatService` -> `RAGPipeline` (search + LLM) -> MongoDB persistence -> optional async RAGAS evaluation.

## Requirements

- Docker and Docker Compose (recommended), or:
- Python 3.10+
- Node.js 22+ and npm
- MongoDB, Redis, and MySQL running locally

## Quick start (Docker)

```bash
cp .env.example .env
# Add API keys (OPENAI_API_KEY, SERPER_API_KEY, etc.)
docker compose up --build
```

| URL            | Description        |
|----------------|--------------------|
| http://localhost:5173 | Web UI      |
| http://localhost:8000 | Backend API |
| http://localhost:8000/api/docs | OpenAPI docs |

The backend entrypoint waits for MySQL, runs Alembic migrations, then starts the API. Data persists in Docker volumes (`mongo_data`, `mysql_data`, `redis_data`) until removed with `docker compose down -v`.

## Local development (without Docker)

### 1. Environment

```bash
cp .env.example .env
```

Edit `.env` with your API keys and database URLs. For local MySQL on the default port, use `localhost:3306`. When using Docker for databases only:

```bash
docker compose up mongo redis mysql
```

Point `.env` at `localhost` for MongoDB and Redis, and `localhost:3307` for MySQL (host port mapped from the container).

### 2. Backend

```bash
cd backend
pip install -e .
python -m chatbot.presentation.api.main
```

Apply MySQL migrations if not using the Docker entrypoint:

```bash
cd backend
alembic upgrade head
```

### 3. Frontend

```bash
cd frontend
cp .env.example .env
npm install
npm run dev
```

See [frontend/README.md](frontend/README.md) for UI-specific setup, auth flow, and project layout.

## Environment variables

Copy `.env.example` to `.env` at the repository root. Key variables:

| Variable | Description |
|----------|-------------|
| `OPENAI_API_KEY` | OpenAI API key (chat and RAGAS evaluation) |
| `GEMINI_API_KEY` | Google Gemini API key (optional LLM provider) |
| `SERPER_API_KEY` | Serper web search |
| `TAVILY_API_KEY` | Tavily web search (optional) |
| `DEFAULT_SEARCH_METHOD` | Default search provider (e.g. `Serper`) |
| `MONGODB_URI` | MongoDB connection string |
| `REDIS_URL` | Redis connection string |
| `MYSQL_URL` | SQLAlchemy URL for user database |
| `JWT_SECRET_KEY` | Secret for signing JWT access tokens |
| `JWT_EXPIRE_MINUTES` | Token lifetime (default: 10080) |
| `CORS_ORIGINS` | Allowed frontend origins (comma-separated) |

Docker Compose overrides several URLs for in-network service hostnames (`mongo`, `redis`, `mysql`).

## API overview

Base path: `/api/v1`

| Area | Endpoints |
|------|-----------|
| Auth | `POST /auth/register`, `POST /auth/login`, `GET /auth/me` |
| Config | `GET /config` |
| Sessions | `GET /sessions`, `GET /sessions/{id}`, `DELETE /sessions/{id}`, `DELETE /sessions` |
| Chat | `POST /chat/completions`, `POST /chat/image` |

All session and chat routes require a valid JWT (`Authorization: Bearer <token>`). Interactive documentation: http://localhost:8000/api/docs

## Authentication

1. User registers or logs in via the frontend auth modal.
2. Backend stores credentials in MySQL and returns a JWT.
3. Frontend stores the token and sends it on subsequent requests.
4. Chat history in MongoDB is filtered by the authenticated user's ID.

Change `JWT_SECRET_KEY` before any production deployment.

## Database migrations

MySQL schema is managed with Alembic under `backend/alembic/`. Migrations run automatically when the backend container starts. To create a new migration locally:

```bash
cd backend
alembic revision --autogenerate -m "description"
alembic upgrade head
```

## Streamlit UI (optional)

A Streamlit interface is included for development and testing:

```bash
cd backend
pip install -e .
streamlit run src/chatbot/presentation/streamlit/app.py
```

The primary user-facing UI is the React app in `frontend/`.

## Production notes

- Set strong values for `JWT_SECRET_KEY` and database passwords.
- Provide LLM and search API keys in `.env`.
- The frontend Docker image builds static assets and serves them with nginx, proxying `/api` and `/health` to the backend service.
- RAGAS source-alignment scores run asynchronously; failures are logged but do not block chat responses.

