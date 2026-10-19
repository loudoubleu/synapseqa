import base64
from pathlib import Path

import pytest
from playwright.sync_api import Page, expect

from framework.api.clients.employee_client import EmployeeClient
from framework.data.builders import EmployeeBuilder
from framework.ui.pages.pim.add_employee_page import AddEmployeePage

TINY_PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
)


@pytest.fixture
def tiny_photo(tmp_path: Path) -> Path:
    photo_path = tmp_path / "avatar.png"
    photo_path.write_bytes(TINY_PNG)
    return photo_path


@pytest.mark.ui
@pytest.mark.destructive
def test_add_employee_with_photo(admin_page: Page, employee_client: EmployeeClient, tiny_photo: Path) -> None:
    builder = EmployeeBuilder()
    add_page = AddEmployeePage(admin_page).open()
    add_page.fill_name(first_name=builder.first_name, last_name=builder.last_name)
    add_page.upload_photo(str(tiny_photo))
    personal_details = add_page.save()

    expect(personal_details.page.get_by_role("heading", name="Personal Details")).to_be_visible()
    emp_number = int(personal_details.page.url.rstrip("/").split("/")[-1])
    fetched = employee_client.get_by_number(emp_number)
    assert fetched.first_name == builder.first_name
    employee_client.delete(emp_number)
