from dataclasses import dataclass

@dataclass
class BaseAuthContext:
    device_id: str
    user_id: int
    session_id: int
    session: str