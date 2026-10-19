# CLAUDE.md — SynapseQA

This file is the hand-off context for Claude Code. Read it fully before making changes.
Last updated: 2026-10-18.

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

The full design plan is a Word document outside this repo:
`C:\Users\louaw\Claude_Local_Session\Test_Automation_Framework_Plan.docx` (13 sections: goals, apps,
environment strategy, stack, architecture, layout, design examples, role-based tests, coverage,
CI/CD, roadmap, showcase tips, open decisions). Consider copying it into `docs/`.

---

## 2. Current state of the codebase

**Phase 1 (Foundation) is partly done.** Infrastructure and tooling exist and are verified;
no framework code or real tests have been written yet. **Git repository initialized**
(first commit `929aaac chore: bootstrap project`; pushed to
`https://github.com/loudoubleu/synapseqa`). History was rewritten once (`929aaac`..`3a1f5f1`) to drop
an unwanted `Co-Authored-By: Claude` trailer — do not add that trailer to future commits.

```
SynapseQA/
├── CLAUDE.md                         # this file
├── pyproject.toml                    # deps + pytest/ruff/mypy config (see §4)
├── uv.lock                           # locked dependency versions
├── .python-version                   # 3.13
├── .gitignore                        # ignores .venv, caches, test output, .env
├── .env                              # local secrets — NEVER commit, never print values
├── .venv/                            # uv-managed virtual environment (Python 3.13.1)
└── infra/
    ├── docker-compose.orangehrm.yml  # OrangeHRM + MariaDB, starts pre-installed from seed
    ├── wait_for_ready.py             # readiness probe (stdlib only)
    └── seed/
        ├── orangehrm.sql             # MariaDB dump taken right after the install wizard
        └── confs/
            ├── Conf.php              # OrangeHRM DB config written by the installer
            └── cryptokeys/.htaccess  # from the image; no encryption key (encryption disabled)
```

Directories from the plan that **do not exist yet**: `tests/`,
`.github/workflows/`, `Dockerfile` (test runner), `.pre-commit-config.yaml`, `README.md`.
`docs/` now exists, holding a copy of the plan Word doc (no `architecture.md`/`adr/` yet). `.env.example`
exists and is committed. `src/framework/config/settings.py` exists (pydantic-settings `Settings` class,
verified loads from `.env` and passes ruff/mypy). `tests/conftest.py` exists: session `settings`
fixture, `base_url` override, autouse OrangeHRM readiness check (reuses `infra/wait_for_ready.py` via
a `sys.path` insert — that script stays stdlib-only), `context` fixture override applying
`default_timeout_ms`, and a `pytest_collection_modifyitems` hook skipping `destructive` tests when
`TEST_ENV=demo`. `src/framework/ui/pages/` has `base_page.py` (generic `path` + `open()` → `Self`),
`login_page.py`, `dashboard_page.py`; `tests/ui/test_login.py` covers valid login, invalid password,
and empty-field validation (`smoke`/`ui` markers), all passing against the local instance.
`tests/conftest.py` also has a session-scoped `admin_storage_state` fixture (logs in once via a raw
`browser.new_context()`, saves to `.auth/admin_state.json`, gitignored) and a function-scoped
`admin_page` fixture that opens a new context from that saved state — verified a test using `admin_page`
lands pre-authenticated with no `LoginPage` interaction needed. API layer first slice also exists:
`api/base_client.py` (get/post/delete over `APIRequestContext`, logs method+url+status), `api/models/
employee.py` (pydantic `Employee`/`EmployeeListResponse`), `api/clients/employee_client.py`
(`EmployeeClient.list()`); `tests/conftest.py`'s `employee_client` fixture builds it from
`playwright.request.new_context(storage_state=admin_storage_state)`. `tests/api/orangehrm/
test_employees.py` passes against the real API. `TODO.md` at the repo root tracks the full checklist
derived from the plan — update it alongside §9 as steps land.

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
uv run pytest -n auto                # parallel (local env only)

# Quality
uv run ruff check . ; uv run ruff format . ; uv run mypy src
```

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
- **API:** `GET /web/index.php/api/v2/pim/employees?limit=N` returns **200** with
  `{"data":[{"empNumber":int,"firstName":str,"lastName":str,"middleName":str,"employeeId":str,
  "terminationId":int|null}],"meta":{"total":int},"rels":[]}` when sent with the logged-in session
  cookie; **401** without it. So OrangeHRM API clients must be built from an authenticated context
  (`page.request`, or a `playwright.request.new_context(storage_state=...)` as `employee_client` does).
- **Login page locators:** placeholders `Username` / `Password`; button role `button`, name `Login`.
  Invalid credentials render the text "Invalid credentials" on the login page. Submitting with both
  fields empty renders two "Required" validation messages (one per field). Successful login lands on
  a page with a `role=heading` element named "Dashboard".
- **Uninstalled instance behaviour:** app pages return **500**, and `/` redirects to
  `./installer/index.php`. `wait_for_ready.py` uses this to report exit code 2.
- **Installer:** the new console installer (`php installer/console install:on-new-database`) is
  **interactive only**. The old `installer/cli_install.php` + YAML is deprecated. That's why we use the
  DB-snapshot approach.
- Image layout: web root `/var/www/html` (declared as a Docker VOLUME), config at
  `/var/www/html/lib/confs/Conf.php`, PHP 8.3, `curl` available in the container.
- Still **unverified** (check against the running app before hard-coding): other API paths/payloads
  (create/delete employee, admin users), each role's menu items, the access-denied behaviour for ESS users.

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

## 9. Exact next steps (Phase 1 → Phase 2)

Work through these in order. Each step should leave `ruff`, `mypy` and the test suite green.

1. **Initialise git.** `git init`, confirm `.env` and `.venv` are ignored, then make the first commit
   (conventional commit style, e.g. `chore: bootstrap project`).
2. **Add `.env.example`** with placeholders (no real values):
   `TEST_ENV=local`, `TEST_ORANGEHRM_URL=http://localhost:8081`, `TEST_ADMIN_USERNAME=`,
   `TEST_ADMIN_PASSWORD=`, `TEST_BOOKER_API_URL=https://restful-booker.herokuapp.com`.
   Add `TEST_ORANGEHRM_URL` and `TEST_BOOKER_API_URL` to `.env` too (ask the user, since it's their file).
3. **Create `src/framework/` package** (`__init__.py` files) and `config/settings.py`:
   ```python
   class Settings(BaseSettings):
       model_config = SettingsConfigDict(env_file=".env", env_prefix="TEST_", extra="ignore")
       env: Literal["local", "demo"] = "local"
       orangehrm_url: HttpUrl = HttpUrl("http://localhost:8081")
       admin_username: str
       admin_password: SecretStr
       booker_api_url: HttpUrl = HttpUrl("https://restful-booker.herokuapp.com")
       default_timeout_ms: int = 10_000

       @property
       def is_shared_env(self) -> bool:
           return self.env == "demo"
   ```
4. **Create `tests/conftest.py`** with:
   - session-scoped `settings` fixture;
   - override pytest-playwright's `base_url` fixture to return `settings.orangehrm_url`;
   - a session-scoped autouse readiness check for `local` (reuse the logic in `infra/wait_for_ready.py`);
   - set the default timeout on `page`/`context` from settings;
   - a `pytest_collection_modifyitems` hook that skips `destructive` tests when `settings.is_shared_env`.
5. **UI layer, first slice:** `ui/pages/base_page.py` (holds `page`, `open()` using a `path` attribute),
   `login_page.py`, `dashboard_page.py`. Then `tests/ui/test_login.py`:
   - `smoke`: valid admin login lands on the dashboard;
   - invalid password shows "Invalid credentials";
   - empty fields show "Required" validation (confirm exact text in the app first).
6. **Auth state:** session fixture that logs in as admin once and saves `storage_state`
   (e.g. under `.auth/`, add it to `.gitignore`); an `admin_page` fixture using it.
7. **API layer, first slice:** `api/base_client.py` wrapping `APIRequestContext` (base URL, logging,
   `expect(resp).to_be_ok()` helpers); `api/models/employee.py` (pydantic); `api/clients/employee_client.py`
   built from the admin `storage_state`. Test `tests/api/orangehrm/test_employees.py` (`smoke`, `api`):
   list employees returns 200 and validates against the model.
8. **Restful Booker smoke:** `booking_client.py` with token auth (`POST /auth`), test `GET /booking`
   and `POST /auth` with bad credentials.
9. **`.pre-commit-config.yaml`:** ruff (check + format) and mypy; run `uv run pre-commit install`.
10. **CI (`.github/workflows/ci.yml`)** on pull requests: checkout → `astral-sh/setup-uv` → `uv sync` →
    `docker compose -f infra/docker-compose.orangehrm.yml up -d --wait` →
    `uv run python infra/wait_for_ready.py` → `uv run playwright install --with-deps chromium` →
    ruff → mypy → `uv run pytest -m smoke` → upload `test-results/` on failure.
    Admin credentials come from GitHub secrets (`TEST_ADMIN_USERNAME`, `TEST_ADMIN_PASSWORD`).
11. **README.md:** what the project is, architecture diagram, 60-second quick start
    (Compose up → `uv sync` → `uv run playwright install` → `uv run pytest -m smoke`), environment table.
12. **First ADRs in `docs/adr/`:** `0001-local-docker-instance-vs-public-demo.md`,
    `0002-playwright-api-context-over-requests.md`, `0003-pydantic-for-contract-checks.md`.

After that, continue with the roadmap: Phase 2 (full API layer, builders with cleanup, negative tests),
Phase 3 (component library, PIM/Admin/Leave pages), Phase 4 (hybrid E2E + Admin/ESS/Supervisor role tests,
network mocking, visual + a11y), Phase 5 (xdist, browser matrix, Dockerized runner, Allure on GitHub
Pages, nightly + demo-smoke workflows), Phase 6 (showcase polish).

---

## 10. Open decisions (ask the user; don't decide silently)

None currently open. **Decided:** reporting is Allure (§4); Supervisor role tests are in scope for
Phase 4, not a stretch goal (§9); `Details.jpg` was intentionally deleted.

**Decided:** Reporting is **Allure** (already wired in `addopts`; the CLI needs Java and isn't installed
locally yet — results still write to `reports/allure-results` without it).

## 11. Working agreements for Claude

- Use `uv run …` for everything Python; never `pip install`.
- Never print, log or commit values from `.env`.
- Ask before `docker compose … down -v`, deleting files, or changing the user's `.env`.
- Don't run parallel or destructive tests against the public demo.
- Confirm OrangeHRM UI text, API paths and role behaviour against the running app before hard-coding them.
- Keep this file current: update §2, §3 and §9 when a step is finished.
