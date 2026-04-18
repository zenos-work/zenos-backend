from typing import Optional, List
from db.repository import BaseRepository
from api.add_ons import queries as Q
from models.add_on.model import OrgAddOn
from models.base import row_get


class AddOnRepository(BaseRepository):
    async def create_add_on(
        self, addon_id, org_id, add_on_type, tier, enabled_by, limits="{}"
    ):
        await self.execute(
            Q.INSERT_ADD_ON, addon_id, org_id, add_on_type, tier, enabled_by, limits
        )

    async def find_by_org(self, org_id) -> List[OrgAddOn]:
        rows = await self.find_all(Q.SELECT_ADD_ONS_BY_ORG, org_id)
        return self.map_many(rows, OrgAddOn)

    async def find_by_org_type(self, org_id, add_on_type) -> Optional[OrgAddOn]:
        row = await self.find_one(Q.SELECT_ADD_ON_BY_ORG_TYPE, org_id, add_on_type)
        return self.map_one(row, OrgAddOn)

    async def update_add_on(self, org_id, add_on_type, tier, limits="{}"):
        await self.execute(Q.UPDATE_ADD_ON, tier, limits, org_id, add_on_type)

    async def disable_add_on(self, org_id, add_on_type):
        await self.execute(Q.DISABLE_ADD_ON, org_id, add_on_type)

    async def summary(self) -> list:
        rows = await self.find_all(Q.COUNT_ADD_ONS_SUMMARY)
        return [
            {"add_on_type": row_get(r, "add_on_type"), "count": row_get(r, "c", 0)}
            for r in rows
        ]
