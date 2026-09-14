from datetime import datetime
from pydantic import BaseModel

class MeResponse(BaseModel):
    user_id: int
    name: str | None = None
    phone: str | None = None
    email: str
    img: str | None = None
    is_default_img: bool
    created_at: datetime
    updated_at: datetime
