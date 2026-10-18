import sys
from pathlib import Path

import pytest
from playwright.sync_api import BrowserContext

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "infra"))
from wait_for_ready import NotInstalledError, wait_for_ready  # type: ignore[import-not-found]

from framework.config.settings import Settings


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


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    settings = Settings()
    if not settings.is_shared_env:
        return
    skip_destructive = pytest.mark.skip(reason="destructive tests are skipped against the shared demo env")
    for item in items:
        if "destructive" in item.keywords:
            item.add_marker(skip_destructive)
