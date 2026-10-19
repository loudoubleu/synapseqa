# CLAUDE.md — SynapseQA

This file is the hand-off context for Claude Code. Read it fully before making changes.
Last updated: 2026-10-19.

---

## 1. What this project is

**SynapseQA** is a portfolio-grade test automation framework built with **Playwright + Pytest + Python**.
It tests **web UIs and REST APIs**, and is designed the way a production SDET team would build it:
maintainable, layered, CI-ready, and easy to explain in an interview.

### Applications under test

| App | Role | Where |
|---|---|---|
| **OrangeHRM 5.9** (open-source HR system) | Main app: web UI **and** its JSON REST API | Local Docker on `http://localhost:8081` (default); public demo `https://opensource-demo.orangehrmlive.com` as a secondary environment |
| **Restful Booker** | API-only app: token auth, CRUD, chained requests | `https://restful-booker.herokuapp.com` |

The two apps were chosen to show **two authentication styles**: OrangeHRM uses a browser session
cookie; Restful Booker uses a token.

### Objectives (keep every change aligned with these)

1. **One framework for UI and API testing.** Both layers share config, fixtures, reporting and CI.
2. **Hybrid tests.** Use the API to set up state and the UI to verify it (flagship pattern).
3. **Built for real teams.** Parallel runs, multiple environments, traceable failures, containerized CI.
4. **The code is the showcase.** Type hints, linting, clean layers, documented decisions (ADRs).
5. **Role-based tests.** Prove Admin vs. ESS (regular employee) access at both UI and API level.
6. Aim for **40–60 high-quality tests**, not hundreds of shallow ones.

The full design plan (13 sections: goals, apps, environment strategy, stack, architecture, layout,
design examples, role-based tests, coverage, CI/CD, roadmap, showcase tips, open decisions) is committed
at `docs/Test_Automation_Framework_Plan.docx`.

---

## 2. Current state of the codebase

**Phases 1–5 are complete**, except two Phase 4 items blocked by the same gap (Leave pages and
Supervisor role tests, see below) — see `TODO.md`. Git repository initialized and pushed to
`https://github.com/loudoubleu/synapseqa` (public); CI runs on every pull request; nightly (browser
matrix) and demo-smoke (public demo) run on schedule + manual dispatch; pre-commit hooks installed
locally. Live Allure report: **https://loudoubleu.github.io/synapseqa/** (updated after every nightly
run, history across runs).

```
SynapseQA/
├── CLAUDE.md · README.md · TODO.md
├── pyproject.toml · uv.lock · .python-version · .gitignore
├── Dockerfile · .dockerignore         # containerized test runner, verified against the real app
├── .env                               # local secrets — NEVER commit, never print values
├── .env.example · .pre-commit-config.yaml
├── .venv/                             # uv-managed virtual environment (Python 3.13.1)
├── .github/workflows/
│   ├── ci.yml                          # every pull request: lint, mypy, smoke (chromium)
│   ├── nightly.yml                     # daily + manual: full suite × {chromium,firefox,webkit}, -n 4
│   └── demo-smoke.yml                  # weekly + manual: smoke subset, serial, vs. the public demo
├── docs/
│   ├── Test_Automation_Framework_Plan.docx
│   └── adr/0001-…  0002-…  0003-…     # no architecture.md yet
├── __snapshots__/                     # visual-regression baselines — committed; generated on Linux
│                                       # (the Dockerized runner), NOT locally on Windows — see §7
├── infra/
│   ├── docker-compose.orangehrm.yml   # OrangeHRM + MariaDB, starts pre-installed from seed
│   ├── wait_for_ready.py              # readiness probe (stdlib only)
│   └── seed/{orangehrm.sql, confs/{Conf.php, cryptokeys/.htaccess}}
├── src/framework/
│   ├── config/settings.py             # pydantic-settings Settings, local/demo
│   ├── data/builders.py               # EmployeeBuilder, UserBuilder, BookingBuilder (Faker)
│   ├── auth/roles.py                  # Role enum, EXPECTED_MENU per role
│   ├── ui/
│   │   ├── pages/{base_page,login_page,dashboard_page}.py
│   │   ├── pages/pim/{employee_list_page,add_employee_page,personal_details_page}.py
│   │   ├── pages/admin/{user_management_page,add_user_page}.py
│   │   └── components/{component,dropdown,autocomplete,date_picker,data_table,toast,modal,side_menu}.py
│   └── api/
│       ├── base_client.py             # wraps APIRequestContext: get/post/put/patch/delete_json + logging
│       ├── models/{common,employee,user,booking}.py
│       └── clients/{employee_client,user_client,booking_client}.py
└── tests/
    ├── conftest.py                    # settings/base_url/readiness + admin+ESS auth-state + role fixtures
    │                                   # + all API client fixtures + an Allure failure-screenshot hook
    ├── ui/{test_login,test_add_employee,test_personal_details,test_employee_delete_modal,
    │       test_network_mocking,test_visual_regression,test_accessibility}.py
    ├── e2e/{test_employee_search_hybrid,test_admin_add_user_hybrid,test_user_search_hybrid}.py
    ├── roles/test_role_access.py
    └── api/{orangehrm/{test_employees,test_users}.py, restful_booker/{test_booking_smoke,test_booking_crud}.py}
```

Still missing from the target layout: `docs/architecture.md` (Phase 6).

**Leave pages and Supervisor role tests are deliberately not built yet — same blocker.** A fresh seeded
instance has no leave type or leave period configured — `/leave/applyLeave` shows "No Leave Types with
Leave Balance" rather than a usable form. Building `ApplyLeavePage`/approval pages (and, downstream,
Supervisor role tests, which need an ESS user's leave request to approve) needs that configured first
(via Admin > Leave in the UI, or finding the right API payload) — not yet investigated.

GitHub repo secrets `TEST_ADMIN_USERNAME`/`TEST_ADMIN_PASSWORD` are set (via `gh secret set`, values
never printed). History was rewritten once early on (commits `929aaac`..`3a1f5f1`) to drop an unwanted
`Co-Authored-By: Claude` trailer — do not add that trailer to future commits.

### `.env` keys (values are local test credentials — do not echo them)

- `TEST_ADMIN_USERNAME`, `TEST_ADMIN_PASSWORD` — the OrangeHRM admin created in the install wizard.
  Verified 2026-10-18: they log in successfully on port 8081 **and** match the admin in `seed/orangehrm.sql`.
- `TEST_ENV=local`
- `TEST_ORANGEHRM_URL=http://localhost:8081`, `TEST_BOOKER_API_URL=https://restful-booker.herokuapp.com`
  — added 2026-10-18 so `Settings` (§9 step 3) has everything it needs.

`.env.example` (committed, placeholders only) mirrors these five keys.

---

## 3. Recent changes (chronological)

1. **Plan written** (Word doc above). App choice changed from Automation Exercise/SauceDemo to
   **OrangeHRM + Restful Booker**; added local-vs-demo environment strategy and role-based tests.
2. **Docker Desktop installed** (per-user install, WSL 2 backend).
3. **OrangeHRM installed locally** via the web wizard (DB host `db`, port 3306, DB `orangehrm`, user `root`).
4. **Seed snapshot taken**: DB dump (`infra/seed/orangehrm.sql`) and `lib/confs` copied out of the container.
5. **Compose file rewritten** (`infra/docker-compose.orangehrm.yml`):
   - Images pinned: `mariadb:11.8.9@sha256:f16d7a34…` and `orangehrm/orangehrm@sha256:d692780e…` (OrangeHRM 5.9).
   - DB loads `seed/orangehrm.sql` via `/docker-entrypoint-initdb.d` **only when the `db_data` volume is empty**.
   - App mounts `seed/confs/Conf.php` read-only → starts already installed, no wizard.
   - Healthchecks on both services, so `up -d --wait` returns only when ready.
   - Host port configurable: `${ORANGEHRM_PORT:-8081}`.
   - Verified in a throwaway project (`-p synapseqa-verify`, port 8091): starts installed, 171 tables, 1 user.
6. **`infra/wait_for_ready.py` added.** Exit codes: `0` ready, `1` timeout, `2` setup wizard (seed not loaded).
   Reads `--url` / `$TEST_ORANGEHRM_URL`, default `http://localhost:8081`. All three outcomes tested.
7. **Admin password in `.env` corrected** by the user; login verified.
8. **uv project initialised**: Python pinned to 3.13, `requires-python >=3.12`, dependencies added,
   Playwright browsers installed (Chromium, Firefox, WebKit).
9. **`pyproject.toml` configured** with pytest markers, Playwright defaults, Allure, ruff, mypy; **`.gitignore` added**.
10. **Sample smoke test passed** (headless Chromium opened the login page and found the Login button, 3.45 s).
    The sample test was a throwaway and is not in the repo.

> Note: the user's long-running containers may still have been created from the **old** Compose file
> (no Conf.php mount, unpinned images). Running `up -d --wait` recreates them on the new config;
> data in `db_data` is kept.

---

## 4. Tooling and versions

| Tool | Version | Notes |
|---|---|---|
| Python | 3.13.1 (in `.venv`) | System default is 3.14; the project deliberately pins 3.13 |
| uv | 0.13.1 at `C:\Users\louaw\.local\bin\uv.exe` | A second, **Langflow-bundled** `uv.exe` is also on PATH — don't use it. Check with `uv --version` |
| pytest | 9.1.1 | |
| playwright / pytest-playwright | 1.64.0 / 0.10.0 | `--base-url` option is built into pytest-playwright |
| pydantic / pydantic-settings | 2.14.1 / 2.16.0 | |
| faker | 40.43.0 | |
| pytest-xdist / pytest-rerunfailures | 3.8.0 / 16.7 | `flaky` marker comes from rerunfailures |
| allure-pytest | 2.16.2 | The Allure **CLI** (needs Java) is not installed; results are still written |
| ruff / mypy / pre-commit (dev) | 0.17.1 / 2.4.0 / 4.7.0 | |
| Docker Desktop | Engine 29.8.2, Compose v5.6.0 | Per-user install (see §8 for PATH) |

### pytest configuration (in `pyproject.toml`)

- `testpaths = ["tests"]`, `pythonpath = ["src"]` (so `import framework` works).
- `addopts`: `-ra --strict-markers --strict-config --browser=chromium --tracing=retain-on-failure
  --video=retain-on-failure --screenshot=only-on-failure --output=test-results
  --alluredir=reports/allure-results --clean-alluredir`.
- **Markers**: `smoke`, `regression`, `ui`, `api`, `e2e`, `roles`, `destructive`
  (plus `flaky` from pytest-rerunfailures). Unknown markers are errors.
- ruff: line length 110, target py312, rules `E F W I B UP SIM PT RUF`.
- mypy: `strict = true`, pydantic plugin, `mypy_path = "src"`; relaxed `disallow_untyped_defs` for `tests.*`.

---

## 5. Commands (run from the repo root, PowerShell)

```powershell
# Start OrangeHRM (pre-installed from seed) and wait until healthy
docker compose -f infra/docker-compose.orangehrm.yml up -d --wait
uv run python infra/wait_for_ready.py

# Stop (keeps data) / full reset to the seed (DELETES local OrangeHRM data — ask the user first)
docker compose -f infra/docker-compose.orangehrm.yml down
docker compose -f infra/docker-compose.orangehrm.yml down -v

# Python environment
uv sync                              # recreate .venv exactly from uv.lock
uv add <pkg> / uv add --dev <pkg>    # never use pip install
uv run playwright install            # browsers (CI: add --with-deps chromium)

# Tests
uv run pytest -m smoke
uv run pytest -m "api and not destructive"
uv run pytest --headed --browser firefox
uv run pytest -n 4                   # parallel (local env only) — see note below on worker count

# Quality
uv run ruff check . ; uv run ruff format . ; uv run mypy src
```

**On `-n` worker count:** `-n auto` (16 on this machine) was measurably *slower* than `-n 4`
(50s vs. 21s for the full suite, confirmed by running both) — OrangeHRM is a single Docker container
with one PHP-FPM/MariaDB backend, so past a handful of concurrent browsers it becomes the bottleneck,
not client-side CPU. `-n 4`–`-n 8` is the sweet spot locally; re-measure if the container gets more
resources. Session-scoped fixtures that persist to disk (`admin_storage_state`, `ess_storage_state`)
key their filename on `$PYTEST_XDIST_WORKER` (falls back to `"master"` outside xdist) — xdist gives
each worker its own session scope, so without a worker-unique filename, parallel workers racing to
write/read the same `.auth/admin_state.json` is a real (if intermittent) bug, not a hypothetical one.

---

## 6. Architecture and conventions (from the plan — follow these)

### Layers

```
tests/ (ui, api, e2e, roles)
   │  pytest fixtures (conftest.py)
   ├─► Page objects + component objects   src/framework/ui/{pages,components}
   └─► API clients (services)             src/framework/api/{clients,models}
core: config · logging · data builders · models · utils
```

**Main rule:** tests never touch locators or raw HTTP. They speak in business terms
(`pim.search_employee(name)`, `employee_api.create(employee)`).

### Target layout (to build)

```
src/framework/
  config/settings.py        # pydantic-settings, TEST_ prefix, local/demo
  api/base_client.py        # wraps Playwright APIRequestContext, logging, assertions
  api/clients/              # employee_client.py, user_client.py, booking_client.py
  api/models/               # pydantic request/response schemas (contract checks)
  ui/pages/                 # base_page, login, dashboard, pim/, admin/, leave/
  ui/components/            # side_menu, dropdown, autocomplete, date_picker, data_table, toast, modal
  auth/roles.py             # Role enum, per-role login + storage_state
  data/builders.py          # EmployeeBuilder, UserBuilder, BookingBuilder (Faker)
  utils/                    # logger, allure helpers
tests/
  conftest.py  api/{orangehrm,restful_booker}/  ui/  e2e/  roles/
docs/  architecture.md  adr/
.github/workflows/  ci.yml  nightly.yml  demo-smoke.yml
```

### Coding rules

- **Locators:** web-first only (`get_by_role`, `get_by_label`, `get_by_placeholder`, `get_by_text`).
  No XPath unless there is no alternative; document why if used.
- **No `time.sleep`.** Use Playwright auto-waiting and `expect(...)` assertions.
- **No assertions inside page objects** (they return data/locators; tests assert). Navigation methods
  return the next page object.
- OrangeHRM's custom widgets (dropdowns are **not** native `<select>`, autocompletes, date pickers,
  tables, toasts) get **reusable component classes**.
- **Test data:** every test creates its own data with a unique prefix (`auto_<short-uuid>`) through the
  API, and deletes it in fixture teardown (`yield`). Never depend on pre-existing records.
- **Fixture scopes:** `session` for settings, readiness check, per-role `storage_state`;
  `function` for `page`, page objects and test data.
- **Config:** everything from `Settings` (pydantic-settings, `TEST_` prefix, `.env`). No hard-coded URLs
  or credentials in tests. Credentials are `SecretStr`.
- **Type hints everywhere** in `src/`; code must pass `ruff check`, `ruff format`, `mypy src`.
- `destructive` tests must be skipped automatically when `TEST_ENV=demo` (conftest hook).
- `flaky` is a last resort, always with a comment explaining why.

### Environment rules

| | `local` (default) | `demo` |
|---|---|---|
| Target | Docker OrangeHRM on `localhost:8081` | Public demo site |
| Used for | Development, PR checks, nightly regression | Weekly/manual smoke only |
| Parallel / browser matrix | Allowed | **No** — serial, Chromium, `smoke` only |
| Destructive tests | Allowed | **Skipped** |

Never change the admin's password or roles in tests; create dedicated test users through the API.

---

## 7. OrangeHRM facts verified in this project

- **Login (UI/HTTP):** `GET /web/index.php/auth/login` renders `<auth-login … :token="&quot;<csrf>&quot;">`.
  Login is `POST /web/index.php/auth/validate` with form fields `_token`, `username`, `password`.
  Success redirects to `/web/index.php/dashboard/index`; failure redirects back to login with
  `invalid_credentials`. Session cookie name: `_orangehrm`.
- **API — employees:** `GET .../pim/employees?limit=N` → **200**, `{"data":[{...}],"meta":{"total":int},
  "rels":[]}`; **401** unauthenticated. `employeeId` is `str | None` (`null` until assigned — a newly
  created employee has no employee ID, unlike the seeded admin's `"0001"`). `POST .../pim/employees`
  with just `{firstName, lastName}` → **200** `{"data":{...employee...},"meta":[],"rels":[]}` (note:
  `meta` is `[]` here, a `dict` with `"total"` only on the **list** endpoint — two different shapes for
  the same key name). `GET .../pim/employees/{empNumber}` → same single-employee shape.
  **`PUT .../pim/employees/{empNumber}` is 403** — the real update endpoint is
  `PUT .../pim/employees/{empNumber}/personal-details`, which returns more fields (otherId,
  nationality, …) that the `Employee` model simply ignores (pydantic's default `extra="ignore"`).
  `DELETE .../pim/employees` takes `{"ids":[...]}` → `{"data":[<empNumber>,...]}`. Missing a required
  field → **422** `{"error":{"status":"422","message":"Invalid Parameter","data":
  {"invalidParamKeys":["lastName"]}}}`.
- **API — admin users:** `GET/POST/DELETE .../admin/users` follow the same envelope/ID-list pattern as
  employees. A user needs `username`, `password`, `userRoleId`, `empNumber`, `status` — confirmed
  **role IDs: `1` = Admin, `2` = ESS** (`src/framework/api/clients/user_client.py` exposes
  `ADMIN_ROLE_ID`/`ESS_ROLE_ID`). The app enforces password complexity server-side (a plain lowercase
  password like `"weak"` is rejected with the same 422 shape, keyed `"password"`); Faker's
  `password(special_chars=True, digits=True, upper_case=True, lower_case=True)` satisfies it.
- **Login page locators:** placeholders `Username` / `Password`; button role `button`, name `Login`.
  Invalid credentials render the text "Invalid credentials" on the login page. Submitting with both
  fields empty renders two "Required" validation messages (one per field). Successful login lands on
  a page with a `role=heading` element named "Dashboard".
- **Admin's side menu** (confirmed): `['Admin', 'PIM', 'Leave', 'Time', 'Recruitment', 'My Info',
  'Performance', 'Dashboard', 'Directory', 'Maintenance', 'Claim', 'Buzz']`. ESS's menu is still
  unverified — needed for Phase 4's role tests.
- **UI widgets (custom, not native HTML controls):** dropdown trigger is a `.oxd-select-text` div;
  clicking it opens a `role=listbox` of `role=option` items (fully role-locatable once open). The
  typeahead ("Type for hints...") autocomplete works the same way — fill the input, then
  `get_by_role("option", name=...)`; Playwright's default substring name-matching means passing just
  the unique `auto_<uuid>` last name is enough, no need to know the full rendered label. Date fields
  (`.oxd-date-input input`) accept direct `yyyy-mm-dd` text entry — no need to drive the calendar
  popup. Table rows are `.oxd-table-card` elements. The toast (`.oxd-toast`, no ARIA role) and the
  confirm modal (`.oxd-dialog-sheet`, buttons "Yes, Delete" / "No, Cancel") are both plain CSS-class
  locators since neither carries useful semantics.
- **Known UI pitfalls** (all hit for real building Phase 3 pages — see `git log` for
  `feat: Phase 3 UI layer` for the full story):
  - `page.wait_for_url()` does not reliably catch this SPA's client-side route change after a save
    (e.g. Add Employee → Personal Details); wait on a resulting-page locator (its heading) instead.
  - A `.oxd-form-row` scoped by `has_text="Employee Id"`/`"Username"` matches a **broader** row that
    also contains other fields (e.g. First/Middle/Last Name), so `.locator("input").first` silently
    grabs the wrong input. Scope with `.oxd-input-group` instead — one label, one input, no ambiguity.
  - The server's auto-suggested Employee Id on Add Employee has been observed to collide with one
    already in use; `AddEmployeePage` clears that field before save so the server assigns a fresh one.
  - The toast is transient (auto-dismisses) — don't assert on it after an action that also waits for a
    page transition; the dismiss can beat your assertion. Assert the toast right after a same-page
    save, not after a save that navigates.
  - Save confirmation text varies by action: "Successfully Saved" (create), "Successfully Updated"
    (edit), "Successfully Deleted" (delete) — don't assume one wording everywhere.
- **Uninstalled instance behaviour:** app pages return **500**, and `/` redirects to
  `./installer/index.php`. `wait_for_ready.py` uses this to report exit code 2.
- **Installer:** the new console installer (`php installer/console install:on-new-database`) is
  **interactive only**. The old `installer/cli_install.php` + YAML is deprecated. That's why we use the
  DB-snapshot approach.
- Image layout: web root `/var/www/html` (declared as a Docker VOLUME), config at
  `/var/www/html/lib/confs/Conf.php`, PHP 8.3, `curl` available in the container.
- **ESS role (confirmed):** side menu is `{Leave, Time, My Info, Performance, Dashboard, Directory,
  Claim, Buzz}` — no Admin, PIM, Recruitment, or Maintenance (vs. Admin's full 12-item menu above).
  Navigating directly to an admin UI URL (e.g. `/admin/viewSystemUsers`) does **not** redirect —
  the page loads but shows the text "Credential Required" instead of the real content. Hitting an
  admin API endpoint (e.g. `GET /admin/users`) as ESS returns **403**
  `{"error":{"status":403,"message":"Unauthorized"}}`, same shape as the unauthenticated case.
- **Accessibility:** the real app has genuine pre-existing non-critical `axe-core` violations on
  every page checked (color-contrast, missing landmarks, missing `html[lang]`, missing H1, etc.) —
  this is the app's own debt, not something to "fix" from the test suite. `tests/ui/test_accessibility.py`
  scopes its assertion to `impact == "critical"` on the login page specifically, which currently has
  none; that's a meaningful regression guard, not a blanket zero-violations claim.
- **Visual regression:** `expect(page).to_have_screenshot()` **does not exist in Python's Playwright
  bindings** — confirmed by inspecting `PageAssertions` on the installed version (1.64.0); it's a
  Node.js/`@playwright/test`-only API that CLAUDE.md's plan assumed existed. Used
  `pytest-playwright-visual-snapshot`'s `assert_snapshot(page, name=...)` fixture instead (same
  baseline/compare/diff workflow). Baselines live in `__snapshots__/` and **are committed**; diff
  output on a failing run goes to `snapshot_failures/` (gitignored). **Baselines must be generated on
  Linux, not Windows** — a Windows-captured baseline failed nightly.yml's very first real run on
  chromium (OS-level font rendering/anti-aliasing differences against Ubuntu, not a real regression).
  Regenerate via the Dockerized runner against the live app, e.g. (PowerShell, from the repo root, with
  `infra-...` compose stack already up):
  `docker run --rm --network infra_default -e TEST_ORANGEHRM_URL=http://orangehrm:80
  -e TEST_ADMIN_USERNAME=... -e TEST_ADMIN_PASSWORD=... -v ${PWD}/__snapshots__:/app/__snapshots__
  --entrypoint uv synapseqa-tests run pytest tests/ui/test_visual_regression.py --update-snapshots`
  — then review the diff image before committing. (In Git Bash on Windows, the same command needs
  `MSYS_NO_PATHCONV=1` prefixed, or the `-v` mount silently fails to write back to the host — it was
  hit for real building this.) Visual regression only runs on chromium (`browser_name` fixture, skip
  otherwise) since baselines are rendering-engine-specific and firefox/webkit have none. **Consequence:
  `test_login_page_visual_regression` is now expected to fail when run locally on this Windows dev
  machine** (confirmed: `uv run pytest` reproduces it) — the committed baseline matches Linux
  rendering, not Windows. That's correct, not a regression: trust this check from CI or the Dockerized
  runner, not a bare local Windows run.
- **Browser matrix note:** pytest-playwright's `--browser` flag is additive
  (`action="append"`) and the plugin already defaults to chromium with none given, so `addopts` must
  **not** bake in `--browser=chromium` — doing so made `pytest --browser firefox` run chromium *and*
  firefox together, silently (fixed; see git history on `pyproject.toml`).
- **Public demo (`https://opensource-demo.orangehrmlive.com`) login (confirmed):** `Admin` / `admin123`
  — OrangeHRM's own publicly documented demo credentials, not secrets; `demo-smoke.yml` sets them as
  plain `env:` values, not GitHub secrets.

**Restful Booker facts verified:** `POST /auth` with valid credentials (`admin`/`password123`, the
service's own public demo credentials) returns **200** `{"token": "..."}`; with bad credentials it
still returns **200**, body `{"reason": "Bad credentials"}` — never 401/403, so `BookingClient.
authenticate()` returns `None` rather than raising. `GET /booking` returns **200** with a JSON array of
`{"bookingid": int}`. `POST /booking` → **200** `{"bookingid":int,"booking":{...}}`; `GET /booking/{id}`
→ the bare booking object (no `bookingid` wrapper). Writes (`PUT`/`PATCH`/`DELETE` on `/booking/{id}`)
need the token sent as a **`Cookie: token=<token>` header**, not `Authorization`; without it they
return **403**. `DELETE` on success returns **201**, not 200/204 (a known quirk). `GET` on a deleted/
nonexistent booking → **404**. `POST /booking` with a required field missing entirely → **500**
(a documented quirk of this demo API, not treated as our bug); empty strings and `0` values are
accepted fine. The service's storage is ephemeral/shared — a booking created by a one-off script can
disappear on its own; tests always create and delete their own data rather than relying on persistence.

---

## 8. Windows / environment gotchas

- **Docker not found in a terminal** → the terminal was opened before Docker Desktop was installed.
  Open a new terminal, or for the current one:
  `$env:Path += ";$env:LOCALAPPDATA\Programs\DockerDesktop\resources\bin"`
- **Docker API 500 errors** (`dockerDesktopLinuxEngine … 500 Internal Server Error`) → Docker Desktop is
  starting or stopped. Wait for it to be running.
- **Don't redirect binary/SQL output with `>` in PowerShell** (encoding issues, and it won't create
  missing folders). For DB dumps use `mariadb-dump --result-file=/tmp/x.sql` inside the container, then
  `docker compose cp`.
- `uv init` sets `requires-python` from the default interpreter (3.14); keep it at `>=3.12`.
- `infra/seed/confs/Conf.php` contains the local DB root password (`rootpass`, a test-only value that
  must match the Compose file). It's fine to commit.

---

## 9. Exact next steps (Phases 1–5 complete, except the Leave blocker → now in Phase 6)

Phases 1–5 are done — see `TODO.md` for the checked-off detail on each, and git history for how every
fact was verified for real (not assumed) before being coded, including real bugs found and fixed along
the way: an xdist `storage_state` race, a `--browser` flag silently running two browsers at once, a
visual-regression baseline captured on the wrong OS, and (Allure-on-Pages) the live page being
CDN-cached just long enough to look like history wasn't accumulating when it actually was — caught by
checking the deployed git content directly instead of trusting one screenshot. The two Phase 4 open
items (Leave pages, Supervisor role tests) share one blocker: a fresh seeded instance has no leave type
or leave period configured (§7) — not yet investigated.

GitHub Pages is enabled (`gh-pages` branch, confirmed with the user before enabling since it's a public
setting); live report at **https://loudoubleu.github.io/synapseqa/**, updated by `nightly.yml`'s
`publish-report` job after every run.

**Now in Phase 6 — showcase polish** (per the roadmap and `TODO.md`):

- README architecture diagram refresh (reflect the actual current layout, not just the Phase 1 sketch),
  a "how to add a test" guide, a short demo GIF.
- Status badges (CI build, Allure report link).
- Clean commit history check — conventional commits throughout already; confirm nothing needs squashing.
- A final pass for `time.sleep`, XPath-heavy locators, assertions inside page objects, dependence on
  pre-existing data, hard-coded credentials — the project's own stated anti-patterns (§6).
- Decide on and, if picked up, unblock Leave pages/Supervisor role tests (still deferred, not in scope
  unless explicitly revisited).

---

## 10. Open decisions (ask the user; don't decide silently)

None currently open. **Decided:** reporting is **Allure** (already wired in `addopts`; the CLI needs
Java and isn't installed locally yet — results still write to `reports/allure-results` without it);
Supervisor role tests are in scope for Phase 4, not a stretch goal (§9); `Details.jpg` was intentionally
deleted.

## 11. Working agreements for Claude

- Use `uv run …` for everything Python; never `pip install`.
- Never print, log or commit values from `.env`.
- Ask before `docker compose … down -v`, deleting files, or changing the user's `.env`.
- Don't run parallel or destructive tests against the public demo.
- Confirm OrangeHRM UI text, API paths and role behaviour against the running app before hard-coding them.
- Keep this file current: update §2, §3 and §9 when a step is finished.
