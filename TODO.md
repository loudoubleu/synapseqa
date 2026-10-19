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
- [x] `.pre-commit-config.yaml` (ruff check+format, mypy); `uv run pre-commit install` — verified
  `pre-commit run --all-files` passes, and that a deliberately broken file is caught and reformatted
- [x] `.github/workflows/ci.yml`: checkout → setup-uv → `uv sync` → compose up --wait → readiness probe →
  playwright install --with-deps → ruff → mypy → `pytest -m smoke` → upload `test-results/` on failure.
  `TEST_ADMIN_USERNAME`/`TEST_ADMIN_PASSWORD` set as GitHub secrets (piped via `gh secret set`, never
  printed). Verified green end-to-end via a throwaway test PR.
- [x] `README.md`: what it is, architecture diagram, 60-second quick start, environment table
- [x] First ADRs in `docs/adr/`:
  - [x] `0001-local-docker-instance-vs-public-demo.md`
  - [x] `0002-playwright-api-context-over-requests.md`
  - [x] `0003-pydantic-for-contract-checks.md`

## Facts to verify against the running app before hard-coding (blocks role/API work)

- [ ] Employee create/update/delete API paths + payloads
- [ ] Admin user management API paths + payloads
- [ ] Each role's exact menu items (Admin vs. ESS)
- [ ] Access-denied behavior/text for ESS hitting admin pages & admin API endpoints

## Phase 2 — API layer

- [x] `BaseClient` (wraps `APIRequestContext`, logging) — done in Phase 1; PUT/PATCH + headers
  passthrough added here for Booker's token-as-Cookie-header writes
- [x] OrangeHRM `employee_client.py` / `user_client.py`: create/get/update/delete for employees
  (update via `/personal-details`, confirmed — bare `PUT /employees/{id}` is 403), create/get/delete
  for users (confirmed role IDs: Admin=1, ESS=2; app enforces password complexity)
  — search/pagination beyond a plain `limit` param not yet added (not currently needed by any test)
- [x] Restful Booker full suite: CRUD (create/get/update/partial-update/delete, chained in one
  round-trip test), token auth incl. writes-without-auth → 403, negative/boundary inputs (missing
  required fields → a documented 500 quirk, not our bug; empty/zero values accepted), data-driven
  parametrized cases, a response-time threshold
- [x] Data builders with cleanup: `EmployeeBuilder`, `UserBuilder`, `BookingBuilder` (Faker,
  `auto_<uuid>` prefix) — verified no leftover test records after a full run
- [x] Negative-path tests for both APIs (422 validation errors on OrangeHRM; 403/500 on Booker)

## Phase 3 — UI layer

- [x] `BasePage` (Phase 1) + component library: Dropdown, Autocomplete, DatePicker, DataTable, Toast,
  Modal — all confirmed against the running app (roles, CSS classes, auto-dismiss timing), no
  assertions inside any of them
- [x] PIM pages (employee list/add/edit, photo upload): `EmployeeListPage`, `AddEmployeePage`,
  `PersonalDetailsPage` — covers search+delete-via-modal, create+photo upload, and update (DOB +
  dropdowns)
- [x] Admin pages (user management): `UserManagementPage`, `AddUserPage`
- [ ] Leave pages (apply, approve) — **blocked**: a fresh instance has no leave types/period configured
  (`/leave/applyLeave` shows "No Leave Types with Leave Balance"); needs Admin > Leave configuration
  (via UI or API) before these pages can be built and tested — picked up in a later pass
- [x] Failure artifacts wired into Allure: a `pytest_runtest_makereport` hook attaches a screenshot
  from `page`/`admin_page` on failure — verified with a deliberately failing throwaway test that the
  attachment lands in the Allure result

## Phase 4 — Hybrid + roles

- [x] 3–5 E2E hybrid flows (API sets up state, UI verifies) — 3 done (`tests/e2e/`): employee created
  via API shows in PIM search; admin creates a user via UI for an API-created employee; user created
  via API shows in Admin's user search. Leave-applied-in-UI-shows-via-API still needs Leave pages first
- [x] `auth/roles.py`: `Role` enum, per-role login + `storage_state` (`ess_storage_state` fixture
  creates a throwaway employee+ESS user via the API each session, logs in once, tears down after)
- [x] `logged_in_as` parametrized fixture (indirect on `role`)
- [x] Role tests: menu visibility (Admin vs. ESS — confirmed exact menu sets against the app), direct-URL
  access ("Credential Required" for ESS on an admin page), API 401/403 checks (403 confirmed)
- [ ] Supervisor role tests: ESS user assigned as another employee's supervisor; can see and approve
  their direct report's leave requests — **blocked**, same reason as Leave pages (needs Leave module
  configured first)
- [x] Network mocking tests (`page.route`) — employee-list API mocked to 500; confirmed the UI degrades
  gracefully (error toast + "No Records Found") rather than crashing
- [x] Visual regression check — `expect(page).to_have_screenshot()` **does not exist in Python
  Playwright** (confirmed: it's a Node.js/`@playwright/test`-only API); used
  `pytest-playwright-visual-snapshot`'s `assert_snapshot` fixture instead (same workflow). Verified it
  both passes against its baseline and genuinely catches a real pixel change
- [x] Accessibility scan (`axe-playwright-python`) — scoped to "critical" impact on the login page
  (the app has real pre-existing non-critical violations outside our control; see `CLAUDE.md` §7).
  Verified it genuinely fails when a critical issue is introduced

## Phase 5 — Scale + polish

- [x] `pytest-xdist` parallel runs (local env only) — verified `-n 4` passes reliably (2 consecutive
  runs) and is faster than both serial and `-n auto`/16 workers (single OrangeHRM container is the
  bottleneck, not CPU). Fixed a real race: `admin_storage_state`/`ess_storage_state` now key their
  filename on `$PYTEST_XDIST_WORKER` since xdist gives each worker its own session scope
- [ ] Browser matrix (Chromium/Firefox/WebKit) in nightly
- [x] Dockerized test runner (`mcr.microsoft.com/playwright/python` base, pinned by digest matching
  the installed `playwright==1.64.0`) — verified it builds, joins `infra_default`, and runs real tests
  against the live `orangehrm` service by its compose hostname (`docker run --network infra_default
  -e TEST_ORANGEHRM_URL=http://orangehrm:80 ...`), 5/5 smoke tests passed
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
  network mocking — not hundreds of shallow ones. **31 tests as of end of Phase 4** (5 OrangeHRM API,
  10 Restful Booker API, 8 UI incl. visual/a11y/network-mocking, 3 E2E hybrid, 4 roles, 3 UI login) —
  on track; Phase 5/6 shouldn't need many more to land in range

