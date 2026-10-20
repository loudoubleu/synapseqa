# Building SynapseQA from scratch

This is a from-scratch build guide for this framework, written for someone with solid Python and some
Playwright/pytest exposure but no access to an AI pair who's already explored the target app. `TODO.md`
is the checklist of what got built, in order; `CLAUDE.md` §7 is the reference of facts already
confirmed. Neither teaches the thing that actually took the time: **finding those facts out**. This
tutorial tries to.

Read "The discovery habit" below before anything else — it's the one piece of methodology that applies
to every phase that follows, and the one thing a checklist can't hand you.

---

## The discovery habit

Almost everything interesting in `CLAUDE.md` §7 — API payload shapes, which endpoint actually works,
exact error text, which role can see what — was found by **doing the thing in the real running app
first**, then coding against what was actually observed. Not the docs, not what seems reasonable, not
what a similar app does elsewhere.

In practice, for this project that meant three tools used constantly:

1. **Browser DevTools Network tab.** Log in, click the button, fill the form — whatever the feature is
   — and watch the actual request: method, URL, request body shape, response shape, status code. This
   is how every API client's payload (`{firstName, lastName}` for creating an employee, `{action:
   "APPROVE"}` for approving leave, the exact query params for a leave-request list) was found. Never
   guess a field name; read it off a real request.
2. **A disposable Python REPL or throwaway script hitting the API directly**, authenticated via a
   session cookie or token already in hand. Confirms the Network-tab observation outside the browser and
   surfaces things the UI doesn't show you (e.g. that updating an employee via the "obvious" `PUT
   /pim/employees/{id}` returns 403, and the real endpoint is `.../personal-details`).
3. **Direct database inspection** (`docker exec <db-container> mariadb -u... -e "SELECT ..."`) when the
   UI and API both give ambiguous or silent results. This project hit that twice: once to discover that
   an admin "Assign Leave" action writes a different status code than a self-applied leave request
   (nothing in the UI or a 200 response told us that), and once to find a leftover test-data row a
   cleanup pass had missed before re-snapshotting the seed database.

The rule that falls out of this: **if you're about to hard-code a locator, a payload shape, or a status
code, and you haven't personally watched the real app produce it, stop and go look.** This is slower
than assuming, but every "slow test" later in this build is cheaper than a flaky suite built on guesses.
See the [case study](#case-study-unblocking-the-leave-module) at the end for a worked example where this
mattered a lot.

---

## Prerequisites

- Python 3.12+, [`uv`](https://docs.astral.sh/uv/) for environment/dependency management
- Docker Desktop (or another Docker Engine) for a local instance of the app under test
- A GitHub account if you want CI, Pages-hosted reporting, and secrets management
- Patience for the Network tab — you'll live there in Phases 1–3

---

## Phase 0 — Pick your apps and write a one-page plan

Pick (at least) two systems that together let you show range:

- One with **both a web UI and a JSON REST API**, ideally open-source so you can self-host it. This is
  your main app and flagship pattern: set up state via the API, verify it in the UI (or the reverse).
- One **API-only** service, ideally with a different auth style than your main app (session cookie vs.
  bearer token is a good pair) — this is what proves your framework generalizes rather than being
  one app's test suite with a thin wrapper.

Before writing any code, write down: the two apps and why; a target test count (a real but modest number
— 40-ish, not "as many as possible"); the local-vs-shared-environment split (see Phase 1.1 for why this
matters); and which roles you'll prove access for (e.g. admin vs. a regular user). This becomes your
`CLAUDE.md` §1.

---

## Phase 1 — Foundation

### 1.1 Get a resettable local instance running

If your main app is self-hostable, don't test only against a shared public demo — see
[`docs/adr/0001-local-docker-instance-vs-public-demo.md`](adr/0001-local-docker-instance-vs-public-demo.md)
for the full reasoning (shared data, instability, a shared login other people can break, server
etiquette under parallel runs). Keep the public demo as a *secondary*, read-mostly environment.

The pattern that worked well here:

1. Install the app once through its real installer/wizard, by hand, in a disposable container.
2. Take a database dump and copy out its config file (`infra/seed/`).
3. Write a Compose file that loads that dump via the DB image's init-script mechanism (e.g. MariaDB's
   `/docker-entrypoint-initdb.d`) **only when the data volume is empty**, and mounts the config
   read-only — so every fresh `docker compose up` starts already-installed, no wizard, no manual steps.
4. Write a small readiness probe (stdlib `urllib`/`requests`, no extra deps) that polls until the app
   actually answers, with a distinct exit code for "still an uninstalled wizard" vs. "timed out" vs.
   "ready" — you'll want to tell those apart in CI logs.
5. Verify it for real: spin up a **separate, isolated** Compose project (different project name, a
   different host port) from a clean volume and confirm it boots pre-installed. Don't just trust your
   main dev stack, which may have drifted from the Compose file.

This infrastructure investment pays for itself immediately: every test run starts from identical data,
destructive tests are safe, and CI never races the app's own startup.

### 1.2 Scaffold the Python project

```bash
uv init
uv add playwright pytest pytest-playwright pydantic pydantic-settings faker
uv add --dev ruff mypy pre-commit pytest-xdist pytest-rerunfailures allure-pytest
uv run playwright install
```

Pin `requires-python` deliberately in `pyproject.toml` rather than trusting whatever `uv init` picked up
from your system's default interpreter.

Decide your layout up front and write it into your own `CLAUDE.md`:

```
src/framework/{config,auth,data,ui/{pages,components},api/{clients,models}}/
tests/{conftest.py, ui/, api/, e2e/, roles/}
```

The rule worth committing to from day one: **tests never touch locators or raw HTTP.** They call page
objects and API clients in business terms. Enforcing this early is much cheaper than retrofitting it.

### 1.3 Config layer

A `pydantic-settings` `Settings` class, reading `TEST_`-prefixed env vars from `.env`, with a
`local`/`demo` `Literal` field and `SecretStr` for credentials. Everything environment-specific — base
URL, admin credentials, which other API's base URL — flows through this one object. No hard-coded URLs
in test files, ever.

### 1.4 First `conftest.py`

Minimum viable: a session-scoped `settings` fixture, a `base_url` fixture that pytest-playwright
recognizes, a session-scoped autouse fixture that calls your readiness probe before any test runs (and
`pytest.exit`s with a clear message if the app isn't up), and a hook that skips `destructive`-marked
tests when `settings.env == "demo"`.

### 1.5 First page object + smoke test

A `BasePage` holding `page` and an `open()` that navigates to a `path` class attribute. A `LoginPage`
with **web-first locators only** (`get_by_role`, `get_by_label`, `get_by_placeholder`) — find them by
opening DevTools, inspecting the real element, and preferring role/label/placeholder over a CSS class or
XPath every time one exists. Write one smoke test: valid login lands on a dashboard. Confirm the exact
success signal (a heading's accessible name, a URL fragment) by watching the real app, not by assuming.

### 1.6 Auth state fixture

Logging in through the UI for every single test is slow and redundant. Log in **once** per session, save
Playwright's `storage_state` to disk, and build per-test contexts from that saved state. Two things bite
people here that are worth knowing in advance rather than debugging later:

- If you ever add parallel workers (`pytest-xdist`), each worker gets its **own** session scope. If your
  storage-state fixture writes to one fixed path, two workers racing to write/read the same file is a
  real bug, not a hypothetical one — key the filename on the worker ID.
- Login helpers that just submit the form and return often **don't wait for navigation to complete**.
  Don't assume the session is ready right after calling `login()`; assert on something only the logged-in
  page has (a dashboard heading) before trusting the context is authenticated. Getting this wrong shows
  up as an intermittent 401 on the very next request, not an obvious UI failure.

### 1.7 First API client

A `BaseClient` wrapping Playwright's own `APIRequestContext` (not a separate HTTP library — see
[ADR 0002](adr/0002-playwright-api-context-over-requests.md)): thin `get`/`post`/`put`/`delete` methods
with logging, built from a `storage_state`-authenticated context so the browser's own session cookie
rides along with your API calls for free. Define your first pydantic response model
([ADR 0003](adr/0003-pydantic-for-contract-checks.md)) for a read-only "list" endpoint, found via the
discovery habit above — watch the real list request, model what it actually returns, let pydantic's
default `extra="ignore"` absorb fields you don't care about. Test: the list call returns 200 and
validates against the model.

### 1.8 Second app, smoke only

Set up the auth style contrast deliberately — if your main app uses a session cookie, pick (or confirm)
that the second app uses something different, like a bearer token obtained from its own auth endpoint.
One smoke test per obvious case (a real request succeeds; a request with deliberately bad credentials
is rejected) is enough for now — you'll build this out properly in Phase 2.

### 1.9 Pre-commit and CI

`.pre-commit-config.yaml` running lint + format + type-check on every commit locally. A CI workflow
(checkout → install deps → start your Compose stack with `--wait` → run your readiness probe → install
browsers → lint → type-check → run the `smoke`-marked subset) on every pull request. Keep this fast —
full regression is a separate, later workflow (Phase 5).

### 1.10 README and first ADRs

Write the project's actual architecture diagram and a 60-second quick start before you have much to
show — it's much easier to keep a README honest incrementally than to write it from memory at the end.
Record your first few real architectural decisions as ADRs (why local Docker over only a public demo;
why this particular API-context choice; why pydantic) while the reasoning is still fresh — see
[`docs/adr/`](adr/) for the format: Status / Context / Decision / Consequences.

---

## Phase 2 — API layer, in depth

### 2.1 `BaseClient` and clients per resource

Add the remaining verbs your app needs (`put`, `patch`, custom headers for the second app's token). One
client class per resource (`EmployeeClient`, `UserClient`, `BookingClient`, …), each built from an
authenticated context, each method returning a validated pydantic model — never raw `response.json()`
handed back to a test.

### 2.2 Finding real payloads (apply the discovery habit)

For every create/update/delete endpoint: perform the action in the real UI first, read the actual
request/response off the Network tab, replicate it as a direct API call, and note anything surprising
(a field that's `null` until something else happens; an endpoint that looks right but returns 403 while
a sibling path is the real one; an envelope shape that differs between a list endpoint and a single-item
endpoint under the same base path). Write these down somewhere durable (this project kept them in
`CLAUDE.md` §7) — they're exactly the kind of thing you'll otherwise re-discover by accident, under time
pressure, later.

### 2.3 Data builders with guaranteed cleanup

A `Faker`-backed builder per data type (`EmployeeBuilder`, `UserBuilder`, …), each producing uniquely
identifiable data (an `auto_<short-uuid>`-style field) so tests never collide and never depend on
pre-existing records. Pair every builder with a `yield`-based fixture that deletes what it created in
teardown. Worth confirming empirically whether your app cascades deletes (e.g. deleting a parent record
auto-removes its dependent user accounts/records) — it changes how much teardown code you actually need
to write, and you should verify it by checking, not assuming either way.

### 2.4 Negative-path tests

For each resource: a request missing a required field, and (if your app enforces it) a value that fails
server-side validation (a weak password, say). Confirm the real status code and error shape first — one
of the two apps in this project returns a **200** with an error payload on bad credentials rather than
401/403, which is the kind of thing you only know by trying it.

---

## Phase 3 — UI layer

### 3.1 Component objects for custom widgets

Modern app UI kits rarely use native `<select>`/`<input type=date>` — expect custom dropdowns,
autocompletes, date pickers, and data tables built from styled `div`s. Give each a small, reusable
component class (constructed from a root locator) rather than re-deriving the same multi-step
click-then-select dance inside every page object. Confirm each widget's actual interaction pattern
(does it open a `role=listbox` on click? does a date field accept direct typed input, or does it require
driving a calendar popup?) against the real app before writing the component.

### 3.2 Page objects, built from real workflows

For each screen you need: a page object exposing locators and **navigation methods that return the next
page object** — no assertions inside page objects; that's the test's job. Build these by actually
performing the workflow in the browser and watching what happens (does a save navigate away, or stay on
the page and show a toast? what's the page's actual heading once you land on it?).

### 3.3 Pitfalls worth expecting in advance

These are generic enough to show up in most single-page-app UIs, not specific to one project:

- A framework-level "wait for URL to change" helper often doesn't reliably catch a client-side route
  change inside a single-page app. Wait on a locator unique to the resulting page instead.
- A form-section locator scoped by visible label text (`has_text="Employee Id"`) can accidentally match
  a **broader** container that also holds other, unrelated fields, silently grabbing the wrong input.
  Scope to the tightest wrapping element that holds exactly one label and one input.
- Toasts/snackbars are transient. Don't trigger an action that both shows a toast *and* navigates away,
  then assert on the toast — the auto-dismiss can beat your assertion. Assert it right after a
  same-page action instead.
- Confirmation text often varies by action ("Saved" vs. "Updated" vs. "Deleted") — don't hard-code one
  string and reuse it everywhere; check each case.
- At least one input type across a non-trivial app's UI kit will not clear existing content on a
  `.fill()`-equivalent call — it'll concatenate onto whatever was already there. If a field's value looks
  garbled in a failure screenshot (old and new text mashed together), this is the first thing to check,
  not a timing issue.

---

## Phase 4 — Hybrid tests and roles

### 4.1 The hybrid pattern

This is the flagship pattern for a framework that spans UI and API: use the API to set up state quickly
and reliably, then verify it through the UI (or the reverse — act through the UI, verify through the
API). It proves your two layers genuinely share a session/auth model, not just a test runner. A nice
trick: Playwright's `BrowserContext.request` object shares that context's cookies, so once you're
logged in via the UI in a context, you can make authenticated API calls "as" that same user through
`context.request` without a second login.

### 4.2 Role fixtures

A `Role` enum and a fixture that logs in once per role, saves `storage_state` per role, and parametrizes
indirectly so a test can request `role=Role.ADMIN` or `role=Role.STANDARD_USER` and get a correctly
authenticated page. Confirm each role's actual menu/visible-feature set and its actual behavior on a
page or endpoint it shouldn't access (does it redirect? show an in-page "not authorized" message? what
status code does a direct API call return?) — don't assume parity between the UI's and the API's
enforcement; this project found they differ (a non-redirecting in-page message on the UI side, a plain
403 on the API side).

### 4.3 Network mocking

At least one test using your framework's request-interception hook (e.g. `page.route`) to force an API
call to fail, confirming the UI degrades gracefully rather than crashing. Cheap to write, catches a real
class of bug.

### 4.4 Visual regression

Check whether your Playwright binding actually has a built-in screenshot-comparison assertion before
assuming it does — some language bindings of some testing frameworks ship it only in their original
language's version, not every port. If not, a community plugin providing the same baseline/compare/diff
workflow is a fine substitute. Whichever you use: **generate baselines on the same OS your CI runs on**,
not your local dev machine — font rendering and anti-aliasing differ enough between operating systems to
fail a comparison that isn't actually a regression. Expect (and document, so it isn't mistaken for a
real failure later) that a locally-run visual test may legitimately fail on a different OS than the one
that produced the committed baseline.

### 4.5 Accessibility scanning

Scope your assertion realistically. A real, actively-developed app will likely have genuine
pre-existing accessibility debt you don't own and can't fix from a test suite. Scoping to "no
**critical**-impact violations" on a page that currently has none is a meaningful regression guard; a
blanket "zero violations anywhere" assertion against a real app is usually either immediately failing or
quietly skipped — check what the tool actually reports against your app before deciding the threshold.

---

## Phase 5 — Scale and CI

### 5.1 Parallelism, tuned not assumed

Measure before picking a worker count. `-n auto` is not automatically best — a single-container local
app backend can become the bottleneck well before you run out of client-side CPU, making a high worker
count *slower* than a moderate one. Time a couple of options for real and pick accordingly; re-measure
if your backend's resources change.

### 5.2 A flag-interaction bug worth checking for

If your test runner's browser-selection flag is additive rather than replacing (appending a browser to a
list rather than setting it), and your default config also bakes in a default browser via the same
mechanism, passing a different browser on the command line can silently run **both** instead of
switching — check your plugin's actual flag semantics before trusting `--browser firefox` really means
"only firefox."

### 5.3 A Dockerized test runner

Package the test suite itself as an image (a Playwright-maintained base image is usually the right
start, pinned to match your installed Playwright version) so CI, and anyone reproducing an issue
locally, run tests from an identical environment rather than "works on my machine." Verify it can reach
your app-under-test container by its Compose network hostname, not `localhost`.

### 5.4 A hosted, accumulating report

If your reporting tool supports a trend/history view across runs (Allure does), wire it to persist that
history somewhere durable between CI runs — a `gh-pages`-style branch works well — rather than
regenerating a report from scratch each time and losing the trend. Verify history genuinely accumulates
by checking the published history data directly after two real runs, not by eyeballing the page once (a
CDN can cache a page just long enough to make "nothing changed" and "it's cached" look identical).

### 5.5 Scheduled regression and a demo-environment smoke check

A full-regression workflow on a schedule, across your full browser matrix, sharded. A separate, much
smaller, serial, non-destructive smoke workflow against any shared/public secondary environment from
Phase 1 — never run parallel or destructive tests there.

### 5.6 A gotcha worth knowing before you hit it: re-running a single CI job

If you ever re-run just one matrix job in a multi-job workflow (because one leg flaked), check whether
your artifact-upload step defaults to refusing to overwrite an artifact of the same name. If it does,
re-running one job after a prior attempt leaves **two** same-named artifacts in that workflow run, and a
downstream job that just downloads "the artifact named X" can silently grab the stale one instead of the
fresh, passing one — making a report or gate look wrong even though the re-run actually succeeded. Set
the upload step to overwrite explicitly so a job re-run really replaces its own prior output.

---

## Phase 6 — Polish

A final audit pass against your own stated rules (no sleeps, no XPath where a web-first locator exists,
no assertions inside page objects, no hard-coded credentials, no dependence on pre-existing data) — grep
for it, don't just trust memory. A short demo clip or GIF showing the flagship hybrid pattern actually
running, built from real screenshots of the real app if you don't have a screen-recorder handy. Status
badges that link to something real, verified to actually resolve before committing them. A clean,
readable commit history — this is itself part of the showcase.

---

## Case study: unblocking the Leave module

A worked example of the discovery habit paying for itself, from this project's own history: the Leave
pages were initially left unbuilt because a fresh seeded instance had no leave type or period configured
— the apply form just showed an error. Unblocking it, in order:

1. **UI exploration first.** Configured a leave period and type by hand through Admin > Leave, to see
   what "working" actually looked like before writing any code against it.
2. **Network-tab capture** of granting a leave entitlement and submitting a leave application, to get
   the real payload shapes for the API client.
3. **An ambiguous result, resolved by going straight to the database.** Two different ways to create a
   leave request — a user applying for themselves, versus an admin assigning leave on someone's behalf
   — looked like they should do the same thing. The UI and API responses alone didn't make it obvious
   that they produce genuinely different outcomes (one lands pending approval, the other auto-schedules
   with nothing left to approve). A direct `SELECT` against the leave table made the status-code
   difference undeniable, and that fact reshaped the test: an approval test needs the self-apply path,
   not the admin-assign path, or there's nothing left to approve.
4. **A second DB check** to figure out why a submitted leave request wasn't showing up in a supervisor's
   approval queue at all — turned out visibility is gated on an explicit supervisor relationship that
   has to be set up first via a separate endpoint, not inferred from org structure.
5. **Baking the one-time config into the seed**, not just the live dev database, so the fix benefits
   every fresh instance (local resets, CI) — then re-verifying against a **genuinely fresh, isolated**
   container built from the updated seed, not just the already-configured dev stack, before trusting it.

None of this sequence is visible in `TODO.md`'s single checked-off line for "Leave pages done." That's
the gap this tutorial exists to fill.

---

## Appendix: environment gotchas worth expecting

- Don't redirect binary/SQL tool output through your shell's `>` on Windows — encoding issues, and it
  won't create missing directories. Use the tool's own `--result-file`/equivalent flag, then copy the
  result out of the container explicitly.
- Git Bash on Windows will mangle an absolute Unix-style path (like `/tmp/...`) passed through to a
  containerized command, rewriting it as a Windows path first. Prefix with `MSYS_NO_PATHCONV=1` when
  that's not what you want, or avoid the absolute path entirely by working inside the repo.
- A port already in use when starting an isolated verification stack almost always means your main dev
  stack is already bound to it — give the verification stack its own project name and a different host
  port rather than tearing down what you're trying to verify against.

---

## What this tutorial still can't give you

It can hand you the order, the patterns, and the specific traps this project hit. It can't hand you the
hours of actually watching a Network tab, trying a payload, getting a 403, and trying again — that part
doesn't compress. Budget for it; it's most of the real work.
