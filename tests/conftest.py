import os
import sys
from collections.abc import Generator, Iterator
from pathlib import Path

import allure
import pytest
from playwright.sync_api import Browser, BrowserContext, Page, Playwright, expect
from pluggy import Result

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "infra"))
from wait_for_ready import NotInstalledError, wait_for_ready  # type: ignore[import-not-found]

from framework.api.clients.booking_client import BookingClient
from framework.api.clients.employee_client import EmployeeClient
from framework.api.clients.leave_client import LeaveClient
from framework.api.clients.user_client import ESS_ROLE_ID, UserClient
from framework.api.models.employee import Employee
from framework.auth.roles import Role
from framework.config.settings import Settings
from framework.data.builders import EmployeeBuilder, UserBuilder
from framework.ui.pages.login_page import LoginPage

# xdist gives each worker its own session scope, so session-scoped fixtures that write to
# a shared path (admin/ESS storage_state) need a worker-unique filename, or parallel workers
# can read a half-written file from another worker.
WORKER_ID = os.environ.get("PYTEST_XDIST_WORKER", "master")
AUTH_DIR = Path(__file__).resolve().parent.parent / ".auth"
ADMIN_STORAGE_STATE_PATH = AUTH_DIR / f"admin_state.{WORKER_ID}.json"
ESS_STORAGE_STATE_PATH = AUTH_DIR / f"ess_state.{WORKER_ID}.json"


@pytest.fixture(scope="session")
def settings() -> Settings:
    return Settings()


@pytest.fixture(scope="session")
def base_url(settings: Settings) -> str:
    return str(settings.orangehrm_url)


@pytest.fixture(scope="session", autouse=True)
def _ensure_orangehrm_ready(settings: Settings) -> None:
    if settings.is_shared_env:
        return
    try:
        ready = wait_for_ready(str(settings.orangehrm_url), timeout=180.0, interval=3.0)
    except NotInstalledError as exc:
        pytest.exit(str(exc), returncode=2)
    if not ready:
        pytest.exit(f"OrangeHRM was not ready at {settings.orangehrm_url}", returncode=1)


@pytest.fixture
def context(context: BrowserContext, settings: Settings) -> BrowserContext:
    context.set_default_timeout(settings.default_timeout_ms)
    return context


@pytest.fixture(scope="session")
def admin_storage_state(browser: Browser, settings: Settings, base_url: str) -> Path:
    AUTH_DIR.mkdir(parents=True, exist_ok=True)
    login_context = browser.new_context(base_url=base_url)
    login_page = LoginPage(login_context.new_page()).open()
    dashboard = login_page.login(settings.admin_username, settings.admin_password.get_secret_value())
    expect(dashboard.heading).to_be_visible()
    login_context.storage_state(path=ADMIN_STORAGE_STATE_PATH)
    login_context.close()
    return ADMIN_STORAGE_STATE_PATH


@pytest.fixture
def admin_page(
    browser: Browser, admin_storage_state: Path, settings: Settings, base_url: str
) -> Iterator[Page]:
    context = browser.new_context(base_url=base_url, storage_state=admin_storage_state)
    context.set_default_timeout(settings.default_timeout_ms)
    page = context.new_page()
    yield page
    context.close()


@pytest.fixture(scope="session")
def ess_storage_state(
    playwright: Playwright, browser: Browser, base_url: str, admin_storage_state: Path
) -> Iterator[Path]:
    AUTH_DIR.mkdir(parents=True, exist_ok=True)
    api_context = playwright.request.new_context(base_url=base_url, storage_state=admin_storage_state)
    employee_api = EmployeeClient(api_context, base_url)
    user_api = UserClient(api_context, base_url)

    emp_builder = EmployeeBuilder()
    emp = employee_api.create(first_name=emp_builder.first_name, last_name=emp_builder.last_name)
    user_builder = UserBuilder()
    user = user_api.create(
        username=user_builder.username,
        password=user_builder.password,
        user_role_id=ESS_ROLE_ID,
        emp_number=emp.emp_number,
    )

    login_context = browser.new_context(base_url=base_url)
    login_page = LoginPage(login_context.new_page()).open()
    dashboard = login_page.login(user.user_name, user_builder.password)
    expect(dashboard.heading).to_be_visible()
    login_context.storage_state(path=ESS_STORAGE_STATE_PATH)
    login_context.close()

    yield ESS_STORAGE_STATE_PATH

    user_api.delete(user.id)
    employee_api.delete(emp.emp_number)
    api_context.dispose()


@pytest.fixture
def ess_page(browser: Browser, ess_storage_state: Path, settings: Settings, base_url: str) -> Iterator[Page]:
    context = browser.new_context(base_url=base_url, storage_state=ess_storage_state)
    context.set_default_timeout(settings.default_timeout_ms)
    page = context.new_page()
    yield page
    context.close()


@pytest.fixture
def role(request: pytest.FixtureRequest) -> Role:
    role_param: Role = request.param
    return role_param


@pytest.fixture
def logged_in_as(
    role: Role,
    browser: Browser,
    settings: Settings,
    base_url: str,
    admin_storage_state: Path,
    ess_storage_state: Path,
) -> Iterator[Page]:
    storage_state = admin_storage_state if role is Role.ADMIN else ess_storage_state
    context = browser.new_context(base_url=base_url, storage_state=storage_state)
    context.set_default_timeout(settings.default_timeout_ms)
    page = context.new_page()
    page.goto("/web/index.php/dashboard/index")
    page.wait_for_load_state("networkidle")
    yield page
    context.close()


@pytest.fixture
def employee_client(
    playwright: Playwright, admin_storage_state: Path, base_url: str
) -> Iterator[EmployeeClient]:
    request_context = playwright.request.new_context(base_url=base_url, storage_state=admin_storage_state)
    yield EmployeeClient(request_context, base_url)
    request_context.dispose()


@pytest.fixture
def user_client(playwright: Playwright, admin_storage_state: Path, base_url: str) -> Iterator[UserClient]:
    request_context = playwright.request.new_context(base_url=base_url, storage_state=admin_storage_state)
    yield UserClient(request_context, base_url)
    request_context.dispose()


@pytest.fixture
def leave_client(playwright: Playwright, admin_storage_state: Path, base_url: str) -> Iterator[LeaveClient]:
    request_context = playwright.request.new_context(base_url=base_url, storage_state=admin_storage_state)
    yield LeaveClient(request_context, base_url)
    request_context.dispose()


@pytest.fixture
def employee(employee_client: EmployeeClient) -> Iterator[Employee]:
    builder = EmployeeBuilder()
    created = employee_client.create(
        first_name=builder.first_name, last_name=builder.last_name, middle_name=builder.middle_name
    )
    yield created
    employee_client.delete(created.emp_number)


@pytest.fixture
def booking_client(playwright: Playwright, settings: Settings) -> Iterator[BookingClient]:
    booker_url = str(settings.booker_api_url)
    request_context = playwright.request.new_context(base_url=booker_url)
    yield BookingClient(request_context, booker_url)
    request_context.dispose()


@pytest.fixture
def auth_token(booking_client: BookingClient) -> str:
    # Restful Booker's own publicly documented demo credentials (not a project secret) --
    # there's no self-hosted alternative to this third-party service, so there's nothing to
    # read from config here.
    token = booking_client.authenticate("admin", "password123")
    assert token is not None
    return token


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(
    item: pytest.Item, call: pytest.CallInfo[None]
) -> Generator[None, Result[pytest.TestReport], None]:
    outcome = yield
    report = outcome.get_result()
    if report.when == "call" and report.failed and isinstance(item, pytest.Function):
        page = next((v for v in item.funcargs.values() if isinstance(v, Page)), None)
        if page is not None:
            allure.attach(
                page.screenshot(), name="failure-screenshot", attachment_type=allure.attachment_type.PNG
            )


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    settings = Settings()
    if not settings.is_shared_env:
        return
    skip_destructive = pytest.mark.skip(reason="destructive tests are skipped against the shared demo env")
    for item in items:
        if "destructive" in item.keywords:
            item.add_marker(skip_destructive)
