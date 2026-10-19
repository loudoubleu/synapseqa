from pydantic import BaseModel


class BookingIdSummary(BaseModel):
    bookingid: int
