from datetime import datetime
from pydantic import BaseModel, EmailStr

class MeResponse(BaseModel):
    name: str | None = None
    phone: str | None = None
    email: str
    img_url: str | None = None
    is_admin: bool | None = None
    expires_at: datetime

class MeUpdateRequest(BaseModel):
    name: str | None = None
    phone: str | None = None
    email: EmailStr | None = None
