from framework.api.base_client import BaseClient
from framework.api.models.employee import EmployeeListResponse


class EmployeeClient(BaseClient):
    base_path = "/web/index.php/api/v2/pim/employees"

    def list(self, *, limit: int = 50) -> EmployeeListResponse:
        response = self.get(self.base_path, params={"limit": limit})
        return EmployeeListResponse.model_validate(response.json())
