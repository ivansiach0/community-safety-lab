# Repository guidance

Work in a dedicated worktree and keep `main` as the protected integration branch. Write source,
tests, documentation, branch names, and commit messages in English.

## Boundaries

- `apps/web` owns the Next.js user interface.
- `apps/api` owns the Flask HTTP API.
- Read `docs/adr/` before changing platform choices or application boundaries.
- Introduce domain modules, infrastructure, or dependencies only after their scope and tradeoffs
  have been explicitly approved.

## Workflow

- Use pnpm for JavaScript and uv for Python; manifests and lockfiles are the version authority.
- Use the scripts in `package.json` and the commands in `README.md` for local verification.
- Test behavior through public seams. Keep each change inside the approved feature or bootstrap scope.
- Finish with formatting, linting, type checking, tests, builds, and `git diff --check`.
