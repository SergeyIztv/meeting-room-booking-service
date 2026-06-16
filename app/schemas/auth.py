from pydantic import BaseModel


class PromoteRequest(BaseModel):
    user_id: int
