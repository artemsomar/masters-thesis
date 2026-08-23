# Blueprint UC

Blueprint UC generates and edits UML use-case diagrams from natural-language system descriptions. The application is split into a React web client and a FastAPI server with Redis-backed background jobs.

## Repository layout

| Directory | Purpose |
| --- | --- |
| [web](web/) | React editor, generator flow, diagram export, and browser UI |
| [server](server/) | REST API, AI generation workflow, Redis persistence, and RQ worker |

## Run with Docker Compose

### 1. Configure the server

Create `server/.env` from the example and set a real Gemini API key. Do not commit this file.

```bash
cd server
cp .env.example .env
```

At minimum, replace `GEMINI_API_KEY` and `APP_SESSION_TOKEN_PEPPER`. The selected AI models are configured with `APP_GEMINI_MODEL` and `APP_GEMINI_EMBEDDING_MODEL`.

### 2. Start the server stack

```bash
cd server
docker compose up --build --detach
```

This starts Redis, the API, and the background worker. The API is available at `http://localhost:8000`, and its readiness endpoint is `http://localhost:8000/ready`.

### 3. Start the web app

```bash
cd web
docker compose up --build --detach
```

Open `http://localhost:8080`.

The web Compose project uses the Docker network created by the server Compose project, so the server stack must be started first.

## Stop the application

Run these commands from their respective directories:

```bash
docker compose down
```

Stopping the server stack also removes the shared Docker network. Stop the web stack first when shutting down both parts.

## Additional documentation

- [Web README](web/README.md)
- [Server README](server/README.md)
- [Product and implementation documentation](web/docs/)
