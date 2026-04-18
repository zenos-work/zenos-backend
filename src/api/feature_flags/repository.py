from typing import Optional, List
from db.repository import BaseRepository
from api.feature_flags import queries as Q
from models.feature_flag.model import FeatureFlag
from models.base import row_get


class FeatureFlagRepository(BaseRepository):
    async def create(
        self,
        flag_id: str,
        flag_key: str,
        name: str,
        description: str,
        category: str,
        is_active: int,
        target_type: str,
        targets: str,
        rollout_pct: int,
        metadata: str,
        created_by: str,
    ) -> None:
        await self.execute(
            Q.INSERT_FLAG,
            flag_id,
            flag_key,
            name,
            description or "",
            category,
            is_active,
            target_type,
            targets,
            rollout_pct,
            metadata,
            created_by,
        )

    async def find_by_id(self, flag_id: str) -> Optional[FeatureFlag]:
        row = await self.find_one(Q.GET_FLAG_BY_ID, flag_id)
        return self.map_one(row, FeatureFlag)

    async def find_by_key(self, flag_key: str) -> Optional[FeatureFlag]:
        row = await self.find_one(Q.GET_FLAG_BY_KEY, flag_key)
        return self.map_one(row, FeatureFlag)

    async def find_all(self) -> List[FeatureFlag]:
        rows = await self.find_all_rows(Q.GET_ALL_FLAGS)
        return self.map_many(rows, FeatureFlag)

    async def find_active(self) -> List[FeatureFlag]:
        rows = await self.find_all_rows(Q.GET_ACTIVE_FLAGS)
        return self.map_many(rows, FeatureFlag)

    async def find_by_category(self, category: str) -> List[FeatureFlag]:
        rows = await self.find_all_rows(Q.GET_FLAGS_BY_CATEGORY, category)
        return self.map_many(rows, FeatureFlag)

    async def count_all(self) -> int:
        row = await self.find_one(Q.COUNT_ALL)
        return row_get(row, "c", 0)

    async def update(
        self,
        flag_id: str,
        name: str,
        description: str,
        category: str,
        is_active: int,
        target_type: str,
        targets: str,
        rollout_pct: int,
        metadata: str,
        updated_by: str,
    ) -> None:
        await self.execute(
            Q.UPDATE_FLAG,
            name,
            description or "",
            category,
            is_active,
            target_type,
            targets,
            rollout_pct,
            metadata,
            updated_by,
            flag_id,
        )

    async def delete(self, flag_id: str) -> None:
        await self.execute(Q.DELETE_FLAG, flag_id)

    async def toggle(self, flag_id: str, updated_by: str) -> None:
        await self.execute(Q.TOGGLE_FLAG, updated_by, flag_id)

    async def list_active_user_ids(self) -> List[str]:
        rows = await self.find_all_rows(Q.LIST_ACTIVE_USER_IDS)
        return [row_get(r, "id", "") for r in rows if row_get(r, "id", "")]

    async def list_active_user_ids_by_roles(self, roles: List[str]) -> List[str]:
        if not roles:
            return []
        placeholders = ",".join(["?"] * len(roles))
        sql = Q.LIST_ACTIVE_USER_IDS_BY_ROLE.format(placeholders=placeholders)
        rows = await self.find_all_rows(sql, *roles)
        return [row_get(r, "id", "") for r in rows if row_get(r, "id", "")]

    async def list_active_user_ids_by_ids(self, user_ids: List[str]) -> List[str]:
        if not user_ids:
            return []
        placeholders = ",".join(["?"] * len(user_ids))
        sql = Q.LIST_ACTIVE_USER_IDS_BY_IDS.format(placeholders=placeholders)
        rows = await self.find_all_rows(sql, *user_ids)
        return [row_get(r, "id", "") for r in rows if row_get(r, "id", "")]

    async def list_active_user_ids_by_membership_tiers(
        self, membership_tiers: List[str]
    ) -> List[str]:
        if not membership_tiers:
            return []
        placeholders = ",".join(["?"] * len(membership_tiers))
        sql = Q.LIST_ACTIVE_USER_IDS_BY_MEMBERSHIP_TIERS.format(
            placeholders=placeholders
        )
        rows = await self.find_all_rows(sql, *membership_tiers)
        return [row_get(r, "id", "") for r in rows if row_get(r, "id", "")]

    async def list_active_user_ids_by_org_ids(self, org_ids: List[str]) -> List[str]:
        if not org_ids:
            return []
        placeholders = ",".join(["?"] * len(org_ids))
        sql = Q.LIST_ACTIVE_USER_IDS_BY_ORG_IDS.format(placeholders=placeholders)
        rows = await self.find_all_rows(sql, *org_ids)
        return [row_get(r, "id", "") for r in rows if row_get(r, "id", "")]

    async def list_active_user_ids_by_org_tiers(
        self, org_tiers: List[str]
    ) -> List[str]:
        if not org_tiers:
            return []
        placeholders = ",".join(["?"] * len(org_tiers))
        sql = Q.LIST_ACTIVE_USER_IDS_BY_ORG_TIERS.format(placeholders=placeholders)
        rows = await self.find_all_rows(sql, *org_tiers)
        return [row_get(r, "id", "") for r in rows if row_get(r, "id", "")]

    async def list_user_ids_with_enabled_pref(
        self, user_ids: List[str], notification_type: str, channel: str
    ) -> List[str]:
        if not user_ids:
            return []
        placeholders = ",".join(["?"] * len(user_ids))
        sql = Q.LIST_USER_IDS_WITH_ENABLED_PREF.format(placeholders=placeholders)
        rows = await self.find_all_rows(sql, notification_type, channel, *user_ids)
        return [row_get(r, "user_id", "") for r in rows if row_get(r, "user_id", "")]

    async def list_user_ids_with_active_push_subs(
        self, user_ids: List[str]
    ) -> List[str]:
        if not user_ids:
            return []
        placeholders = ",".join(["?"] * len(user_ids))
        sql = Q.LIST_USER_IDS_WITH_ACTIVE_PUSH_SUBS.format(placeholders=placeholders)
        rows = await self.find_all_rows(sql, *user_ids)
        return [row_get(r, "user_id", "") for r in rows if row_get(r, "user_id", "")]

    async def insert_notification(
        self,
        nid: str,
        user_id: str,
        actor_id: str,
        type_: str,
        message: str,
        channel: str = "in_app",
        delivery_status: str = "pending",
        group_key: str = "",
    ) -> None:
        await self.execute(
            Q.INSERT_NOTIFICATION,
            nid,
            user_id,
            actor_id if actor_id else None,
            type_,
            None,  # article_id
            None,  # comment_id
            message,
            channel or "in_app",
            delivery_status or "pending",
            group_key or None,
        )

    # Alias to avoid collision with builtin find_all
    async def find_all_rows(self, sql, *params):
        return await super().find_all(sql, *params)
