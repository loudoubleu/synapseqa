from pydantic import BaseModel


class BookingIdSummary(BaseModel):
    bookingid: int


class BookingDates(BaseModel):
    checkin: str
    checkout: str


class Booking(BaseModel):
    firstname: str
    lastname: str
    totalprice: int
    depositpaid: bool
    bookingdates: BookingDates
    additionalneeds: str | None = None


class CreatedBooking(BaseModel):
    bookingid: int
    booking: Booking
