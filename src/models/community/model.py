"""Phase 9 Step 32 — Community models."""

from dataclasses import dataclass


@dataclass
class CommunitySpace:
    id: str = ""
    org_id: str = ""
    name: str = ""
    slug: str = ""
    description: str = ""
    cover_image_url: str = ""
    icon: str = ""
    space_type: str = "open"
    membership_tier: str = ""
    member_count: int = 0
    post_count: int = 0
    created_by: str = ""
    created_at: str = ""
    updated_at: str = ""

    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        return cls(
            id=row.get("id", ""),
            org_id=row.get("org_id", "") or "",
            name=row.get("name", ""),
            slug=row.get("slug", ""),
            description=row.get("description", "") or "",
            cover_image_url=row.get("cover_image_url", "") or "",
            icon=row.get("icon", "") or "",
            space_type=row.get("space_type", "open") or "open",
            membership_tier=row.get("membership_tier", "") or "",
            member_count=int(row.get("member_count", 0) or 0),
            post_count=int(row.get("post_count", 0) or 0),
            created_by=row.get("created_by", "") or "",
            created_at=row.get("created_at", ""),
            updated_at=row.get("updated_at", "") or "",
        )

    def to_dict(self, scope="default"):
        return {
            "id": self.id,
            "org_id": self.org_id,
            "name": self.name,
            "slug": self.slug,
            "description": self.description,
            "cover_image_url": self.cover_image_url,
            "icon": self.icon,
            "space_type": self.space_type,
            "membership_tier": self.membership_tier,
            "member_count": self.member_count,
            "post_count": self.post_count,
            "created_by": self.created_by,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass
class SpaceMember:
    space_id: str = ""
    user_id: str = ""
    role: str = "member"
    joined_at: str = ""

    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        return cls(
            space_id=row.get("space_id", ""),
            user_id=row.get("user_id", ""),
            role=row.get("role", "member") or "member",
            joined_at=row.get("joined_at", ""),
        )

    def to_dict(self, scope="default"):
        return {
            "space_id": self.space_id,
            "user_id": self.user_id,
            "role": self.role,
            "joined_at": self.joined_at,
        }


@dataclass
class CommunityPost:
    id: str = ""
    space_id: str = ""
    author_id: str = ""
    parent_id: str = ""
    title: str = ""
    body: str = ""
    post_type: str = "discussion"
    article_id: str = ""
    status: str = "published"
    pinned: bool = False
    reply_count: int = 0
    like_count: int = 0
    view_count: int = 0
    created_at: str = ""
    updated_at: str = ""

    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        return cls(
            id=row.get("id", ""),
            space_id=row.get("space_id", ""),
            author_id=row.get("author_id", ""),
            parent_id=row.get("parent_id", "") or "",
            title=row.get("title", "") or "",
            body=row.get("body", ""),
            post_type=row.get("post_type", "discussion") or "discussion",
            article_id=row.get("article_id", "") or "",
            status=row.get("status", "published") or "published",
            pinned=bool(row.get("pinned", 0)),
            reply_count=int(row.get("reply_count", 0) or 0),
            like_count=int(row.get("like_count", 0) or 0),
            view_count=int(row.get("view_count", 0) or 0),
            created_at=row.get("created_at", ""),
            updated_at=row.get("updated_at", "") or "",
        )

    def to_dict(self, scope="default"):
        return {
            "id": self.id,
            "space_id": self.space_id,
            "author_id": self.author_id,
            "parent_id": self.parent_id,
            "title": self.title,
            "body": self.body,
            "post_type": self.post_type,
            "article_id": self.article_id,
            "status": self.status,
            "pinned": self.pinned,
            "reply_count": self.reply_count,
            "like_count": self.like_count,
            "view_count": self.view_count,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
