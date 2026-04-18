"""Phase 9 Step 35 — Podcast models."""

from dataclasses import dataclass


@dataclass
class PodcastShow:
    id: str = ""
    owner_id: str = ""
    org_id: str = ""
    title: str = ""
    slug: str = ""
    description: str = ""
    cover_image_url: str = ""
    rss_feed_url: str = ""
    created_at: str = ""

    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        return cls(
            id=row.get("id", ""),
            owner_id=row.get("owner_id", ""),
            org_id=row.get("org_id", "") or "",
            title=row.get("title", ""),
            slug=row.get("slug", ""),
            description=row.get("description", "") or "",
            cover_image_url=row.get("cover_image_url", "") or "",
            rss_feed_url=row.get("rss_feed_url", "") or "",
            created_at=row.get("created_at", ""),
        )

    def to_dict(self, scope="default"):
        return {
            "id": self.id,
            "owner_id": self.owner_id,
            "org_id": self.org_id,
            "title": self.title,
            "slug": self.slug,
            "description": self.description,
            "cover_image_url": self.cover_image_url,
            "rss_feed_url": self.rss_feed_url,
            "created_at": self.created_at,
        }


@dataclass
class PodcastEpisode:
    id: str = ""
    show_id: str = ""
    title: str = ""
    description: str = ""
    audio_url: str = ""
    duration_seconds: int = 0
    episode_number: int = 0
    transcript_article_id: str = ""
    published_at: str = ""
    created_at: str = ""

    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        return cls(
            id=row.get("id", ""),
            show_id=row.get("show_id", ""),
            title=row.get("title", ""),
            description=row.get("description", "") or "",
            audio_url=row.get("audio_url", ""),
            duration_seconds=int(row.get("duration_seconds", 0) or 0),
            episode_number=int(row.get("episode_number", 0) or 0),
            transcript_article_id=row.get("transcript_article_id", "") or "",
            published_at=row.get("published_at", "") or "",
            created_at=row.get("created_at", ""),
        )

    def to_dict(self, scope="default"):
        return {
            "id": self.id,
            "show_id": self.show_id,
            "title": self.title,
            "description": self.description,
            "audio_url": self.audio_url,
            "duration_seconds": self.duration_seconds,
            "episode_number": self.episode_number,
            "transcript_article_id": self.transcript_article_id,
            "published_at": self.published_at,
            "created_at": self.created_at,
        }
