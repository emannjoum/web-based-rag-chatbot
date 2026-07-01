# MedAtlas UI

React frontend for the MedAtlas medical RAG chatbot. The UI talks to the FastAPI backend in `../backend`.

## Requirements

- Node.js 22+
- npm
- Running backend API (local Python process or Docker Compose)

## Quick start (development)

Start the backend first (from repository root):

```bash
cp .env.example .env
cd backend
pip install -e .
python -m chatbot.presentation.api.main
```

Backend: http://127.0.0.1:8000  
API docs: http://127.0.0.1:8000/api/docs

Then start the frontend:

```bash
cd frontend
cp .env.example .env
npm install
npm run dev
```

UI: http://localhost:5173

In development, Vite proxies `/api` and `/health` to `http://127.0.0.1:8000`, so `VITE_API_BASE_URL` can remain empty.

## Configuration

| Variable | Description |
|----------|-------------|
| `VITE_API_BASE_URL` | Base URL for API requests. Leave empty when using the Vite dev proxy or the nginx proxy in Docker. Set only when the API is hosted on a different origin. |

## npm scripts

| Command | Description |
|---------|-------------|
| `npm run dev` | Start Vite dev server on port 5173 |
| `npm run build` | Typecheck and build production assets to `dist/` |
| `npm run preview` | Serve the production build locally |

## Authentication

Most API routes require a JWT.

1. User registers or logs in through the auth modal.
2. The access token is stored in `localStorage` under `medatlas_access_token`.
3. `src/api/client.ts` sends `Authorization: Bearer <token>` on protected requests.

Auth endpoints:

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/auth/register` | Create account |
| POST | `/api/v1/auth/login` | Sign in |
| GET | `/api/v1/auth/me` | Current user (requires token) |

Chat and session endpoints also require authentication.

## API endpoints used by the UI

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| GET | `/api/v1/config` | Available models and search methods |
| GET | `/api/v1/sessions` | List chat sessions |
| GET | `/api/v1/sessions/{id}` | Load one session |
| DELETE | `/api/v1/sessions/{id}` | Delete one session |
| DELETE | `/api/v1/sessions` | Delete all sessions |
| POST | `/api/v1/chat/completions` | Send a text message |
| POST | `/api/v1/chat/image` | Upload a medical image |

## Project layout

```
frontend/
  src/
    api/client.ts              HTTP client and auth header handling
    hooks/
      useAuth.ts               Login, register, logout, token restore
      useChat.ts               Messages, sessions, send/upload
      useGroupedHistory.ts     Sidebar date grouping
    components/
      MedicalChatbot.tsx       Main application shell
      AuthModal.tsx            Login and registration form
      Sidebar.tsx              Session history
      ChatArea.tsx             Message list
      ChatInput.tsx            Text and image input
      AssistantMessage.tsx     Rendered assistant replies
      FaithfulnessCard.tsx     RAGAS source-alignment scores
    types/api.ts               Shared TypeScript types
  vite.config.ts               Dev server and API proxy
  nginx.conf                   Production reverse proxy
  Dockerfile                   Multi-stage build (Node -> nginx)
```

## Docker

From the repository root:

```bash
cp .env.example .env
docker compose up --build
```

Services:

| Service | URL |
|---------|-----|
| Frontend | http://localhost:5173 |
| Backend API | http://localhost:8000 |
| API docs | http://localhost:8000/api/docs |

The frontend container serves static files with nginx and proxies `/api` and `/health` to the `backend` service.

## Production build (without Docker)

```bash
cd frontend
npm ci
npm run build
```

Output is written to `frontend/dist/`. Serve those files with any static file server, or run the frontend Docker image.

## Stack

- React 19
- TypeScript
- Vite 6
- Tailwind CSS 4
- react-markdown

## Related documentation

Project-wide setup, architecture, and environment variables are documented in [../README.md](../README.md).
