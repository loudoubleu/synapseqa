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
- [x] Leave pages (apply, approve) — unblocked: seeded a Leave Period + one Leave Type ("Annual
  Leave", id=1) into `infra/seed/orangehrm.sql` so every fresh instance has the Leave module usable
  once a per-employee entitlement is granted. `ApplyLeavePage`, `LeaveListPage` built and confirmed
  against the running app; `LeaveClient` covers entitlements, self-apply, admin assign-on-behalf, and
  approve/reject (self-apply lands "Pending Approval", admin assign auto-schedules instead — genuinely
  different, confirmed via DB inspection)
- [x] Failure artifacts wired into Allure: a `pytest_runtest_makereport` hook attaches a screenshot
  from `page`/`admin_page` on failure — verified with a deliberately failing throwaway test that the
  attachment lands in the Allure result

## Phase 4 — Hybrid + roles

- [x] 3–5 E2E hybrid flows (API sets up state, UI verifies) — 4 done (`tests/e2e/`): employee created
  via API shows in PIM search; admin creates a user via UI for an API-created employee; user created
  via API shows in Admin's user search; leave applied in the UI shows via the API
  (`test_leave_apply_hybrid.py`, reuses the same authenticated session for the verification call)
- [x] `auth/roles.py`: `Role` enum, per-role login + `storage_state` (`ess_storage_state` fixture
  creates a throwaway employee+ESS user via the API each session, logs in once, tears down after)
- [x] `logged_in_as` parametrized fixture (indirect on `role`)
- [x] Role tests: menu visibility (Admin vs. ESS — confirmed exact menu sets against the app), direct-URL
  access ("Credential Required" for ESS on an admin page), API 401/403 checks (403 confirmed)
- [x] Supervisor role tests: ESS user assigned as another employee's supervisor; can see and approve
  their direct report's leave requests (`tests/roles/test_supervisor_leave_approval.py`) — confirmed
  the admin "Leave List" view only surfaces a pending request once a supervisor relationship exists
  (`EmployeeClient.assign_supervisor`, the Report-to → Assigned Supervisors relationship), and that
  self-approval is disabled (an employee viewing their own request only gets Add Comment/Cancel, never
  Approve/Reject) — required the request to come from a separate report employee, not admin itself
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
- [x] Browser matrix (Chromium/Firefox/WebKit) in nightly — found and fixed a real bug along the way:
  `addopts` baked in `--browser=chromium`, and pytest-playwright's `--browser` is additive, so
  `pytest --browser firefox` was silently running chromium *and* firefox together; removed it since
  the plugin already defaults to chromium with none given
- [x] Dockerized test runner (`mcr.microsoft.com/playwright/python` base, pinned by digest matching
  the installed `playwright==1.64.0`) — verified it builds, joins `infra_default`, and runs real tests
  against the live `orangehrm` service by its compose hostname (`docker run --network infra_default
  -e TEST_ORANGEHRM_URL=http://orangehrm:80 ...`), 5/5 smoke tests passed
- [x] Allure report published to GitHub Pages (history across runs) — live at
  https://loudoubleu.github.io/synapseqa/. GitHub Pages enabled with user confirmation first
  (`gh-pages` branch, build_type legacy). Verified with two real `workflow_dispatch` runs: report
  renders correctly (73 test cases, 100%, 5 suites matching the real test layout) and history
  genuinely accumulates across runs — confirmed at the git-content level (`history-trend.json` had 1
  entry after the first deploy, 2 after the second), not just a visual check (the live page itself was
  CDN-cached for a few minutes, which could've been mistaken for a failure)
- [x] `.github/workflows/nightly.yml` (full regression, sharded with `-n 4`, browser matrix) — verified
  with two real `workflow_dispatch` runs; the first failed on chromium only (visual-regression baseline
  was captured on Windows, didn't match Ubuntu's font rendering — not a real regression), fixed by
  regenerating the baseline inside the Dockerized runner (Linux, same browser build CI uses); second
  run green on all three browsers
- [x] `.github/workflows/demo-smoke.yml` (serial, Chromium only, no destructive tests, against public
  demo) — verified with a real `workflow_dispatch` run, green first try. Uses the demo site's own
  publicly documented login (`Admin`/`admin123`, confirmed against the live site)

## Phase 6 — Showcase polish

- [x] README architecture diagram + "how to add a test" guide — the conceptual diagram was already
  accurate; added a concrete `src`/`tests` project layout (previously missing) and a step-by-step
  "How to add a test" section
- [x] `docs/architecture.md` — layers + dependency rules, fixture graph, auth model, hybrid-test flow,
  data lifecycle, environments, CI topology, failure artifacts, extension points, deviations from plan
- [x] Short demo GIF — no recording tool was available locally (no ffmpeg/vhs/asciinema), so built it
  from real Playwright screenshots + Pillow: login → dashboard → PIM search finding an employee just
  created via the API (the actual flagship hybrid pattern, not a mockup). `docs/media/demo.gif`, ~190KB
- [x] Status badges (build, Allure report link) — CI/nightly/demo-smoke workflow badges + an Allure
  Report badge; verified each badge URL actually resolves (200, image/svg+xml) before committing
- [x] Clean commit history (conventional commits); PRs against own repo so CI is visible — reviewed the
  full `git log`: consistent `feat`/`fix`/`docs`/`ci`/`chore`/`refactor` prefixes throughout, no noise
  commits, nothing needing squashing. One real PR (#1) already exists demonstrating the pattern
  (opened to verify `ci.yml`, merged); the rest of the work went directly to `main` as agreed with the
  user throughout this project — not retroactively redone as PRs, since that would just be performative
- [x] Final pass: no `time.sleep`, no XPath-heavy locators, no assertions in page objects, no
  dependence on pre-existing data, no hard-coded credentials — audited with a full-tree grep; the
  first four were already clean. Found and fixed two real issues: a hard-coded ESS test password
  (now Faker-generated via `UserBuilder`, like every other test-data fixture) and a Booker smoke test
  that assumed the shared public demo already had booking data (now creates and cleans up its own,
  matching the project's own documented principle for that exact service)

## Coverage target sanity check

- [x] ~40–60 total tests across: OrangeHRM API, Restful Booker API, UI, E2E/hybrid (3–5), roles,
  network mocking — not hundreds of shallow ones. **Decided final at 33** (up from 31 after the
  Leave-pages unblock: the Leave-applied-via-API hybrid test and the Supervisor approval role test,
  both previously blocked and now built and passing). Under the original 40–60 estimate, but the user
  confirmed 33 well-chosen, real-scenario tests is enough for this portfolio — not padded with
  low-value tests just to hit a number from the original plan. Closed, not just deferred.

