from enum import StrEnum


class Role(StrEnum):
    ADMIN = "Admin"
    ESS = "ESS"


# Confirmed against the running app (CLAUDE.md §7): Admin sees every module; ESS is
# restricted to the employee self-service modules (no Admin, PIM, Recruitment, Maintenance).
EXPECTED_MENU: dict[Role, set[str]] = {
    Role.ADMIN: {
        "Admin",
        "PIM",
        "Leave",
        "Time",
        "Recruitment",
        "My Info",
        "Performance",
        "Dashboard",
        "Directory",
        "Maintenance",
        "Claim",
        "Buzz",
    },
    Role.ESS: {
        "Leave",
        "Time",
        "My Info",
        "Performance",
        "Dashboard",
        "Directory",
        "Claim",
        "Buzz",
    },
}
