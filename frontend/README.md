# Altibbi Medical Chatbot — React UI

Standalone React frontend wired to the FastAPI backend.

## Development

Run the API and frontend in separate terminals.

### 1. Backend API

```bash
# from repository root
cp .env.example .env
pip install -e .
PYTHONPATH=src python -m chatbot.presentation.api.main
```

API: `http://127.0.0.1:8000`  
Docs: `http://127.0.0.1:8000/api/docs`

### 2. Frontend

```bash
cd frontend
cp .env.example .env
npm install
npm run dev
```

UI: `http://localhost:5173`

Vite proxies `/api` and `/health` to the backend, so `VITE_API_BASE_URL` can stay empty in development.

## Production

### Docker Compose

```bash
cp .env.example .env
# fill in API keys
docker compose up --build
```

Serves the built React app and API on port `8000`.

### Manual production build

```bash
cd frontend && npm ci && npm run build
cd ..
FRONTEND_DIST_PATH=frontend/dist PYTHONPATH=src python -m chatbot.presentation.api.main
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| GET | `/api/v1/config` | Models and search methods |
| GET | `/api/v1/sessions` | Chat history |
| GET | `/api/v1/sessions/{id}` | Session messages |
| DELETE | `/api/v1/sessions/{id}` | Delete one session |
| DELETE | `/api/v1/sessions` | Delete all sessions |
| POST | `/api/v1/chat/completions` | Send a text message |
| POST | `/api/v1/chat/image` | Upload medical image |

## Frontend structure

```
frontend/src/
  api/client.ts          # Typed API client
  hooks/useChat.ts       # Chat state + backend integration
  hooks/useGroupedHistory.ts
  components/            # UI components
  types/api.ts           # Shared types
```
