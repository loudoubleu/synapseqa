# SynapseQA architecture

This document explains how SynapseQA is put together and why: the layers, how a test runs from start
to finish, how authentication and test data are handled, and how the same suite runs locally, in
Docker and in CI. The README covers what the project is and how to run it. Individual decisions are
recorded in [`adr/`](adr/).

---

## 1. Layers

```
┌──────────────────────────────── tests/ ────────────────────────────────┐
│  ui/          api/orangehrm/   api/restful_booker/   e2e/      roles/   │
└───────────────┬────────────────────────────────────────────┬───────────┘
                │        tests/conftest.py (fixtures)         │
┌───────────────▼────────────────┐          ┌─────────────────▼──────────────┐
│  UI layer   framework/ui/       │          │  API layer   framework/api/     │
│  pages/      one class per      │          │  clients/    one class per      │
│              screen             │          │              resource           │
│  components/ reusable widgets   │          │  models/     pydantic contracts │
│  (BasePage, Component)          │          │  (BaseClient)                   │
└───────────────┬────────────────┘          └─────────────────┬──────────────┘
                │                                             │
┌───────────────▼─────────────────────────────────────────────▼──────────────┐
│  core   config/settings.py · auth/roles.py · data/builders.py               │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                    Playwright (Browser / BrowserContext / APIRequestContext)
```

### Dependency rules

| Layer | May import | Must not |
|---|---|---|
| `tests/` | page objects, components, API clients, models, builders, `Role` | build locators, make raw HTTP calls, hard-code URLs or credentials |
| `ui/pages/` | `ui/components/`, other pages (to return them from navigation methods) | assert anything; import from `api/` |
| `ui/components/` | Playwright only | know which page they live on |
| `api/clients/` | `api/base_client.py`, `api/models/` | import from `ui/`; assert anything beyond schema validation |
| `api/models/` | pydantic only | import anything else from the framework |
| core | pydantic / Faker / stdlib | import from `ui/` or `api/` |

`ui/` and `api/` don't know about each other. The only place they meet is `tests/conftest.py` and the
hybrid tests in `tests/e2e/` and `tests/roles/`. Because of this, either half can be replaced or
reused on its own.

### What lives in each layer

**Pages** (`src/framework/ui/pages/`). Each page subclasses `BasePage`, which holds the `Page` and an
optional `path` that `open()` navigates to (relative to the context's `base_url`). In its constructor a
page defines its locators as attributes, built with web-first queries (`get_by_role`,
`get_by_placeholder`, …). Each OrangeHRM widget becomes a component instance. Page methods describe
user intent (`search()`, `delete_row(text)`). Navigation methods return the next page object, so tests
can chain them: `LoginPage(page).open().login(user, pw)` returns a `DashboardPage`.

**Components** (`src/framework/ui/components/`). OrangeHRM's widgets are not native HTML controls.
Dropdowns aren't `<select>` elements, and the typeahead, date picker, table, toast and confirm modal
are custom too. Each one gets a small `Component` subclass that wraps a root `Locator`. A page creates
a component by passing it a locator, e.g.
`Autocomplete(page, page.get_by_placeholder("Type for hints...").first)`. The widget's quirks are
handled once inside the component. One example is `DatePicker.set_date()`, which clears the field and
types into it, because `.fill()` appends to whatever is already there (see `CLAUDE.md` §7).

**API clients** (`src/framework/api/clients/`). Each client subclasses `BaseClient`, a thin wrapper
around Playwright's `APIRequestContext` ([ADR 0002](adr/0002-playwright-api-context-over-requests.md))
that adds base-URL joining and request/response logging. Clients expose business operations
(`EmployeeClient.create()`, `LeaveClient.apply()`, `BookingClient.authenticate()`) and return typed
models.

**Models** (`src/framework/api/models/`). These are pydantic v2 models for every response the framework
uses. Clients call `Model.model_validate(response.json())` before returning, so a contract change shows
up as a `ValidationError` that names the field
([ADR 0003](adr/0003-pydantic-for-contract-checks.md)). camelCase API keys map to snake_case
attributes through `Field(alias=...)`. The models also record app quirks, such as `meta` being a dict
on list endpoints but `[]` on single-item endpoints.

**Core.**
- `config/settings.py` is a pydantic-settings `Settings` class. It reads `TEST_`-prefixed environment
  variables, then `.env`. The admin password is a `SecretStr`. `is_shared_env` is the single switch
  for demo-specific behaviour.
- `auth/roles.py` holds the `Role` enum and `EXPECTED_MENU`, which lists the side-menu modules each
  role should see. These were confirmed against the running app.
- `data/builders.py` has Faker-backed builders that produce unique `auto_<short-uuid>` data, so tests
  never collide with each other or with existing records.

---

## 2. The fixture graph

`tests/conftest.py` wires the layers together. Scopes follow a simple rule: anything expensive and
read-only is session-scoped, and anything a test can change is function-scoped.

```
session ─┬─ settings ──► base_url
         ├─ _ensure_orangehrm_ready (autouse; skipped on demo)
         ├─ admin_storage_state ─────────────┐     UI login once, saved to
         │                                   │     .auth/admin_state.<worker>.json
         └─ ess_storage_state ◄──────────────┤     creates employee + ESS user via API,
                                             │     UI login once, deletes both at session end
function ┬─ admin_page / ess_page            │     new context from the saved state
         ├─ role ─► logged_in_as             │     parametrized (indirect) over Role
         ├─ employee_client / user_client /  │
         │  leave_client ◄───────────────────┘     APIRequestContext from admin's state
         ├─ employee                               creates via API, yields, deletes
         ├─ booking_client ─► auth_token           Restful Booker, no browser state
         └─ context (override)                     applies settings.default_timeout_ms
```

Two hooks complete the setup:

- `pytest_runtest_makereport` attaches a screenshot to Allure for any failed test that has a `Page`
  argument. This covers `admin_page`, `ess_page` and `logged_in_as`, as well as pytest-playwright's own
  `page`.
- `pytest_collection_modifyitems` skips every `@pytest.mark.destructive` test when `TEST_ENV=demo`.

### Parallel runs

pytest-xdist gives each worker its own session scope, so session fixtures run once per worker, not
once per run. The storage-state files are named after `$PYTEST_XDIST_WORKER` (falling back to
`master`). Without that, workers would race to write and read the same `.auth/*.json` file. This was
an intermittent failure we actually hit, not a hypothetical one.

---

## 3. Authentication model

The two apps under test use different auth styles on purpose, and the framework handles both with
the same `APIRequestContext` approach.

| | OrangeHRM | Restful Booker |
|---|---|---|
| Mechanism | Session cookie `_orangehrm`, set by a form login with a CSRF `_token` | `POST /auth` returns a token, sent back as a `Cookie: token=…` header on writes |
| How tests get it | One real **UI** login per role per worker, saved with `storage_state()` | `BookingClient.authenticate()` per test |
| How the API layer reuses it | `playwright.request.new_context(storage_state=…)`: the API client sends the same cookie the browser received | Token passed explicitly to write methods |
| Failure shape | 401 unauthenticated / 403 wrong role, `{"error": {...}}` | Bad credentials still return **200** with `{"reason": ...}`, so `authenticate()` returns `None` |

There's no separate HTTP-level login for OrangeHRM. API clients reuse the cookie from a browser login,
so the API tests use the same session real users get.

### Roles

- **Admin** uses the seeded admin account (credentials come from `Settings`, never from test code).
  Tests never change its password or role.
- **ESS** uses a throwaway employee and ESS user created through the API for each session. It is
  logged in once through the UI and removed when the session ends.
- **Supervisor** isn't a role ID in OrangeHRM. It's an ESS user who has a report-to relationship with
  another employee. `test_supervisor_leave_approval.py` builds both users and the relationship inside
  the test, then signs each of them in with its own browser context.

`tests/roles/test_role_access.py` is parametrized over `Role` through the indirect `role` →
`logged_in_as` fixture pair, and asserts against `EXPECTED_MENU`. So a single test function covers both
roles.

---

## 4. How a hybrid test runs

The flagship pattern sets up state through the API, checks it in the UI and cleans up through the API.
Taking `tests/e2e/test_employee_search_hybrid.py` as an example:

```
 pytest                conftest                EmployeeClient         OrangeHRM          EmployeeListPage
   │  request fixtures    │                          │                    │                     │
   ├────────────────────► │ admin_storage_state      │                    │                     │
   │                      │ (cached per worker) ─────┼── UI login ───────►│                     │
   │                      │ employee_client ────────►│                    │                     │
   │                      │ employee: create() ─────►│── POST /pim/employees ─►│                 │
   │                      │                          │◄── 200 {data:…} ───│                     │
   │                      │                          │  validate → Employee                     │
   │                      │ admin_page (same cookie) │                    │                     │
   │  test body ──────────┼──────────────────────────┼────────────────────┼──► open(), search  │
   │                      │                          │                    │◄── browser traffic ─┤
   │  expect(row).to_be_visible()                    │                    │                     │
   │  teardown ──────────►│ employee: delete() ─────►│── DELETE /pim/employees ►│                │
```

Setting up state through the API takes milliseconds and doesn't depend on the Add Employee screen, so
a failure in this test points at search, not at data creation. The reverse direction also exists:
`tests/e2e/test_leave_apply_hybrid.py` acts in the UI and verifies through the API.

---

## 5. Test data lifecycle

- **Every test creates the data it needs** through API clients, using builders, so names are unique
  (`auto_<short-uuid>`). No test depends on a record that already exists, and that includes Restful
  Booker, whose shared storage can be wiped at any time.
- **Cleanup happens in fixture teardown** (code after `yield`), so it runs even when the test fails.
  Tests that build their own data inline, like the supervisor test, clean up in the same function.
- **Organisation-wide configuration is seeded, not created by tests.** The Leave Period (Jan 1–Dec 31)
  and the "Annual Leave" type (`ANNUAL_LEAVE_TYPE_ID = 1`) are in `infra/seed/orangehrm.sql`. They are
  global, singular settings: if each test created them, tests would conflict whenever they ran in
  parallel. Per-employee data, such as entitlements, is still created by each test.
- **Tests that change data** carry `@pytest.mark.destructive` and are skipped automatically on the
  shared demo.

---

## 6. Environments and infrastructure

```
                ┌──────────────── TEST_ENV=local (default) ────────────────┐
 uv run pytest ─┤  infra/docker-compose.orangehrm.yml                       │
  (host or      │   ├─ db         mariadb (pinned digest), loads             │
   Docker)      │   │             seed/orangehrm.sql on an empty volume    │
                │   └─ orangehrm  OrangeHRM 5.9 (pinned digest), mounts    │
                │                 seed/confs/Conf.php → starts installed   │
                └──────────────────────────────────────────────────────────┘
                ┌──────────────── TEST_ENV=demo ───────────────────────────┐
                │  opensource-demo.orangehrmlive.com, serial, smoke,       │
                │  chromium, destructive skipped                           │
                └──────────────────────────────────────────────────────────┘
                Restful Booker (hosted, shared) is the same in both
```

- **The seeded database replaces the install wizard.** OrangeHRM 5.9's console installer only runs
  interactively. Instead, a database dump plus `Conf.php` lets the app start already installed, which
  keeps CI reproducible with no manual steps ([ADR 0001](adr/0001-local-docker-instance-vs-public-demo.md)).
- **There are two readiness checks.** Compose healthchecks let `up -d --wait` block until the
  containers are healthy. `infra/wait_for_ready.py` then confirms the login page actually renders. It
  returns exit code 2 if it finds the setup wizard, which means the seed didn't load. The session
  fixture `_ensure_orangehrm_ready` calls the same function, so a bare `pytest` run fails fast with a
  clear message instead of 33 timeouts.
- **Switching environments only changes configuration.** `TEST_ENV`, `TEST_ORANGEHRM_URL` and the
  credentials all come from `Settings`. No test code changes between local, Docker and demo.
- **There's a containerized runner.** The `Dockerfile` builds on the official Playwright Python image
  (pinned digest) plus a pinned `uv`. It joins the Compose network and reaches the app as
  `http://orangehrm:80`. Visual-regression baselines are generated with it so they match Linux
  rendering.

---

## 7. CI topology

| Workflow | Trigger | Target | Scope | Parallelism |
|---|---|---|---|---|
| `ci.yml` | every pull request | local Compose stack on the runner | `ruff check`, `ruff format --check`, `mypy src tests`, `pytest -m smoke` | serial, chromium |
| `nightly.yml` | daily 03:00 UTC + manual | local Compose stack | full suite | matrix {chromium, firefox, webkit} × `-n 4` |
| `demo-smoke.yml` | weekly Mon 06:00 UTC + manual | public demo | `smoke and not destructive` | serial, chromium |

`nightly.yml` has a final `publish-report` job. It merges the three browsers' Allure results, carries
over history from the `gh-pages` branch and publishes the report to
https://loudoubleu.github.io/synapseqa/. Each job tears the stack down with `down -v`, so every run
starts from the seed.

Why `-n 4` and not `-n auto`: the bottleneck is the single OrangeHRM container (one PHP-FPM and MariaDB
backend), not the runner's CPU. Locally, `-n auto` (16 workers) took 50s and `-n 4` took 21s.

---

## 8. Diagnosing failures

A failing test leaves these behind, without any extra code in the test:

| Artifact | Source | Where |
|---|---|---|
| Playwright trace (DOM snapshots, network, console, **including API calls** made through `APIRequestContext`) | `--tracing=retain-on-failure` | `test-results/` |
| Video | `--video=retain-on-failure` | `test-results/` |
| Screenshot | `--screenshot=only-on-failure` + conftest hook | `test-results/` and attached to Allure |
| Request log (`GET <url>` / `-> <status> <url>`) | `BaseClient` logger | pytest captured log, shown in the report |
| Contract mismatch | pydantic `ValidationError` naming the field | the test's traceback |
| Visual diff | `pytest-playwright-visual-snapshot` | `snapshot_failures/` |

In CI, `test-results/` is uploaded as a build artifact when a job fails, and Allure results are
uploaded per browser.

---

## 9. Extension points

| To add… | Do this |
|---|---|
| A new screen | Subclass `BasePage`, set `path`, define locators in `__init__`, return the next page from navigation methods |
| A new widget type | Subclass `Component` and put the widget's quirks inside it, not in every page that uses it |
| A new API resource | Add pydantic models under `api/models/`, subclass `BaseClient`, validate every response, and add a function-scoped client fixture built from `admin_storage_state` |
| A new role | Add it to `Role` and `EXPECTED_MENU` (confirmed against the app), add a session storage-state fixture modelled on `ess_storage_state`, and add a branch to `logged_in_as` |
| A new environment | Add a value to `Settings.env` and decide what `is_shared_env` (or a new property) should skip |

Before hard-coding any UI text, API path or role behaviour, confirm it against the running app. The
confirmed facts are collected in `CLAUDE.md` §7.

---

## 10. Where the build differs from the original plan

The original plan is in `Test_Automation_Framework_Plan.docx`. These are the places where the code
deliberately turned out different:

- **There's no `utils/` package.** Logging is the standard library `logging` module, used directly in
  `BaseClient`. The only Allure helper needed is the screenshot hook in `conftest.py`. A package for
  two lines of code would add structure without adding value.
- **`auth/roles.py` has no login helpers.** Logging in and saving storage state happen in conftest
  fixtures, because that's where scope and teardown are managed. `roles.py` only holds data (the
  `Role` enum and expected menus).
- **Visual regression uses `pytest-playwright-visual-snapshot`.** The plan assumed
  `expect(page).to_have_screenshot()`, which only exists in Node's `@playwright/test`, not in the
  Python bindings.
- **The suite has 33 tests, not 40–60.** We chose fewer, real-scenario tests over padding the count.
