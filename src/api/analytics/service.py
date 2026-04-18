from datetime import datetime, timedelta, timezone

from api.analytics.repository import AnalyticsRepository
from utils.helpers import new_id, paginate


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

    # ═══════════════════════════════════════════════════════════
    # Phase 6 Step 26 — Extended analytics engine
    # ═══════════════════════════════════════════════════════════

    # ── Analytics Events ─────────────────────────────────────
    async def list_analytics_events(self, org_id, page=1, limit=50):
        lim, off = paginate(page, limit)
        items = await self._repo.list_analytics_events(org_id, lim, off)
        return {"events": [e.to_dict() for e in items], "page": page, "limit": lim}

    async def track_event(self, org_id, event_category, event_action, **kwargs):
        eid = new_id()
        await self._repo.create_analytics_event(
            eid,
            org_id,
            kwargs.get("user_id", ""),
            kwargs.get("session_id", ""),
            kwargs.get("anonymous_id", ""),
            event_category,
            event_action,
            kwargs.get("event_label", ""),
            kwargs.get("event_value", 0),
            kwargs.get("resource_type", ""),
            kwargs.get("resource_id", ""),
            kwargs.get("page_url", ""),
            kwargs.get("referrer_url", ""),
            kwargs.get("utm_source", ""),
            kwargs.get("utm_medium", ""),
            kwargs.get("utm_campaign", ""),
            kwargs.get("properties", {}),
            kwargs.get("device_type", ""),
            kwargs.get("country_code", ""),
        )
        return {"id": eid}

    # ── Conversion Goals ─────────────────────────────────────
    async def list_goals(self, org_id):
        items = await self._repo.list_goals(org_id)
        return [g.to_dict() for g in items]

    async def get_goal(self, gid):
        g = await self._repo.get_goal(gid)
        if not g:
            raise ValueError("Goal not found")
        return g.to_dict()

    async def create_goal(
        self,
        org_id,
        name,
        goal_type,
        target_event_category="",
        target_event_action="",
        target_resource_id="",
        value_cents=0,
        is_active=True,
    ):
        gid = new_id()
        await self._repo.create_goal(
            gid,
            org_id,
            name,
            goal_type,
            target_event_category,
            target_event_action,
            target_resource_id,
            value_cents,
            is_active,
        )
        return {"id": gid}

    async def update_goal(self, gid, **kwargs):
        existing = await self._repo.get_goal(gid)
        if not existing:
            raise ValueError("Goal not found")
        await self._repo.update_goal(
            gid,
            kwargs.get("name") or existing.name,
            kwargs.get("goal_type") or existing.goal_type,
            kwargs.get("target_event_category")
            if kwargs.get("target_event_category") is not None
            else existing.target_event_category,
            kwargs.get("target_event_action")
            if kwargs.get("target_event_action") is not None
            else existing.target_event_action,
            kwargs.get("target_resource_id")
            if kwargs.get("target_resource_id") is not None
            else existing.target_resource_id,
            kwargs.get("value_cents")
            if kwargs.get("value_cents") is not None
            else existing.value_cents,
            kwargs.get("is_active")
            if kwargs.get("is_active") is not None
            else existing.is_active,
        )
        return {"id": gid}

    async def delete_goal(self, gid):
        existing = await self._repo.get_goal(gid)
        if not existing:
            raise ValueError("Goal not found")
        await self._repo.delete_goal(gid)

    # ── Conversion Events ────────────────────────────────────
    async def list_conversions(self, goal_id, page=1, limit=50):
        lim, off = paginate(page, limit)
        items = await self._repo.list_conversions(goal_id, lim, off)
        return {"conversions": [c.to_dict() for c in items], "page": page, "limit": lim}

    async def record_conversion(
        self,
        goal_id,
        org_id,
        user_id="",
        anonymous_id="",
        session_id="",
        event_id="",
        value_cents=0,
    ):
        cid = new_id()
        await self._repo.create_conversion(
            cid,
            goal_id,
            org_id,
            user_id,
            anonymous_id,
            session_id,
            event_id,
            value_cents,
        )
        return {"id": cid}

    # ── Funnel Definitions ───────────────────────────────────
    async def list_funnels(self, org_id):
        items = await self._repo.list_funnels(org_id)
        return [f.to_dict() for f in items]

    async def get_funnel(self, fid):
        f = await self._repo.get_funnel(fid)
        if not f:
            raise ValueError("Funnel not found")
        return f.to_dict()

    async def create_funnel(
        self, org_id, name, description="", is_active=True, created_by=""
    ):
        fid = new_id()
        await self._repo.create_funnel(
            fid, org_id, name, description, is_active, created_by
        )
        return {"id": fid}

    async def update_funnel(self, fid, **kwargs):
        existing = await self._repo.get_funnel(fid)
        if not existing:
            raise ValueError("Funnel not found")
        await self._repo.update_funnel(
            fid,
            kwargs.get("name") or existing.name,
            kwargs.get("description")
            if kwargs.get("description") is not None
            else existing.description,
            kwargs.get("is_active")
            if kwargs.get("is_active") is not None
            else existing.is_active,
        )
        return {"id": fid}

    async def delete_funnel(self, fid):
        existing = await self._repo.get_funnel(fid)
        if not existing:
            raise ValueError("Funnel not found")
        await self._repo.delete_funnel(fid)

    # ── Funnel Steps ─────────────────────────────────────────
    async def list_funnel_steps(self, funnel_id):
        items = await self._repo.list_funnel_steps(funnel_id)
        return [s.to_dict() for s in items]

    async def create_funnel_step(
        self,
        funnel_id,
        step_number,
        name,
        event_category,
        event_action,
        resource_type="",
        resource_id="",
    ):
        sid = new_id()
        await self._repo.create_funnel_step(
            sid,
            funnel_id,
            step_number,
            name,
            event_category,
            event_action,
            resource_type,
            resource_id,
        )
        return {"id": sid}

    async def delete_funnel_step(self, sid):
        await self._repo.delete_funnel_step(sid)

    # ── A/B Experiments ──────────────────────────────────────
    async def list_experiments(self, org_id):
        items = await self._repo.list_experiments(org_id)
        return [e.to_dict() for e in items]

    async def get_experiment(self, eid):
        e = await self._repo.get_experiment(eid)
        if not e:
            raise ValueError("Experiment not found")
        return e.to_dict()

    async def create_experiment(
        self,
        org_id,
        name,
        hypothesis="",
        traffic_split=None,
        success_goal_id="",
        created_by="",
    ):
        eid = new_id()
        await self._repo.create_experiment(
            eid,
            org_id,
            name,
            hypothesis,
            traffic_split or {},
            success_goal_id,
            created_by,
        )
        return {"id": eid}

    async def update_experiment(self, eid, **kwargs):
        existing = await self._repo.get_experiment(eid)
        if not existing:
            raise ValueError("Experiment not found")
        await self._repo.update_experiment(
            eid,
            kwargs.get("name") or existing.name,
            kwargs.get("hypothesis")
            if kwargs.get("hypothesis") is not None
            else existing.hypothesis,
            kwargs.get("status") or existing.status,
            kwargs.get("traffic_split")
            if kwargs.get("traffic_split") is not None
            else existing.traffic_split,
            kwargs.get("started_at")
            if kwargs.get("started_at") is not None
            else existing.started_at,
            kwargs.get("ended_at")
            if kwargs.get("ended_at") is not None
            else existing.ended_at,
            kwargs.get("winner_variant")
            if kwargs.get("winner_variant") is not None
            else existing.winner_variant,
        )
        return {"id": eid}

    async def delete_experiment(self, eid):
        existing = await self._repo.get_experiment(eid)
        if not existing:
            raise ValueError("Experiment not found")
        await self._repo.delete_experiment(eid)

    # ── A/B Experiment Variants ──────────────────────────────
    async def list_variants(self, experiment_id):
        items = await self._repo.list_variants(experiment_id)
        return [v.to_dict() for v in items]

    async def create_variant(self, experiment_id, name, description="", changes=None):
        vid = new_id()
        await self._repo.create_variant(
            vid, experiment_id, name, description, changes or {}
        )
        return {"id": vid}

    async def update_variant_stats(self, vid, impressions, conversions):
        await self._repo.update_variant_stats(vid, impressions, conversions)
        return {"id": vid}

    async def delete_variant(self, vid):
        await self._repo.delete_variant(vid)

    # ── A/B Experiment Assignments ───────────────────────────
    async def get_or_assign(self, experiment_id, anonymous_id, variant_id):
        existing = await self._repo.get_assignment(experiment_id, anonymous_id)
        if existing:
            return {"variant_id": existing, "new": False}
        await self._repo.create_assignment(experiment_id, anonymous_id, variant_id)
        return {"variant_id": variant_id, "new": True}

    # ── Metering / Dashboard (Steps 27-28) ──────────────────
    async def dashboard_event_breakdown(self, org_id, start, end):
        rows = await self._repo.count_events_by_category(org_id, start, end)
        return [{"category": r["event_category"], "count": r["cnt"]} for r in rows]

    async def dashboard_conversion_summary(self, org_id, start, end):
        rows = await self._repo.count_conversions_by_goal(org_id, start, end)
        return [
            {
                "goal": r["name"],
                "count": r["cnt"],
                "total_value_cents": r["total_value"],
            }
            for r in rows
        ]

    async def dashboard_experiment_summary(self, org_id):
        rows = await self._repo.experiment_summary(org_id)
        experiments = {}
        for r in rows:
            eid = r["id"]
            if eid not in experiments:
                experiments[eid] = {
                    "id": eid,
                    "name": r["name"],
                    "status": r["status"],
                    "variants": [],
                }
            experiments[eid]["variants"].append(
                {
                    "id": r["variant_id"],
                    "name": r["variant_name"],
                    "impressions": r["impressions"],
                    "conversions": r["conversions"],
                }
            )
        return list(experiments.values())
