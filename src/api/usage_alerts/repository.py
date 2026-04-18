"""Phase 10 Steps 39-40 — Usage alerts repository."""

import json
from db.repository import BaseRepository
from api.usage_alerts import queries as Q
from models.alert_rule.model import AlertRule


class UsageAlertRepository(BaseRepository):
    def _one(self, cls, row):
        return self.map_one(row, cls)

    def _many(self, rows, cls):
        return self.map_many(rows, cls)

    async def list_alert_rules(self, org_id):
        return self._many(await self.find_all(Q.LIST_ALERT_RULES, org_id), AlertRule)

    async def list_active_alerts(self, org_id):
        return self._many(await self.find_all(Q.LIST_ACTIVE_ALERTS, org_id), AlertRule)

    async def get_alert_rule(self, rid):
        return self._one(AlertRule, await self.find_one(Q.GET_ALERT_RULE, rid))

    async def create_alert_rule(
        self,
        rid,
        org_id,
        created_by,
        name,
        alert_type,
        config,
        threshold_value,
        comparison,
        notify_channels,
        notify_user_ids,
        cooldown_minutes,
        is_active,
    ):
        await self.execute(
            Q.INSERT_ALERT_RULE,
            rid,
            org_id,
            created_by,
            name,
            alert_type,
            json.dumps(config),
            threshold_value,
            comparison,
            json.dumps(notify_channels),
            json.dumps(notify_user_ids),
            cooldown_minutes,
            int(is_active),
        )

    async def update_alert_rule(
        self,
        rid,
        name,
        alert_type,
        config,
        threshold_value,
        comparison,
        notify_channels,
        notify_user_ids,
        cooldown_minutes,
        is_active,
    ):
        await self.execute(
            Q.UPDATE_ALERT_RULE,
            name,
            alert_type,
            json.dumps(config),
            threshold_value,
            comparison,
            json.dumps(notify_channels),
            json.dumps(notify_user_ids),
            cooldown_minutes,
            int(is_active),
            rid,
        )

    async def delete_alert_rule(self, rid):
        await self.execute(Q.DELETE_ALERT_RULE, rid)

    async def toggle_alert_rule(self, rid, is_active):
        await self.execute(Q.TOGGLE_ALERT_RULE, int(is_active), rid)

    async def trigger_alert(self, rid):
        await self.execute(Q.TRIGGER_ALERT, rid)

    # ── Quota helpers ────────────────────────────────────────
    async def get_org_workflow_limit(self, org_id):
        row = await self.find_one(Q.GET_ORG_WORKFLOW_LIMIT, org_id)
        return int(row.get("limit_value", 0)) if row else 0

    async def get_org_monthly_runs(self, org_id, year_month):
        row = await self.find_one(Q.GET_ORG_MONTHLY_RUNS, org_id, year_month)
        return int(row.get("workflow_runs", 0)) if row else 0
