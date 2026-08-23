# Blueprint UC Web

The web application provides the Blueprint UC generator and UML use-case diagram editor. It is a React and TypeScript single-page application built with Vite.

## Features

- Describe a system and generate a UML use-case diagram through the server API.
- Answer optional AI clarification questions.
- Edit actors, use cases, system boundaries, and relations on a Konva canvas.
- Automatically save projects to the server.
- Import and export diagram XML, SVG, and PNG.

All AI requests go through the server. The browser never communicates with an AI provider directly.

## Prerequisites

- Node.js 24 and npm for local development
- Docker Desktop with Docker Compose for containerized use

## Run with Docker Compose

Start the server stack first. It creates the shared Docker network and makes the API available to this container.

```bash
cd ../server
docker compose up --build --detach

cd ../web
docker compose up --build --detach
```

Open `http://localhost:8080`.

The web container is named `blueprint-uc-web` and uses the image `blueprint-uc-web:latest`.

## Local development

Install dependencies and start Vite:

```bash
npm ci
npm run dev
```

By default, the application sends API requests to `http://localhost:8000`. Override this with `VITE_API_URL` when needed:

```bash
VITE_API_URL=http://localhost:8000 npm run dev
```

## Commands

```bash
# Build the production application
npm run build

# Check formatting
npm run format:check

# Apply formatting
npm run format

# Stop the web container
docker compose down
```

## Architecture

| Path | Purpose |
| --- | --- |
| `src/api` | HTTP client and API operations |
| `src/components` | Reusable UI and editor components |
| `src/hooks` | Generation, project, and diagram interactions |
| `src/lib` | XML, export, layout, and browser utilities |
| `src/pages` | Route-level page composition |
| `src/store` | Zustand editor state |
| `src/styles` | Global styles and design tokens |

## Docker details

The production image builds the Vite application and serves it with Nginx on port `8080`. Nginx also proxies `/api/*` requests to the API container, which gives the browser one same-origin endpoint and supports server-sent events.
