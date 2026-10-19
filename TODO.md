# SynapseQA — Project Checklist

Derived from `docs/Test_Automation_Framework_Plan.docx` and `CLAUDE.md`. Check items off as they land;
update `CLAUDE.md` §2/§3/§9 when a phase finishes.

## Open decisions (ask the user — don't decide silently)

All resolved:

- [x] Local install automation: DB snapshot vs. scripted install → **DB snapshot** (done, §3)
- [x] Reporting: **Allure** (already wired in `addopts`)
- [x] `Details.jpg`: intentionally deleted
- [x] Supervisor role tests: **in scope for Phase 4** (not a stretch goal)

## Phase 1 — Foundation (in progress)

- [x] `git init`; confirm `.env`/`.venv` ignored; first commit (conventional commit style) — `929aaac`
- [x] Push to `https://github.com/loudoubleu/synapseqa` (public); history rewritten to drop the
  `Co-Authored-By: Claude` trailer per user request — don't add it to future commits
- [x] `.env.example` with placeholders (`TEST_ENV`, `TEST_ORANGEHRM_URL`, `TEST_ADMIN_USERNAME`,
  `TEST_ADMIN_PASSWORD`, `TEST_BOOKER_API_URL`)
- [x] Add `TEST_ORANGEHRM_URL` / `TEST_BOOKER_API_URL` to real `.env` (confirmed with user)
- [x] `src/framework/` package skeleton + `config/settings.py` (pydantic-settings, `TEST_` prefix, local/demo)
- [x] `tests/conftest.py`: session `settings` fixture, `base_url` override, readiness autouse check,
  default timeout wiring, `destructive`-skip-on-demo hook — all four behaviors verified with a
  throwaway test (not committed): base_url resolves, login page loads, context timeout is 10s not
  Playwright's 30s default, and the destructive test is skipped only under `TEST_ENV=demo`
- [x] UI slice: `ui/pages/base_page.py`, `login_page.py`, `dashboard_page.py`
- [x] `tests/ui/test_login.py`: valid login → dashboard (smoke); invalid password message;
  empty-field validation — verified against the running app first: "Invalid credentials" and two
  "Required" messages (one per field); all 3 tests pass
- [x] Auth state fixture: log in as admin once, save `storage_state` under `.auth/` (gitignored)
- [x] API slice: `api/base_client.py`, `api/models/employee.py`, `api/clients/employee_client.py`
  (built from admin `storage_state`)
- [x] `tests/api/orangehrm/test_employees.py`: list employees → 200 + schema validation (smoke, api)
- [x] Restful Booker smoke: `booking_client.py` (token auth), `GET /booking`, bad-credentials `POST /auth`
  — verified against the live API first (bad auth returns 200 + `{"reason": "Bad credentials"}`, not 401)
- [ ] `.pre-commit-config.yaml` (ruff check+format, mypy); `uv run pre-commit install`
- [ ] `.github/workflows/ci.yml`: checkout → setup-uv → `uv sync` → compose up --wait → readiness probe →
  playwright install --with-deps → ruff → mypy → `pytest -m smoke` → upload `test-results/` on failure
- [ ] `README.md`: what it is, architecture diagram, 60-second quick start, environment table
- [ ] First ADRs in `docs/adr/`:
  - [ ] `0001-local-docker-instance-vs-public-demo.md`
  - [ ] `0002-playwright-api-context-over-requests.md`
  - [ ] `0003-pydantic-for-contract-checks.md`

## Facts to verify against the running app before hard-coding (blocks role/API work)

- [ ] Employee create/update/delete API paths + payloads
- [ ] Admin user management API paths + payloads
- [ ] Each role's exact menu items (Admin vs. ESS)
- [ ] Access-denied behavior/text for ESS hitting admin pages & admin API endpoints

## Phase 2 — API layer

- [ ] `BaseClient` (wraps `APIRequestContext`, logging, `expect(resp).to_be_ok()` helpers)
- [ ] OrangeHRM `employee_client.py` / `user_client.py` (CRUD, search, pagination, validation errors)
- [ ] Restful Booker full suite: CRUD, token auth (valid/invalid/missing), chained requests,
  negative/boundary inputs, data-driven cases, response-time thresholds
- [ ] Data builders with cleanup: `EmployeeBuilder`, `UserBuilder`, `BookingBuilder` (Faker, `auto_<uuid>` prefix)
- [ ] Negative-path tests for both APIs

## Phase 3 — UI layer

- [ ] `BasePage` + component library: dropdown, autocomplete, date picker, data table, toast, modal
- [ ] PIM pages (employee list/add/edit, photo upload)
- [ ] Admin pages (user management)
- [ ] Leave pages (apply, approve)
- [ ] Failure artifacts wired into Allure (trace/video/screenshot on failure)

## Phase 4 — Hybrid + roles

- [ ] 3–5 E2E hybrid flows (API sets up state, UI verifies) — e.g. employee created via API shows in PIM;
  leave applied in UI shows via API
- [ ] `auth/roles.py`: `Role` enum, per-role login + `storage_state`
- [ ] `logged_in_as` parametrized fixture
- [ ] Role tests: menu visibility (Admin vs. ESS), direct-URL access, API 401/403 checks
- [ ] Supervisor role tests: ESS user assigned as another employee's supervisor; can see and approve
  their direct report's leave requests
- [ ] Network mocking tests (`page.route`) — e.g. simulate a 500 from the employee list API
- [ ] Visual regression check (`expect(page).to_have_screenshot()`)
- [ ] Accessibility scan (axe-playwright-python)

## Phase 5 — Scale + polish

- [ ] `pytest-xdist` parallel runs (local env only)
- [ ] Browser matrix (Chromium/Firefox/WebKit) in nightly
- [ ] Dockerized test runner (`mcr.microsoft.com/playwright/python` base)
- [ ] Allure report published to GitHub Pages (history across runs)
- [ ] `.github/workflows/nightly.yml` (full regression, sharded, browser matrix)
- [ ] `.github/workflows/demo-smoke.yml` (serial, Chromium only, no destructive tests, against public demo)

## Phase 6 — Showcase polish

- [ ] README architecture diagram + "how to add a test" guide
- [ ] Short demo GIF
- [ ] Status badges (build, Allure report link)
- [ ] Clean commit history (conventional commits); PRs against own repo so CI is visible
- [ ] Final pass: no `time.sleep`, no XPath-heavy locators, no assertions in page objects,
  no dependence on pre-existing data, no hard-coded credentials

## Coverage target sanity check

- [ ] ~40–60 total tests across: OrangeHRM API, Restful Booker API, UI, E2E/hybrid (3–5), roles,
  network mocking — not hundreds of shallow ones
