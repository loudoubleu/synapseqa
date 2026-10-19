import sys
from collections.abc import Iterator
from pathlib import Path

import pytest
from playwright.sync_api import Browser, BrowserContext, Page, Playwright, expect

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "infra"))
from wait_for_ready import NotInstalledError, wait_for_ready  # type: ignore[import-not-found]

from framework.api.clients.booking_client import BookingClient
from framework.api.clients.employee_client import EmployeeClient
from framework.api.clients.user_client import UserClient
from framework.api.models.employee import Employee
from framework.config.settings import Settings
from framework.data.builders import EmployeeBuilder
from framework.ui.pages.login_page import LoginPage

AUTH_DIR = Path(__file__).resolve().parent.parent / ".auth"
ADMIN_STORAGE_STATE_PATH = AUTH_DIR / "admin_state.json"


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


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    settings = Settings()
    if not settings.is_shared_env:
        return
    skip_destructive = pytest.mark.skip(reason="destructive tests are skipped against the shared demo env")
    for item in items:
        if "destructive" in item.keywords:
            item.add_marker(skip_destructive)
