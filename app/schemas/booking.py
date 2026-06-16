from datetime import date, datetime

from pydantic import BaseModel


class BookingCreate(BaseModel):
    room_id: int
    slot_id: int
    date: date


class BookingResponse(BaseModel):
    id: int
    user_id: int
    room_id: int
    slot_id: int
    date: date
    created_at: datetime

    model_config = {"from_attributes": True}
