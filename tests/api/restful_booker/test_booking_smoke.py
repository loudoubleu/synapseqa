import pytest

from framework.api.clients.booking_client import BookingClient
from framework.data.builders import BookingBuilder


@pytest.mark.smoke
@pytest.mark.api
@pytest.mark.destructive
def test_get_booking_ids_returns_list(booking_client: BookingClient, auth_token: str) -> None:
    # Don't rely on the shared public demo already having bookings (CLAUDE.md §7: its storage
    # is ephemeral/shared) -- create one so this test is self-contained, like every other test.
    builder = BookingBuilder()
    created = booking_client.create_booking(
        firstname=builder.firstname,
        lastname=builder.lastname,
        totalprice=builder.totalprice,
        depositpaid=builder.depositpaid,
        checkin=builder.checkin,
        checkout=builder.checkout,
    )

    bookings = booking_client.list_booking_ids()

    assert any(booking.bookingid == created.bookingid for booking in bookings)
    booking_client.delete_booking(created.bookingid, auth_token)


@pytest.mark.smoke
@pytest.mark.api
def test_auth_with_bad_credentials_returns_no_token(booking_client: BookingClient) -> None:
    token = booking_client.authenticate("admin", "not-the-right-password")
    assert token is None
