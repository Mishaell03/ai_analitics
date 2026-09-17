from pydantic import BaseModel, Field

# locale base models
class _AuthData(BaseModel):
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
    language: str = Field(
        ...,
        pattern=r"^[a-z]{2,3}$",
        max_length=3,
        examples=["ru"],
    )

# register && login with only password and email + base data for reg
class BaseAuthRequest(_AuthData):
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
        pattern=r'^[A-Za-z0-9!@#$%^&*()_+\-=\[\]{};:,.<>?/\\|~`]*$',
        examples=['Qwery123@']
    )

class BaseAuthResponse(BaseModel):
    session: str = Field(
        examples=["session"],
    )
