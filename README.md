# AskRepo

**Ask your codebase anything.**

AI-powered codebase intelligence — understand any repository in minutes.

---

## Architecture

```
                        ASKREPO
                           │
                           ▼
                   React Frontend        ← Vite + TypeScript + Tailwind
                           │
                           ▼
                      FastAPI API         ← Python + Pydantic + Uvicorn
                           │
          ┌────────────────┼────────────────┐
          │                │                │
          ▼                ▼                ▼
     Repository        Analysis         AI Gateway
      Service           Engine           (Phase 3+)
          │                │
          ▼                ▼
      GitPython      Tree-sitter (Phase 2+)
                          │
               ┌──────────┴──────────┐
               │                     │
               ▼                     ▼
         Vector Index          Dependency Graph
         FAISS (Phase 3)       NetworkX (Phase 4)
```

## Quick Start

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and Docker Compose
- Or: Python 3.12+, Node 20+, PostgreSQL 16+

### Option 1 — Docker (recommended)

```bash
# 1. Copy environment config
cp .env.example .env

# 2. Start all services
docker-compose up --build

# 3. Open the app
#    Frontend → http://localhost:5173
#    Backend  → http://localhost:8000
#    API docs → http://localhost:8000/docs
```

### Option 2 — Manual

```bash
# 1. Copy environment config
cp .env.example .env

# 2. Start PostgreSQL (ensure it's running on port 5432)

# 3. Backend
cd backend
python -m venv venv
source venv/bin/activate   # or venv\Scripts\activate on Windows
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# 4. Frontend
cd frontend
npm install
npm run dev
```

## Environment Variables

See [`.env.example`](.env.example) for all configuration options.

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `postgresql+asyncpg://postgres:postgres@localhost:5432/askrepo` | PostgreSQL connection |
| `GITHUB_TOKEN` | — | Optional GitHub token for higher API rate limits |
| `MAX_REPOSITORY_SIZE_MB` | `50` | Max repository size to clone/extract |
| `MAX_FILE_COUNT` | `2000` | Max files to process per repository |
| `MAX_FILE_SIZE_MB` | `1` | Max individual file size |
| `MAX_ANALYSES_PER_DAY` | `3` | Analysis limit per day |
| `MAX_AI_REQUESTS_PER_DAY` | `20` | AI question limit per day |
| `TEMP_REPOSITORY_PATH` | `./tmp/repos` | Temp storage for cloned/extracted repos |
| `DEBUG` | `false` | Enable debug mode |

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Health check |
| `POST` | `/api/repositories` | Create repository (URL or ZIP upload) |
| `GET` | `/api/repositories/{id}` | Get repository metadata |
| `GET` | `/api/repositories/{id}/files` | List repository files |
| `GET` | `/api/repositories/{id}/stats` | Get repository statistics |
| `GET` | `/api/analyses/{id}` | Get analysis details |
| `GET` | `/api/analyses/{id}/status` | Poll analysis status |

## Project Structure

```
askrepo/
├── frontend/           ← React + TypeScript + Vite
│   ├── src/
│   │   ├── components/ ← Reusable UI components
│   │   ├── pages/      ← Route pages
│   │   ├── hooks/      ← Custom React hooks
│   │   ├── services/   ← API client
│   │   ├── types/      ← TypeScript types
│   │   └── utils/      ← Utility functions
│   └── package.json
│
├── backend/            ← Python + FastAPI
│   ├── app/
│   │   ├── api/        ← API endpoints
│   │   ├── core/       ← Config, DB, security
│   │   ├── models/     ← SQLAlchemy models
│   │   ├── schemas/    ← Pydantic schemas
│   │   └── services/   ← Business logic
│   │       └── repository/
│   ├── tests/
│   └── requirements.txt
│
├── docker-compose.yml
├── .env.example
└── README.md
```

## Development Phases

- [x] **Phase 1** — Foundation (repo input, scanning, basic dashboard)
- [ ] **Phase 2** — Code Intelligence (Tree-sitter, AST, symbols)
- [ ] **Phase 3** — RAG (embeddings, FAISS, AI chat)
- [ ] **Phase 4** — Architecture (NetworkX, React Flow)
- [ ] **Phase 5** — Git Archaeology (commit history, diffs)
- [ ] **Phase 6** — Multi-Agent (specialized reasoning agents)
- [ ] **Phase 7** — Production Hardening (auth, rate limiting, deployment)

## License

MIT
