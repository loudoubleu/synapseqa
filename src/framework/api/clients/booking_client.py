from typing import Any

from framework.api.base_client import BaseClient
from framework.api.models.booking import BookingIdSummary


class BookingClient(BaseClient):
    def authenticate(self, username: str, password: str) -> str | None:
        response = self.post("/auth", data={"username": username, "password": password})
        body: dict[str, Any] = response.json()
        token = body.get("token")
        return token if isinstance(token, str) else None

    def list_booking_ids(self) -> list[BookingIdSummary]:
        response = self.get("/booking")
        return [BookingIdSummary.model_validate(item) for item in response.json()]
