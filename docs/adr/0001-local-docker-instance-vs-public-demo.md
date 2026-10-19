# 1. Run tests against a local Docker instance, not only the public demo

## Status

Accepted

## Context

OrangeHRM publishes a public demo site. Testing against it alone would mean less infrastructure to
build and maintain, but it carries real risks for a CI-driven test suite:

- **Shared data.** Anyone can edit or delete records, and the site resets on its own schedule, so tests
  that depend on existing data are inherently flaky.
- **Instability.** The demo is sometimes slow or unavailable, which would show up as flaky CI runs
  unrelated to the code under test.
- **A shared admin login.** Other users of the same demo could change the admin password or role at any
  time, breaking every test that depends on it.
- **Etiquette.** Parallel test runs and browser matrices put load on a server shared with everyone else
  using the demo.

## Decision

Run the primary test suite against a local, self-hosted OrangeHRM instance in Docker Compose
(`infra/docker-compose.orangehrm.yml`), seeded from a one-time database snapshot
(`infra/seed/orangehrm.sql`) so the container starts already installed — no interactive setup wizard,
no manual steps, and CI never races the app on startup (`infra/wait_for_ready.py` polls until the login
page actually renders).

The public demo is kept as a **secondary** environment (`TEST_ENV=demo`), used only for a small,
serial, Chromium-only smoke subset on a schedule or by hand. Switching between environments is
configuration-only (`TEST_ENV=local|demo`); no test code changes. Destructive tests are skipped
automatically when `TEST_ENV=demo` (see `tests/conftest.py`'s `pytest_collection_modifyitems` hook).

## Consequences

- **Gains:** fast, isolated, parallelizable test runs; deterministic data every run; no dependency on a
  third party's uptime for day-to-day development and PR checks; safe to run destructive tests
  (create/update/delete) without damaging a shared resource.
- **Costs:** the project now owns a small amount of infrastructure — pinned Docker images, a seed
  snapshot to keep in sync with the app version, and a readiness probe. The demo environment still gets
  exercised periodically, so the suite doesn't quietly stop working against the "real" public app.
