from pydantic import BaseModel

from app.schemas.slot import SlotResponse


class RoomResponse(BaseModel):
    id: int
    name: str
    description: str | None = None

    model_config = {"from_attributes": True}


class RoomDetailResponse(RoomResponse):
    slots: list[SlotResponse] = []
