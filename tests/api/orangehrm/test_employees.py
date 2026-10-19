import pytest

from framework.api.clients.employee_client import EmployeeClient


@pytest.mark.smoke
@pytest.mark.api
def test_list_employees_returns_valid_schema(employee_client: EmployeeClient) -> None:
    employees = employee_client.list(limit=5)
    assert employees.meta.total >= 1
    assert len(employees.data) >= 1
    assert employees.data[0].emp_number > 0
