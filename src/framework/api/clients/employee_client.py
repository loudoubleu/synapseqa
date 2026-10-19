from framework.api.base_client import BaseClient
from framework.api.models.employee import (
    Employee,
    EmployeeDeleteResponse,
    EmployeeListResponse,
    EmployeeResponse,
)


class EmployeeClient(BaseClient):
    base_path = "/web/index.php/api/v2/pim/employees"

    def list_all(self, *, limit: int = 50) -> EmployeeListResponse:
        response = self.get(self.base_path, params={"limit": limit})
        return EmployeeListResponse.model_validate(response.json())

    def create(self, *, first_name: str, last_name: str, middle_name: str = "") -> Employee:
        response = self.post(
            self.base_path,
            data={"firstName": first_name, "lastName": last_name, "middleName": middle_name},
        )
        return EmployeeResponse.model_validate(response.json()).data

    def get_by_number(self, emp_number: int) -> Employee:
        response = self.get(f"{self.base_path}/{emp_number}")
        return EmployeeResponse.model_validate(response.json()).data

    def update_personal_details(
        self, emp_number: int, *, first_name: str, last_name: str, middle_name: str = ""
    ) -> Employee:
        response = self.put(
            f"{self.base_path}/{emp_number}/personal-details",
            data={"firstName": first_name, "lastName": last_name, "middleName": middle_name},
        )
        return EmployeeResponse.model_validate(response.json()).data

    def delete(self, *emp_numbers: int) -> list[int]:
        response = self.delete_json(self.base_path, data={"ids": list(emp_numbers)})
        return EmployeeDeleteResponse.model_validate(response.json()).data
