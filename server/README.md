# Blueprint UC Server

The server exposes the API used by Blueprint UC, runs AI-assisted use-case diagram generation, stores short-lived projects and sessions in Redis, and processes generation jobs with RQ.

## Services

| Service | Container | Responsibility |
| --- | --- | --- |
| API | `blueprint-uc-api` | FastAPI endpoints on port `8000` |
| Worker | `blueprint-uc-worker` | Runs queued clarification and diagram-generation jobs |
| Redis | `blueprint-uc-redis` | Session, project, queue, event, and rate-limit storage |

## Prerequisites

- Docker Desktop with Docker Compose
- A Gemini API key

## Configuration

Create a local `.env` file from the example:

```bash
cp .env.example .env
```

Set at least these values:

```dotenv
GEMINI_API_KEY=your-gemini-api-key
APP_SESSION_TOKEN_PEPPER=replace-with-a-long-random-secret
```

You can choose the AI models with `APP_GEMINI_MODEL` and `APP_GEMINI_EMBEDDING_MODEL`. Keep `.env` private; it is excluded from version control.

## Run with Docker Compose

```bash
docker compose up --build --detach
```

Endpoints:

- API: `http://localhost:8000`
- Readiness: `http://localhost:8000/ready`
- OpenAPI UI: `http://localhost:8000/docs`

The Compose project creates the shared `blueprint-uc` network. Start this stack before starting the web stack.

## Useful commands

```bash
# Follow API and worker logs
docker compose logs --follow api worker

# Inspect service state
docker compose ps

# Stop the stack
docker compose down
```

## Local development

Python 3.12 and Poetry 2 are required.

```bash
poetry install
poetry run uvicorn app.main:app --reload
```

Run the worker in a separate terminal:

```bash
poetry run python -m app.workers.runner
```

A Redis instance must be available at the address configured by `APP_REDIS_URL`.

## Project structure

| Path | Purpose |
| --- | --- |
| `src/app/api` | HTTP routes and request/response schemas |
| `src/app/modules` | Domain rules and application models |
| `src/app/workflows` | Generation and evaluation orchestration |
| `src/app/infrastructure` | Redis, RQ, Gemini, and other adapters |
| `src/app/workers` | Background-job entry point |
