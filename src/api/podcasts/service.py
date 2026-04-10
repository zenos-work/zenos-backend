"""Phase 9 Step 35 — Podcast service."""

from api.podcasts.repository import PodcastRepository
from utils.helpers import new_id, paginate


class PodcastService:
    def __init__(self, env, ctx=None):
        self._repo = PodcastRepository(env.DB, ctx)

    # ── Shows ────────────────────────────────────────────────
    async def list_shows(self, page=1, limit=20):
        lim, off = paginate(page, limit)
        items = await self._repo.list_shows(lim, off)
        return {"shows": [s.to_dict() for s in items], "page": page, "limit": lim}

    async def list_shows_by_owner(self, owner_id):
        items = await self._repo.list_shows_by_owner(owner_id)
        return [s.to_dict() for s in items]

    async def get_show(self, sid):
        s = await self._repo.get_show(sid)
        if not s:
            raise ValueError("Show not found")
        return s.to_dict()

    async def create_show(
        self,
        owner_id,
        title,
        slug,
        org_id="",
        description="",
        cover_image_url="",
        rss_feed_url="",
    ):
        sid = new_id()
        await self._repo.create_show(
            sid,
            owner_id,
            org_id,
            title,
            slug,
            description,
            cover_image_url,
            rss_feed_url,
        )
        return {"id": sid}

    async def update_show(self, sid, **kwargs):
        existing = await self._repo.get_show(sid)
        if not existing:
            raise ValueError("Show not found")
        await self._repo.update_show(
            sid,
            title=kwargs.get("title") or existing.title,
            description=kwargs.get("description")
            if kwargs.get("description") is not None
            else existing.description,
            cover_image_url=kwargs.get("cover_image_url")
            if kwargs.get("cover_image_url") is not None
            else existing.cover_image_url,
            rss_feed_url=kwargs.get("rss_feed_url")
            if kwargs.get("rss_feed_url") is not None
            else existing.rss_feed_url,
        )
        return {"id": sid}

    async def delete_show(self, sid):
        existing = await self._repo.get_show(sid)
        if not existing:
            raise ValueError("Show not found")
        await self._repo.delete_show(sid)

    # ── Episodes ─────────────────────────────────────────────
    async def list_episodes(self, show_id, page=1, limit=20):
        lim, off = paginate(page, limit)
        items = await self._repo.list_episodes(show_id, lim, off)
        return {"episodes": [e.to_dict() for e in items], "page": page, "limit": lim}

    async def get_episode(self, eid):
        e = await self._repo.get_episode(eid)
        if not e:
            raise ValueError("Episode not found")
        return e.to_dict()

    async def create_episode(
        self,
        show_id,
        title,
        audio_url,
        description="",
        duration_seconds=0,
        episode_number=0,
        transcript_article_id="",
        published_at="",
    ):
        eid = new_id()
        await self._repo.create_episode(
            eid,
            show_id,
            title,
            description,
            audio_url,
            duration_seconds,
            episode_number,
            transcript_article_id,
            published_at,
        )
        return {"id": eid}

    async def update_episode(self, eid, **kwargs):
        existing = await self._repo.get_episode(eid)
        if not existing:
            raise ValueError("Episode not found")
        await self._repo.update_episode(
            eid,
            title=kwargs.get("title") or existing.title,
            description=kwargs.get("description")
            if kwargs.get("description") is not None
            else existing.description,
            audio_url=kwargs.get("audio_url") or existing.audio_url,
            duration_seconds=kwargs.get("duration_seconds")
            if kwargs.get("duration_seconds") is not None
            else existing.duration_seconds,
            episode_number=kwargs.get("episode_number")
            if kwargs.get("episode_number") is not None
            else existing.episode_number,
            transcript_article_id=kwargs.get("transcript_article_id")
            if kwargs.get("transcript_article_id") is not None
            else existing.transcript_article_id,
            published_at=kwargs.get("published_at")
            if kwargs.get("published_at") is not None
            else existing.published_at,
        )
        return {"id": eid}

    async def delete_episode(self, eid):
        existing = await self._repo.get_episode(eid)
        if not existing:
            raise ValueError("Episode not found")
        await self._repo.delete_episode(eid)
