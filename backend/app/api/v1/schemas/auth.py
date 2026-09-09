from pydantic import BaseModel, Field

class BaseRegisterRequest(BaseModel):
    device_id: str = Field(
        ...,
        pattern=r'^[a-zA-Z0-9_-]+$',
        min_length=8,
        max_length=64,
        examples=["device_abc123"],
    )
    device_name: str = Field(
        ...,
        pattern=r'^[a-zA-Z0-9_-]+$',
        min_length=3,
        max_length=32,
        examples=["Chrome"],
    )
    email: str = Field(
        ...,
        min_length=5,
        max_length=250,
        pattern=r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$",
        examples=['user@user.ru'],
    )
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        pattern=r'^[A-Za-z0-9!@#$%^&*()_+\-=\[\]{};:,.<>?/\\|~`]+$',
        examples=['Qwery123@']
    )
    language: str = Field(
        ...,
        pattern=r"^[a-z]{2,3}$",
        max_length=3,
        examples=["ru"],
    )

class BaseRegisterResponse(BaseModel):
    session: str = Field(
        examples=["session"],
    )
