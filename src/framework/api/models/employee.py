from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class Employee(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    emp_number: int = Field(alias="empNumber")
    first_name: str = Field(alias="firstName")
    last_name: str = Field(alias="lastName")
    middle_name: str = Field(alias="middleName", default="")
    employee_id: str = Field(alias="employeeId")
    termination_id: int | None = Field(alias="terminationId", default=None)


class EmployeeListMeta(BaseModel):
    total: int


class EmployeeListResponse(BaseModel):
    data: list[Employee]
    meta: EmployeeListMeta
    rels: list[Any] = Field(default_factory=list)
