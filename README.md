# Community Safety Lab

Community Safety Lab is a monorepo for a community-safety web application. It contains a Next.js
frontend, a Flask API, and a PostgreSQL-backed anonymous report-submission module.

## Repository layout

- `apps/web`: Next.js App Router frontend.
- `apps/api`: Flask API using an application factory.
- `docs/adr`: durable architectural decisions.
- `compose.yaml`: local PostgreSQL service.

## Prerequisites

- Node.js 24.21.0
- pnpm 12.10.1
- Python 3.14.7
- uv 0.12.23
- Docker with Compose support

## Install

```sh
pnpm install --frozen-lockfile
uv sync --project apps/api --frozen
```

## Run locally

Start PostgreSQL and apply the migrations:

```sh
docker compose up -d postgres
DATABASE_URL=postgresql+psycopg://community_safety:community_safety_local@127.0.0.1:5433/community_safety \
  uv run --project apps/api alembic -c apps/api/alembic.ini upgrade head
```

Start the API with the same database URL:

```sh
DATABASE_URL=postgresql+psycopg://community_safety:community_safety_local@127.0.0.1:5433/community_safety \
  uv run --project apps/api flask --app community_safety_api:create_app run
```

Start the web application:

```sh
COMMUNITY_SAFETY_API_URL=http://127.0.0.1:5000 \
  pnpm --filter @community-safety-lab/web dev
```

The report form is available at `http://localhost:3000/reports/new`. The API exposes `POST /reports`
and the health seam at `GET /health`.

## Verify

```sh
pnpm exec prettier . --check
pnpm --filter @community-safety-lab/web lint
pnpm --filter @community-safety-lab/web typecheck
pnpm --filter @community-safety-lab/web test
pnpm --filter @community-safety-lab/web build

uv run --project apps/api ruff format --check apps/api/src apps/api/tests apps/api/migrations
uv run --project apps/api ruff check apps/api/src apps/api/tests apps/api/migrations
uv run --project apps/api mypy apps/api/src
COMMUNITY_SAFETY_TEST_DATABASE_URL=postgresql+psycopg://community_safety:community_safety_local@127.0.0.1:5433/community_safety \
  uv run --project apps/api pytest apps/api/tests
uv build --project apps/api
```

## Baseline exclusions

This project does not yet include authentication, a component library, Storybook, Tailwind CSS,
end-to-end tests, CI/CD, or hosting.
