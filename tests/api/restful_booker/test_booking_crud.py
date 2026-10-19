import time
from collections.abc import Iterator

import pytest

from framework.api.clients.booking_client import BookingClient
from framework.api.models.booking import CreatedBooking
from framework.data.builders import BookingBuilder

BOOKER_USERNAME = "admin"
BOOKER_PASSWORD = "password123"


@pytest.fixture
def auth_token(booking_client: BookingClient) -> str:
    token = booking_client.authenticate(BOOKER_USERNAME, BOOKER_PASSWORD)
    assert token is not None
    return token


@pytest.fixture
def booking(booking_client: BookingClient, auth_token: str) -> Iterator[CreatedBooking]:
    builder = BookingBuilder()
    created = booking_client.create_booking(
        firstname=builder.firstname,
        lastname=builder.lastname,
        totalprice=builder.totalprice,
        depositpaid=builder.depositpaid,
        checkin=builder.checkin,
        checkout=builder.checkout,
        additionalneeds=builder.additionalneeds,
    )
    yield created
    booking_client.delete_booking(created.bookingid, auth_token)


@pytest.mark.api
@pytest.mark.destructive
def test_booking_crud_round_trip(booking_client: BookingClient, auth_token: str) -> None:
    builder = BookingBuilder()
    created = booking_client.create_booking(
        firstname=builder.firstname,
        lastname=builder.lastname,
        totalprice=builder.totalprice,
        depositpaid=builder.depositpaid,
        checkin=builder.checkin,
        checkout=builder.checkout,
        additionalneeds=builder.additionalneeds,
    )
    assert created.booking.firstname == builder.firstname
    assert created.bookingid > 0

    fetched = booking_client.get_booking(created.bookingid)
    assert fetched.status == 200
    assert fetched.json()["lastname"] == builder.lastname

    updated = booking_client.update_booking(
        created.bookingid,
        auth_token,
        firstname="Updated",
        lastname=builder.lastname,
        totalprice=builder.totalprice,
        depositpaid=builder.depositpaid,
        checkin=builder.checkin,
        checkout=builder.checkout,
    )
    assert updated.firstname == "Updated"

    patched = booking_client.partial_update_booking(
        created.bookingid, auth_token, additionalneeds="Late checkout"
    )
    assert patched.additionalneeds == "Late checkout"

    delete_response = booking_client.delete_booking(created.bookingid, auth_token)
    assert delete_response.status == 201

    confirm = booking_client.get_booking(created.bookingid)
    assert confirm.status == 404


@pytest.mark.api
def test_update_booking_without_auth_is_forbidden(
    booking_client: BookingClient, booking: CreatedBooking
) -> None:
    response = booking_client.put(
        f"{booking_client.base_path}/{booking.bookingid}",
        data={
            "firstname": "Nope",
            "lastname": "Nope",
            "totalprice": 1,
            "depositpaid": False,
            "bookingdates": {"checkin": "2026-01-01", "checkout": "2026-01-02"},
        },
    )
    assert response.status == 403


@pytest.mark.api
def test_delete_booking_without_auth_is_forbidden(
    booking_client: BookingClient, booking: CreatedBooking
) -> None:
    response = booking_client.delete_json(f"{booking_client.base_path}/{booking.bookingid}")
    assert response.status == 403


@pytest.mark.api
def test_create_booking_missing_required_fields_returns_server_error(
    booking_client: BookingClient,
) -> None:
    # Restful Booker is known to respond 500 (not a clean 4xx) when required fields are
    # missing entirely — documented here rather than treated as our bug.
    response = booking_client.post(booking_client.base_path, data={"firstname": "OnlyFirst"})
    assert response.status == 500


@pytest.mark.api
@pytest.mark.destructive
def test_create_booking_with_boundary_values_is_accepted(
    booking_client: BookingClient, auth_token: str
) -> None:
    created = booking_client.create_booking(
        firstname="",
        lastname="",
        totalprice=0,
        depositpaid=False,
        checkin="2026-01-01",
        checkout="2026-01-02",
    )
    assert created.booking.totalprice == 0
    booking_client.delete_booking(created.bookingid, auth_token)


@pytest.mark.api
@pytest.mark.destructive
@pytest.mark.parametrize(
    ("depositpaid", "additionalneeds"),
    [
        (True, "Breakfast"),
        (False, None),
    ],
)
def test_create_booking_data_driven_variants(
    booking_client: BookingClient, auth_token: str, depositpaid: bool, additionalneeds: str | None
) -> None:
    builder = BookingBuilder()
    created = booking_client.create_booking(
        firstname=builder.firstname,
        lastname=builder.lastname,
        totalprice=builder.totalprice,
        depositpaid=depositpaid,
        checkin=builder.checkin,
        checkout=builder.checkout,
        additionalneeds=additionalneeds,
    )
    assert created.booking.depositpaid == depositpaid
    assert created.booking.additionalneeds == additionalneeds
    booking_client.delete_booking(created.bookingid, auth_token)


@pytest.mark.api
def test_list_bookings_responds_within_threshold(booking_client: BookingClient) -> None:
    start = time.monotonic()
    booking_client.list_booking_ids()
    elapsed = time.monotonic() - start
    assert elapsed < 5.0
