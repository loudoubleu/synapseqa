from pydantic import BaseModel, ConfigDict, Field


class LeaveType(BaseModel):
    id: int
    name: str


class LeaveTypeListResponse(BaseModel):
    data: list[LeaveType]


class LeaveEntitlement(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: int
    entitlement: float
    days_used: float = Field(alias="daysUsed")


class LeaveEntitlementResponse(BaseModel):
    data: LeaveEntitlement


class AppliedLeave(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: int
    date_applied: str = Field(alias="dateApplied")


class LeaveApplyResponse(BaseModel):
    data: AppliedLeave
