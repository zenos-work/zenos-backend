"""Phase 9 Step 35 — Podcast repository."""

from db.repository import BaseRepository
from api.podcasts import queries as Q
from models.podcast.model import PodcastShow, PodcastEpisode


class PodcastRepository(BaseRepository):
    def _one(self, cls, row):
        return self.map_one(row, cls)

    def _many(self, rows, cls):
        return self.map_many(rows, cls)

    # ── Shows ────────────────────────────────────────────────
    async def list_shows(self, limit, offset):
        return self._many(await self.find_all(Q.LIST_SHOWS, limit, offset), PodcastShow)

    async def list_shows_by_owner(self, owner_id):
        return self._many(
            await self.find_all(Q.LIST_SHOWS_BY_OWNER, owner_id), PodcastShow
        )

    async def get_show(self, sid):
        return self._one(PodcastShow, await self.find_one(Q.GET_SHOW, sid))

    async def get_show_by_slug(self, slug):
        return self._one(PodcastShow, await self.find_one(Q.GET_SHOW_BY_SLUG, slug))

    async def create_show(
        self,
        sid,
        owner_id,
        org_id,
        title,
        slug,
        description,
        cover_image_url,
        rss_feed_url,
    ):
        await self.execute(
            Q.INSERT_SHOW,
            sid,
            owner_id,
            org_id,
            title,
            slug,
            description,
            cover_image_url,
            rss_feed_url,
        )

    async def update_show(self, sid, title, description, cover_image_url, rss_feed_url):
        await self.execute(
            Q.UPDATE_SHOW, title, description, cover_image_url, rss_feed_url, sid
        )

    async def delete_show(self, sid):
        await self.execute(Q.DELETE_SHOW, sid)

    # ── Episodes ─────────────────────────────────────────────
    async def list_episodes(self, show_id, limit, offset):
        return self._many(
            await self.find_all(Q.LIST_EPISODES, show_id, limit, offset), PodcastEpisode
        )

    async def get_episode(self, eid):
        return self._one(PodcastEpisode, await self.find_one(Q.GET_EPISODE, eid))

    async def create_episode(
        self,
        eid,
        show_id,
        title,
        description,
        audio_url,
        duration_seconds,
        episode_number,
        transcript_article_id,
        published_at,
    ):
        await self.execute(
            Q.INSERT_EPISODE,
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

    async def update_episode(
        self,
        eid,
        title,
        description,
        audio_url,
        duration_seconds,
        episode_number,
        transcript_article_id,
        published_at,
    ):
        await self.execute(
            Q.UPDATE_EPISODE,
            title,
            description,
            audio_url,
            duration_seconds,
            episode_number,
            transcript_article_id,
            published_at,
            eid,
        )

    async def delete_episode(self, eid):
        await self.execute(Q.DELETE_EPISODE, eid)
