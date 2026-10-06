from enum import Enum

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

# коды согласий, которые пользователь даёт при регистрации
class ConsentCode(str, Enum):
    PERSONAL_DATA = "PERSONAL_DATA"
    MARKETING = "MARKETING"
    ANALYTICS = "ANALYTICS"

class ConsentItem(BaseModel):
    code: ConsentCode = Field(
        ...,
        examples=["PERSONAL_DATA"],
    )
    is_accepted: bool = Field(
        ...,
        examples=[True],
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

# имя и телефон обязательны при регистрации, согласия проверяются сервисом
class RegisterRequest(BaseAuthRequest):
    name: str = Field(
        ...,
        min_length=1,
        max_length=64,
        pattern=r"^[A-Za-zА-Яа-яЁё][A-Za-zА-Яа-яЁё \-]*$",
        examples=['Иван'],
    )
    phone: str = Field(
        ...,
        min_length=11,
        max_length=20,
        pattern=r"^\+?[\d\s()\-]+$",
        examples=['+7 (999) 000-00-01'],
    )
    consents: list[ConsentItem] = Field(
        ...,
        min_length=1,
        max_length=len(ConsentCode),
        examples=[[{"code": "PERSONAL_DATA", "is_accepted": True}]],
    )

class BaseAuthResponse(BaseModel):
    success: bool = Field(
        examples=["true"],
    )