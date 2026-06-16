import zxcvbn
from pydantic import BaseModel, field_validator, Field


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., max_length=128)

    @field_validator("password")
    @classmethod
    def strong_password(cls, v: str) -> str:
        strength = zxcvbn.zxcvbn(v)
        if strength["score"] < 3:
            warning = strength["feedback"]["warning"]
            suggestions = strength["feedback"]["suggestions"]
            detail = warning or "Password is too weak"
            if suggestions:
                detail += " " + " ".join(suggestions)
            raise ValueError(detail.strip())
        return v


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, json_schema_extra={"example": "ivan"})
    password: str = Field(..., json_schema_extra={"example": "Str0ng!Pass1"})


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: int
    username: str
    role: str

    model_config = {"from_attributes": True}