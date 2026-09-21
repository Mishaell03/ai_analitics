from datetime import datetime
from pydantic import BaseModel

class MeResponse(BaseModel):
    name: str | None = None
    phone: str | None = None
    email: str
    img_url: str | None = None
    expires_at: datetime
