from db.repository import BaseRepository
from models.base import row_get
from api.analytics import queries as Q
from models.analytics.model import (
    AnalyticsEvent,
    ConversionGoal,
    ConversionEvent,
    FunnelDefinition,
    FunnelStep,
    AbExperiment,
    AbExperimentVariant,
)


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
            actor_user_id or "",
            event_type,
            event_value,
            event_source,
            metadata_json or "",
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

    # ═══════════════════════════════════════════════════════════
    # Phase 6 Step 26 — Extended analytics
    # ═══════════════════════════════════════════════════════════

    def _one(self, cls, row):
        return self.map_one(row, cls)

    def _many(self, rows, cls):
        return self.map_many(rows, cls)

    # ── Analytics Events ─────────────────────────────────────
    async def list_analytics_events(self, org_id, limit=50, offset=0):
        return self._many(
            await self.find_all(Q.LIST_ANALYTICS_EVENTS, org_id, limit, offset),
            AnalyticsEvent,
        )

    async def create_analytics_event(
        self,
        eid,
        org_id,
        user_id,
        session_id,
        anonymous_id,
        event_category,
        event_action,
        event_label,
        event_value,
        resource_type,
        resource_id,
        page_url,
        referrer_url,
        utm_source,
        utm_medium,
        utm_campaign,
        properties,
        device_type,
        country_code,
    ):
        import json

        await self.execute(
            Q.INSERT_ANALYTICS_EVENT,
            eid,
            org_id,
            user_id,
            session_id,
            anonymous_id,
            event_category,
            event_action,
            event_label,
            event_value,
            resource_type,
            resource_id,
            page_url,
            referrer_url,
            utm_source,
            utm_medium,
            utm_campaign,
            json.dumps(properties),
            device_type,
            country_code,
        )

    # ── Conversion Goals ─────────────────────────────────────
    async def list_goals(self, org_id):
        return self._many(await self.find_all(Q.LIST_GOALS, org_id), ConversionGoal)

    async def get_goal(self, gid):
        return self._one(ConversionGoal, await self.find_one(Q.GET_GOAL, gid))

    async def create_goal(
        self,
        gid,
        org_id,
        name,
        goal_type,
        target_cat,
        target_action,
        target_resource,
        value_cents,
        is_active,
    ):
        await self.execute(
            Q.INSERT_GOAL,
            gid,
            org_id,
            name,
            goal_type,
            target_cat,
            target_action,
            target_resource,
            value_cents,
            int(is_active),
        )

    async def update_goal(
        self,
        gid,
        name,
        goal_type,
        target_cat,
        target_action,
        target_resource,
        value_cents,
        is_active,
    ):
        await self.execute(
            Q.UPDATE_GOAL,
            name,
            goal_type,
            target_cat,
            target_action,
            target_resource,
            value_cents,
            int(is_active),
            gid,
        )

    async def delete_goal(self, gid):
        await self.execute(Q.DELETE_GOAL, gid)

    # ── Conversion Events ────────────────────────────────────
    async def list_conversions(self, goal_id, limit=50, offset=0):
        return self._many(
            await self.find_all(Q.LIST_CONVERSIONS, goal_id, limit, offset),
            ConversionEvent,
        )

    async def create_conversion(
        self,
        cid,
        goal_id,
        org_id,
        user_id,
        anonymous_id,
        session_id,
        event_id,
        value_cents,
    ):
        await self.execute(
            Q.INSERT_CONVERSION,
            cid,
            goal_id,
            org_id,
            user_id,
            anonymous_id,
            session_id,
            event_id,
            value_cents,
        )

    # ── Funnel Definitions ───────────────────────────────────
    async def list_funnels(self, org_id):
        return self._many(await self.find_all(Q.LIST_FUNNELS, org_id), FunnelDefinition)

    async def get_funnel(self, fid):
        return self._one(FunnelDefinition, await self.find_one(Q.GET_FUNNEL, fid))

    async def create_funnel(
        self, fid, org_id, name, description, is_active, created_by
    ):
        await self.execute(
            Q.INSERT_FUNNEL, fid, org_id, name, description, int(is_active), created_by
        )

    async def update_funnel(self, fid, name, description, is_active):
        await self.execute(Q.UPDATE_FUNNEL, name, description, int(is_active), fid)

    async def delete_funnel(self, fid):
        await self.execute(Q.DELETE_FUNNEL, fid)

    # ── Funnel Steps ─────────────────────────────────────────
    async def list_funnel_steps(self, funnel_id):
        return self._many(
            await self.find_all(Q.LIST_FUNNEL_STEPS, funnel_id), FunnelStep
        )

    async def create_funnel_step(
        self,
        sid,
        funnel_id,
        step_number,
        name,
        event_category,
        event_action,
        resource_type,
        resource_id,
    ):
        await self.execute(
            Q.INSERT_FUNNEL_STEP,
            sid,
            funnel_id,
            step_number,
            name,
            event_category,
            event_action,
            resource_type,
            resource_id,
        )

    async def delete_funnel_step(self, sid):
        await self.execute(Q.DELETE_FUNNEL_STEP, sid)

    # ── A/B Experiments ──────────────────────────────────────
    async def list_experiments(self, org_id):
        return self._many(await self.find_all(Q.LIST_EXPERIMENTS, org_id), AbExperiment)

    async def get_experiment(self, eid):
        return self._one(AbExperiment, await self.find_one(Q.GET_EXPERIMENT, eid))

    async def create_experiment(
        self, eid, org_id, name, hypothesis, traffic_split, success_goal_id, created_by
    ):
        import json

        await self.execute(
            Q.INSERT_EXPERIMENT,
            eid,
            org_id,
            name,
            hypothesis,
            json.dumps(traffic_split),
            success_goal_id,
            created_by,
        )

    async def update_experiment(
        self,
        eid,
        name,
        hypothesis,
        status,
        traffic_split,
        started_at,
        ended_at,
        winner_variant,
    ):
        import json

        await self.execute(
            Q.UPDATE_EXPERIMENT,
            name,
            hypothesis,
            status,
            json.dumps(traffic_split),
            started_at,
            ended_at,
            winner_variant,
            eid,
        )

    async def delete_experiment(self, eid):
        await self.execute(Q.DELETE_EXPERIMENT, eid)

    # ── A/B Experiment Variants ──────────────────────────────
    async def list_variants(self, experiment_id):
        return self._many(
            await self.find_all(Q.LIST_VARIANTS, experiment_id), AbExperimentVariant
        )

    async def get_variant(self, vid):
        return self._one(AbExperimentVariant, await self.find_one(Q.GET_VARIANT, vid))

    async def create_variant(self, vid, experiment_id, name, description, changes):
        import json

        await self.execute(
            Q.INSERT_VARIANT, vid, experiment_id, name, description, json.dumps(changes)
        )

    async def update_variant_stats(self, vid, impressions, conversions):
        await self.execute(Q.UPDATE_VARIANT_STATS, impressions, conversions, vid)

    async def delete_variant(self, vid):
        await self.execute(Q.DELETE_VARIANT, vid)

    # ── A/B Experiment Assignments ───────────────────────────
    async def get_assignment(self, experiment_id, anonymous_id):
        row = await self.find_one(Q.GET_ASSIGNMENT, experiment_id, anonymous_id)
        return row_get(row, "variant_id", "") if row else None

    async def create_assignment(self, experiment_id, anonymous_id, variant_id):
        await self.execute(Q.INSERT_ASSIGNMENT, experiment_id, anonymous_id, variant_id)

    # ── Metering / Dashboard (Steps 27-28) ──────────────────
    async def count_events_by_category(self, org_id, start, end):
        return await self.find_all(Q.COUNT_EVENTS_BY_CATEGORY, org_id, start, end)

    async def count_conversions_by_goal(self, org_id, start, end):
        return await self.find_all(Q.COUNT_CONVERSIONS_BY_GOAL, org_id, start, end)

    async def experiment_summary(self, org_id):
        return await self.find_all(Q.EXPERIMENT_SUMMARY, org_id)
