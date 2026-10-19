import pytest

from framework.api.clients.employee_client import EmployeeClient
from framework.api.models.common import ErrorResponse
from framework.data.builders import EmployeeBuilder


@pytest.mark.smoke
@pytest.mark.api
def test_list_employees_returns_valid_schema(employee_client: EmployeeClient) -> None:
    employees = employee_client.list_all(limit=5)
    assert employees.meta.total >= 1
    assert len(employees.data) >= 1
    assert employees.data[0].emp_number > 0


@pytest.mark.api
@pytest.mark.destructive
def test_create_update_delete_employee_round_trip(employee_client: EmployeeClient) -> None:
    builder = EmployeeBuilder()
    created = employee_client.create(
        first_name=builder.first_name, last_name=builder.last_name, middle_name=builder.middle_name
    )
    assert created.first_name == builder.first_name
    assert created.last_name == builder.last_name
    assert created.emp_number > 0

    fetched = employee_client.get_by_number(created.emp_number)
    assert fetched.emp_number == created.emp_number
    assert fetched.last_name == builder.last_name

    updated = employee_client.update_personal_details(
        created.emp_number, first_name="Updated", last_name=builder.last_name
    )
    assert updated.first_name == "Updated"
    assert updated.emp_number == created.emp_number

    deleted_ids = employee_client.delete(created.emp_number)
    assert deleted_ids == [created.emp_number]


@pytest.mark.api
@pytest.mark.destructive
def test_create_employee_without_last_name_is_rejected(employee_client: EmployeeClient) -> None:
    response = employee_client.post(employee_client.base_path, data={"firstName": "OnlyFirst"})
    assert response.status == 422

    error = ErrorResponse.model_validate(response.json())
    assert error.error.data is not None
    assert "lastName" in error.error.data.invalid_param_keys
