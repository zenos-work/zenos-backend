from db.repository import BaseRepository
from models.base import row_get
from api.analytics import queries as Q


class AnalyticsRepository(BaseRepository):
    async def record_article_event(
        self,
        event_id: str,
        article_id: str,
        event_type: str,
        actor_user_id: str | None = None,
        event_value: int = 1,
        event_source: str = "api",
        metadata_json: str | None = None,
    ) -> None:
        await self.execute(
            Q.INSERT_ARTICLE_EVENT,
            event_id,
            article_id,
            actor_user_id,
            event_type,
            event_value,
            event_source,
            metadata_json,
        )

    async def aggregate_hour(
        self,
        bucket_hour: str,
        window_start: str,
        window_end: str,
    ) -> None:
        await self.execute(
            Q.UPSERT_HOURLY_SUCCESS, bucket_hour, window_start, window_end
        )

    async def count_events_in_window(self, window_start: str, window_end: str) -> int:
        row = await self.find_one(Q.COUNT_EVENTS_IN_WINDOW, window_start, window_end)
        return row_get(row, "count", 0) if row else 0
