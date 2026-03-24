from datetime import datetime, timedelta, timezone

from api.analytics.repository import AnalyticsRepository
from utils.helpers import new_id


class AnalyticsService:
    def __init__(self, env, ctx=None):
        self._repo = AnalyticsRepository(env.DB, ctx)
        self._ctx = ctx

    async def _log(self, name: str, data: dict | None = None) -> None:
        if self._ctx:
            await self._ctx.log.event(name, data=data)

    async def record_article_event(
        self,
        article_id: str,
        event_type: str,
        actor_user_id: str | None = None,
        event_value: int = 1,
        event_source: str = "api",
        metadata_json: str | None = None,
    ) -> None:
        await self._repo.record_article_event(
            event_id=new_id(),
            article_id=article_id,
            event_type=event_type,
            actor_user_id=actor_user_id,
            event_value=event_value,
            event_source=event_source,
            metadata_json=metadata_json,
        )

    async def aggregate_previous_hour(self) -> dict:
        now = datetime.now(timezone.utc).replace(
            minute=0, second=0, microsecond=0, tzinfo=None
        )
        bucket = now - timedelta(hours=1)

        bucket_hour = bucket.strftime("%Y-%m-%d %H:00:00")
        window_start = bucket_hour
        window_end = now.strftime("%Y-%m-%d %H:00:00")

        events = await self._repo.count_events_in_window(window_start, window_end)
        await self._repo.aggregate_hour(bucket_hour, window_start, window_end)

        result = {
            "bucket_hour": bucket_hour,
            "window_start": window_start,
            "window_end": window_end,
            "events_processed": events,
        }
        await self._log("sr011.hourly_aggregation.completed", result)
        return result
