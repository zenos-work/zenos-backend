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

    # Alias to avoid collision with builtin find_all
    async def find_all_rows(self, sql, *params):
        return await super().find_all(sql, *params)
