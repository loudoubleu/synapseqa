import pytest

from framework.api.clients.booking_client import BookingClient


@pytest.mark.smoke
@pytest.mark.api
def test_get_booking_ids_returns_list(booking_client: BookingClient) -> None:
    bookings = booking_client.list_booking_ids()
    assert len(bookings) > 0
    assert all(booking.bookingid > 0 for booking in bookings)


@pytest.mark.smoke
@pytest.mark.api
def test_auth_with_bad_credentials_returns_no_token(booking_client: BookingClient) -> None:
    token = booking_client.authenticate("admin", "not-the-right-password")
    assert token is None
