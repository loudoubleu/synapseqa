from framework.api.base_client import BaseClient
from framework.api.models.leave import (
    AppliedLeave,
    LeaveApplyResponse,
    LeaveEntitlement,
    LeaveEntitlementResponse,
    LeaveType,
    LeaveTypeListResponse,
)

# Seeded into infra/seed/orangehrm.sql (Leave Period Jan 1 - Dec 31, this one Leave Type) so every
# fresh instance -- local or CI -- has a usable Leave module out of the box. Confirmed against the
# running app before seeding: a fresh instance has neither configured, and /leave/applyLeave shows
# "No Leave Types with Leave Balance" until both exist plus a per-employee entitlement.
ANNUAL_LEAVE_TYPE_ID = 1


class LeaveClient(BaseClient):
    types_path = "/web/index.php/api/v2/leave/leave-types"
    entitlements_path = "/web/index.php/api/v2/leave/leave-entitlements"
    self_apply_path = "/web/index.php/api/v2/leave/leave-requests"
    assign_path = "/web/index.php/api/v2/leave/employees/leave-requests"

    def list_types(self) -> list[LeaveType]:
        response = self.get(self.types_path)
        return LeaveTypeListResponse.model_validate(response.json()).data

    def grant_entitlement(
        self, *, emp_number: int, leave_type_id: int, from_date: str, to_date: str, days: float
    ) -> LeaveEntitlement:
        response = self.post(
            self.entitlements_path,
            data={
                "empNumber": emp_number,
                "leaveTypeId": leave_type_id,
                "fromDate": from_date,
                "toDate": to_date,
                "entitlement": str(days),
            },
        )
        return LeaveEntitlementResponse.model_validate(response.json()).data

    def apply(
        self, *, leave_type_id: int, from_date: str, to_date: str, comment: str | None = None
    ) -> AppliedLeave:
        """Self-apply: uses whichever authenticated session this client was built from.

        Lands as status "Pending Approval" -- unlike assign(), which auto-schedules (confirmed
        against the running app: an admin assigning leave on an employee's behalf resolves it
        immediately, with nothing left to approve).
        """
        response = self.post(
            self.self_apply_path,
            data={
                "leaveTypeId": leave_type_id,
                "fromDate": from_date,
                "toDate": to_date,
                "comment": comment,
                "duration": {"type": "full_day"},
            },
        )
        return LeaveApplyResponse.model_validate(response.json()).data

    def assign(
        self,
        *,
        emp_number: int,
        leave_type_id: int,
        from_date: str,
        to_date: str,
        comment: str | None = None,
    ) -> AppliedLeave:
        response = self.post(
            self.assign_path,
            data={
                "leaveTypeId": leave_type_id,
                "fromDate": from_date,
                "toDate": to_date,
                "comment": comment,
                "empNumber": emp_number,
                "duration": {"type": "full_day"},
            },
        )
        return LeaveApplyResponse.model_validate(response.json()).data

    def approve(self, leave_request_id: int) -> None:
        self.put(f"{self.assign_path}/{leave_request_id}", data={"action": "APPROVE"})

    def reject(self, leave_request_id: int) -> None:
        self.put(f"{self.assign_path}/{leave_request_id}", data={"action": "REJECT"})
