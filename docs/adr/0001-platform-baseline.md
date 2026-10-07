# Use a pnpm and uv monorepo with Next.js and Flask

Community Safety Lab will keep its Next.js 16.3.8 frontend and Flask 3.1.3 API in one repository,
managed independently by pnpm 12.10.1 on Node.js 24.21.0 and uv 0.12.23 on Python 3.14.7. This
keeps cross-application changes reviewable together while preserving clear runtime boundaries; the
tradeoff is coordinating two toolchains and lockfiles. Flask uses an application factory so runtime
configuration remains outside module import, and dependency versions are pinned in manifests and
lockfiles. Persistence, authentication, UI primitives, end-to-end testing, delivery, and hosting are
deferred until their requirements are known.
