from typing import Any

from playwright.sync_api import APIResponse

from framework.api.base_client import BaseClient
from framework.api.models.booking import Booking, BookingIdSummary, CreatedBooking


class BookingClient(BaseClient):
    base_path = "/booking"

    def authenticate(self, username: str, password: str) -> str | None:
        response = self.post("/auth", data={"username": username, "password": password})
        body: dict[str, Any] = response.json()
        token = body.get("token")
        return token if isinstance(token, str) else None

    def list_booking_ids(self) -> list[BookingIdSummary]:
        response = self.get(self.base_path)
        return [BookingIdSummary.model_validate(item) for item in response.json()]

    def create_booking(
        self,
        *,
        firstname: str,
        lastname: str,
        totalprice: int,
        depositpaid: bool,
        checkin: str,
        checkout: str,
        additionalneeds: str | None = None,
    ) -> CreatedBooking:
        payload: dict[str, Any] = {
            "firstname": firstname,
            "lastname": lastname,
            "totalprice": totalprice,
            "depositpaid": depositpaid,
            "bookingdates": {"checkin": checkin, "checkout": checkout},
        }
        if additionalneeds is not None:
            payload["additionalneeds"] = additionalneeds
        response = self.post(self.base_path, data=payload)
        return CreatedBooking.model_validate(response.json())

    def get_booking(self, booking_id: int) -> APIResponse:
        return self.get(f"{self.base_path}/{booking_id}")

    def update_booking(
        self,
        booking_id: int,
        token: str,
        *,
        firstname: str,
        lastname: str,
        totalprice: int,
        depositpaid: bool,
        checkin: str,
        checkout: str,
        additionalneeds: str | None = None,
    ) -> Booking:
        payload: dict[str, Any] = {
            "firstname": firstname,
            "lastname": lastname,
            "totalprice": totalprice,
            "depositpaid": depositpaid,
            "bookingdates": {"checkin": checkin, "checkout": checkout},
        }
        if additionalneeds is not None:
            payload["additionalneeds"] = additionalneeds
        response = self.put(
            f"{self.base_path}/{booking_id}", data=payload, headers={"Cookie": f"token={token}"}
        )
        return Booking.model_validate(response.json())

    def partial_update_booking(self, booking_id: int, token: str, **fields: Any) -> Booking:
        response = self.patch(
            f"{self.base_path}/{booking_id}", data=fields, headers={"Cookie": f"token={token}"}
        )
        return Booking.model_validate(response.json())

    def delete_booking(self, booking_id: int, token: str) -> APIResponse:
        return self.delete_json(f"{self.base_path}/{booking_id}", headers={"Cookie": f"token={token}"})
