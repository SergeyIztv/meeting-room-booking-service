from datetime import time

from pydantic import BaseModel


class SlotResponse(BaseModel):
    id: int
    start_time: time
    end_time: time
    is_available: bool | None = None
    booked_by: str | None = None

    model_config = {"from_attributes": True}
