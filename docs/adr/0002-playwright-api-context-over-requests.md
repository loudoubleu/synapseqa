# 2. Use Playwright's APIRequestContext for API testing, not a separate HTTP library

## Status

Accepted

## Context

The framework needs an HTTP client for testing OrangeHRM's and Restful Booker's REST APIs directly
(not through the browser), and for API-driven test setup in hybrid tests. The two realistic options
were a dedicated Python HTTP library (e.g. `httpx` or `requests`) or Playwright's own
`APIRequestContext`, which ships with the `playwright` dependency the UI layer already requires.

## Decision

Use Playwright's `APIRequestContext` (`BaseClient` in `src/framework/api/base_client.py` wraps it) for
all API clients, rather than adding a second HTTP library.

Reasons:

- **One tool for both layers.** UI and API tests already depend on Playwright; adding `httpx` or
  `requests` as well means two HTTP stacks to understand, configure and debug.
- **Shared tracing and artifacts.** Requests made through `APIRequestContext` show up in the same trace
  viewer, screenshots and videos Playwright already produces on failure, so a hybrid test's API calls
  and UI actions appear on one timeline.
- **Cookie/session sharing.** An `APIRequestContext` can be created from a browser context or a saved
  `storage_state` (see `tests/conftest.py`'s `employee_client` fixture), so OrangeHRM's API clients reuse
  the exact session cookie a UI login produced — no separate HTTP-level login flow to maintain for the
  session-cookie auth style.
- **Consistent semantics.** Timeouts, retries and base-URL resolution behave the same way they do for
  `page.goto()`, so there's one mental model across the framework instead of two.

## Consequences

- **Gains:** fewer dependencies, shared failure artifacts, and natural support for OrangeHRM's
  cookie-based auth without extra plumbing.
- **Costs:** `APIRequestContext` is a slightly less familiar API than `requests` to engineers coming
  from a pure-backend testing background, and some advanced HTTP features (e.g. low-level connection
  pooling control) aren't exposed the way they would be in `httpx`. Neither has been needed so far —
  Restful Booker's token auth (`BookingClient.authenticate()`) works the same way through
  `APIRequestContext` as the cookie-based OrangeHRM clients do, just without a shared browser context.
