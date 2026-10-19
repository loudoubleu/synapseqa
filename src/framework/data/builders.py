import uuid
from dataclasses import dataclass, field

from faker import Faker

fake = Faker()


def auto_suffix() -> str:
    return uuid.uuid4().hex[:8]


@dataclass
class EmployeeBuilder:
    first_name: str = field(default_factory=fake.first_name)
    last_name: str = field(default_factory=lambda: f"auto_{auto_suffix()}")
    middle_name: str = ""


@dataclass
class UserBuilder:
    username: str = field(default_factory=lambda: f"auto_{auto_suffix()}")
    password: str = field(
        default_factory=lambda: fake.password(
            length=14, special_chars=True, digits=True, upper_case=True, lower_case=True
        )
    )
    status: bool = True


@dataclass
class BookingBuilder:
    firstname: str = field(default_factory=fake.first_name)
    lastname: str = field(default_factory=lambda: f"auto_{auto_suffix()}")
    totalprice: int = field(default_factory=lambda: fake.random_int(min=50, max=1000))
    depositpaid: bool = True
    checkin: str = field(
        default_factory=lambda: fake.date_between(start_date="+1d", end_date="+10d").isoformat()
    )
    checkout: str = field(
        default_factory=lambda: fake.date_between(start_date="+11d", end_date="+20d").isoformat()
    )
    additionalneeds: str = field(default_factory=fake.word)
