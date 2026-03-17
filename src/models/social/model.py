from dataclasses import dataclass
from datetime import datetime
from models.base import BaseModel


@dataclass
class SocialActionResult(BaseModel):
    """Result of a social action (like, bookmark, follow)."""

    action: str  # 'like' or 'bookmark' or 'follow'
    target_id: str  # article_id or user_id
    active: bool  # True=added the action, False=removed the action

    def to_dict(self) -> dict:
        return {
            "action": self.action,
            "target_id": self.target_id,
            "active": self.active,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }


@dataclass
class UserFollowStats(BaseModel):
    """Social statistics for a user."""

    user_id: str
    followers_count: int = 0
    following_count: int = 0
    total_likes_given: int = 0
    total_articles_liked: int = 0
    total_bookmarks: int = 0

    def to_dict(self) -> dict:
        return {
            "user_id": self.user_id,
            "followers_count": self.followers_count,
            "following_count": self.following_count,
            "total_likes_given": self.total_likes_given,
            "total_articles_liked": self.total_articles_liked,
            "total_bookmarks": self.total_bookmarks,
        }
