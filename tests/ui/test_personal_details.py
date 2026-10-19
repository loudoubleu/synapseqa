import pytest
from playwright.sync_api import Page, expect

from framework.api.models.employee import Employee
from framework.ui.components.toast import Toast
from framework.ui.pages.pim.personal_details_page import PersonalDetailsPage


@pytest.mark.ui
@pytest.mark.destructive
def test_update_personal_details(admin_page: Page, employee: Employee) -> None:
    admin_page.goto(f"/web/index.php/pim/viewPersonalDetails/empNumber/{employee.emp_number}")
    admin_page.wait_for_load_state("networkidle")

    details = PersonalDetailsPage(admin_page)
    details.date_of_birth.set_date("1990-05-15")
    details.nationality.choose("American")
    details.marital_status.choose("Single")
    details.save_button.click()

    toast = Toast(admin_page)
    expect(toast.root).to_be_visible()
    assert "Successfully Updated" in toast.message
