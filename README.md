# Community Safety Lab

Community Safety Lab is a monorepo for a community-safety web application. The baseline contains a
Next.js frontend and a Flask API while deliberately leaving product features and infrastructure for
later, explicit decisions.

## Repository layout

- `apps/web`: Next.js App Router frontend.
- `apps/api`: Flask API using an application factory.
- `docs/adr`: durable architectural decisions.

## Prerequisites

- Node.js 24.21.0
- pnpm 12.10.1
- Python 3.14.7
- uv 0.12.23

## Install

```sh
pnpm install --frozen-lockfile
uv sync --project apps/api --frozen
```

## Run locally

Start the web application:

```sh
pnpm --filter @community-safety-lab/web dev
```

Start the API:

```sh
uv run --project apps/api flask --app community_safety_api:create_app run
```

The API health seam is available at `GET /health`.

## Verify

```sh
pnpm exec prettier . --check
pnpm --filter @community-safety-lab/web lint
pnpm --filter @community-safety-lab/web typecheck
pnpm --filter @community-safety-lab/web test
pnpm --filter @community-safety-lab/web build

uv run --project apps/api ruff format --check apps/api/src apps/api/tests
uv run --project apps/api ruff check apps/api/src apps/api/tests
uv run --project apps/api mypy apps/api/src
uv run --project apps/api pytest apps/api/tests
uv build --project apps/api
```

## Baseline exclusions

This baseline does not include domain modules, persistence, authentication, a component library,
Storybook, Tailwind CSS, end-to-end tests, CI/CD, hosting, or remote repository configuration.
