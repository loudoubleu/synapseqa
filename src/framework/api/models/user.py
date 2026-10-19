from pydantic import BaseModel, ConfigDict, Field

from framework.api.models.employee import Employee


class UserRole(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: int
    name: str
    display_name: str = Field(alias="displayName")


class User(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: int
    user_name: str = Field(alias="userName")
    deleted: bool
    status: bool
    employee: Employee
    user_role: UserRole = Field(alias="userRole")


class UserListMeta(BaseModel):
    total: int


class UserListResponse(BaseModel):
    data: list[User]
    meta: UserListMeta


class UserResponse(BaseModel):
    data: User


class UserDeleteResponse(BaseModel):
    data: list[int]
