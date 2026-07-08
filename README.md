# Enterprise AI Knowledge Platform

> A production-ready platform that lets organizations upload documents and ask natural language questions — powered by RAG (Retrieval-Augmented Generation).

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 18, Vite, Tailwind CSS, Axios, React Router |
| Backend | FastAPI, SQLAlchemy, Alembic, PostgreSQL |
| AI | SentenceTransformers, Qdrant, OpenAI API |
| Cache | Redis |
| Deployment | Docker, Docker Compose, Nginx |

---

## Quick Start

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running
- [Python 3.12+](https://www.python.org/downloads/)
- [Node.js 20+](https://nodejs.org/)
- [Git](https://git-scm.com/)

### 1. Clone the repository

```bash
git clone https://github.com/PrathameshPatil3531/Enterprise-AI-Knowledge-Platform.git
cd Enterprise-AI-Knowledge-Platform
```

### 2. Configure environment variables

```bash
cp .env.example .env
```

Open `.env` and set at minimum:
```
SECRET_KEY=<generate with: python -c "import secrets; print(secrets.token_hex(32))">
OPENAI_API_KEY=sk-your-key-here
```

### 3. Start infrastructure services (PostgreSQL + Redis + Qdrant)

```bash
docker compose up -d postgres redis qdrant
```

Wait for all services to be healthy:
```bash
docker compose ps
```

### 4. Start the backend

```bash
cd backend

# Create and activate virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1        # Windows PowerShell
# source venv/bin/activate          # macOS / Linux

# Install dependencies
pip install -r requirements.txt

# Create .env for local development (use localhost instead of Docker service names)
cp .env.example .env
# Edit DATABASE_URL and REDIS_URL to use localhost

# Start FastAPI
uvicorn app.main:app --reload --port 8000
```

API available at: http://localhost:8000
Swagger UI at: http://localhost:8000/api/docs

### 5. Start the frontend

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

Frontend available at: http://localhost:5173

---

## Start Everything with Docker Compose

```bash
# Start all services (infrastructure + backend)
docker compose up -d

# View logs
docker compose logs -f

# Stop everything
docker compose down
```

---

## Project Structure

```
Enterprise-AI-Knowledge-Platform/
├── backend/                  # FastAPI application
│   ├── app/
│   │   ├── api/v1/           # Route handlers (thin controllers)
│   │   ├── core/             # Config, logging, exceptions, security
│   │   ├── db/               # Database engine and session
│   │   ├── models/           # SQLAlchemy ORM models
│   │   ├── schemas/          # Pydantic request/response DTOs
│   │   ├── services/         # Business logic
│   │   ├── repositories/     # Database queries
│   │   ├── ai/               # ML pipeline (embedding, RAG, LLM)
│   │   ├── middleware/        # Logging, rate limiting
│   │   └── main.py           # FastAPI app factory
│   ├── alembic/              # Database migrations
│   ├── tests/                # Unit and integration tests
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/                 # React + Vite SPA
│   ├── src/
│   │   ├── api/              # Axios API client
│   │   ├── components/       # Reusable UI components
│   │   ├── pages/            # Page-level components
│   │   ├── store/            # Global state
│   │   ├── hooks/            # Custom React hooks
│   │   └── router/           # React Router configuration
│   └── Dockerfile
├── docker/                   # Infrastructure config
│   ├── nginx/nginx.conf
│   └── postgres/init.sql
├── docker-compose.yml
├── docker-compose.dev.yml
└── .env.example
```

---

## Database Migrations (Alembic)

```bash
cd backend

# Generate a new migration after changing a model
alembic revision --autogenerate -m "add users table"

# Apply all pending migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# View migration history
alembic history

# Check current DB version
alembic current
```

---

## API Endpoints

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/health` | ❌ | System health check |
| GET | `/api/v1/health` | ❌ | API v1 health check |
| POST | `/api/v1/auth/register` | ❌ | Register new user |
| POST | `/api/v1/auth/login` | ❌ | Login, receive tokens |
| POST | `/api/v1/auth/refresh` | ❌ | Refresh access token |
| GET | `/api/v1/auth/me` | ✅ | Get current user |
| POST | `/api/v1/documents/upload` | ✅ | Upload document |
| GET | `/api/v1/documents` | ✅ | List documents |
| POST | `/api/v1/chats/{id}/query` | ✅ | Ask a question (RAG) |

Full API docs: http://localhost:8000/api/docs (development only)

---

## Environment Variables

See [`.env.example`](.env.example) for all required variables.

| Variable | Required | Description |
|---|---|---|
| `SECRET_KEY` | ✅ | JWT signing key (min 32 chars) |
| `DATABASE_URL` | ✅ | PostgreSQL connection string |
| `REDIS_URL` | ✅ | Redis connection string |
| `OPENAI_API_KEY` | ✅ | OpenAI API key for LLM |
| `ALLOWED_ORIGINS` | ✅ | Comma-separated CORS origins |

---

## Development Milestones

- [x] **Milestone 0** — System Design & Architecture
- [x] **Milestone 1** — Development Environment & Infrastructure
- [ ] **Milestone 2** — Authentication (JWT, RBAC, Refresh Tokens)
- [ ] **Milestone 3** — Document Management (Upload, Parse, Chunk)
- [ ] **Milestone 4** — AI Pipeline (Embeddings, RAG, LLM)
- [ ] **Milestone 5** — Frontend (React UI, Chat Interface)
- [ ] **Milestone 6** — Production (Docker, CI/CD, Monitoring)

---

## License

MIT License — see [LICENSE](LICENSE) for details.