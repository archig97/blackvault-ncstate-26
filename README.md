## Getting Started

The repository is split into a Python FastAPI backend (`backend/`) and one or more
Next.js frontends (`frontend/`, and an experimental copy under
`frontend/frontend/`). The backend talks to Valkey/Redis for graph data, while
the frontend renders the neighborhood graph with React Flow.

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) with Docker Compose
- Node.js 18+ and npm 9+ (Next.js 16 requires Node 18.17 or newer)

## Run the backend with Docker Compose

```bash
docker compose up --build
```

This starts two containers:

- `valkey` on port `6379`
- `backend` (FastAPI) on port `8000`, running `uvicorn app.main:app`

The first run builds the backend image using `backend/Dockerfile` and installs
requirements from `backend/requirements.txt`. Stop everything with
`Ctrl+C`, or add `-d` to run detached.

## Run a frontend locally with npm

1. Install dependencies (first run only):

   ```bash
   cd frontend
   npm install
   ```

2. Start the dev server and point it at the Docker backend:

   ```bash
   NEXT_PUBLIC_API_BASE=http://localhost:8000 npm run dev
   ```

   The app runs on [http://localhost:3000](http://localhost:3000). The graph
   component automatically falls back to `http://localhost:8000` if the env var
   is missing, but setting `NEXT_PUBLIC_API_BASE` keeps things explicit.

3. (Optional) When you need a production build:

   ```bash
   npm run build
   npm run start
   ```

The nested `frontend/frontend` project uses the same commands; just `cd` into
that directory instead if you are working there.

## Useful npm scripts

- `npm run dev` – Next.js dev server with hot reload
- `npm run build` – Production build
- `npm run start` – Run the built app
- `npm run lint` – ESLint checks (fix issues before pushing)

## Pushing your changes

The root `.gitignore` already excludes `node_modules`, `.next`, and other
generated artifacts, so commit only the source files under `backend/`,
`frontend/`, and related configs before pushing.
