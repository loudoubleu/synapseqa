from pydantic import BaseModel, ConfigDict, Field


class Employee(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    emp_number: int = Field(alias="empNumber")
    first_name: str = Field(alias="firstName")
    last_name: str = Field(alias="lastName")
    middle_name: str = Field(alias="middleName", default="")
    employee_id: str | None = Field(alias="employeeId", default=None)
    termination_id: int | None = Field(alias="terminationId", default=None)


class EmployeeListMeta(BaseModel):
    total: int


class EmployeeListResponse(BaseModel):
    data: list[Employee]
    meta: EmployeeListMeta


class EmployeeResponse(BaseModel):
    data: Employee


class EmployeeDeleteResponse(BaseModel):
    data: list[int]
