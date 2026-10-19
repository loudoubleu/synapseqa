import pytest

from framework.api.clients.user_client import ESS_ROLE_ID, UserClient
from framework.api.models.common import ErrorResponse
from framework.api.models.employee import Employee
from framework.data.builders import UserBuilder


@pytest.mark.api
@pytest.mark.destructive
def test_create_get_delete_user_round_trip(user_client: UserClient, employee: Employee) -> None:
    builder = UserBuilder()
    created = user_client.create(
        username=builder.username,
        password=builder.password,
        user_role_id=ESS_ROLE_ID,
        emp_number=employee.emp_number,
        status=builder.status,
    )
    assert created.user_name == builder.username
    assert created.user_role.id == ESS_ROLE_ID
    assert created.employee.emp_number == employee.emp_number

    fetched = user_client.get_by_id(created.id)
    assert fetched.id == created.id

    deleted_ids = user_client.delete(created.id)
    assert deleted_ids == [created.id]


@pytest.mark.api
@pytest.mark.destructive
def test_create_user_with_weak_password_is_rejected(user_client: UserClient, employee: Employee) -> None:
    response = user_client.post(
        user_client.base_path,
        data={
            "username": "auto_weak_pw_probe",
            "password": "weak",
            "userRoleId": ESS_ROLE_ID,
            "empNumber": employee.emp_number,
            "status": True,
        },
    )
    assert response.status == 422

    error = ErrorResponse.model_validate(response.json())
    assert error.error.data is not None
    assert "password" in error.error.data.invalid_param_keys
