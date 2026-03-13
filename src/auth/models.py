from dataclasses import dataclass
from typing import Optional


@dataclass
class User:
    id: str
    email: str
    name: str
    role: str
    avatar_url: Optional[str] = None
    google_id: Optional[str] = None
    is_active: int = 1
