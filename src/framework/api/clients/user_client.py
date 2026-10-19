from framework.api.base_client import BaseClient
from framework.api.models.user import User, UserDeleteResponse, UserListResponse, UserResponse

ADMIN_ROLE_ID = 1
ESS_ROLE_ID = 2


class UserClient(BaseClient):
    base_path = "/web/index.php/api/v2/admin/users"

    def list_all(self, *, limit: int = 50) -> UserListResponse:
        response = self.get(self.base_path, params={"limit": limit})
        return UserListResponse.model_validate(response.json())

    def create(
        self, *, username: str, password: str, user_role_id: int, emp_number: int, status: bool = True
    ) -> User:
        response = self.post(
            self.base_path,
            data={
                "username": username,
                "password": password,
                "userRoleId": user_role_id,
                "empNumber": emp_number,
                "status": status,
            },
        )
        return UserResponse.model_validate(response.json()).data

    def get_by_id(self, user_id: int) -> User:
        response = self.get(f"{self.base_path}/{user_id}")
        return UserResponse.model_validate(response.json()).data

    def delete(self, *user_ids: int) -> list[int]:
        response = self.delete_json(self.base_path, data={"ids": list(user_ids)})
        return UserDeleteResponse.model_validate(response.json()).data
