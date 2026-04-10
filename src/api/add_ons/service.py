from api.add_ons.repository import AddOnRepository
from models.add_on.model import VALID_ADD_ON_TYPES
from utils.helpers import new_id


class AddOnService:
    def __init__(self, env, ctx=None):
        self._repo = AddOnRepository(env.DB, ctx)

    async def enable_add_on(self, org_id, add_on_type, tier, enabled_by, limits="{}"):
        if add_on_type not in VALID_ADD_ON_TYPES:
            raise ValueError(f"Invalid add-on type: {add_on_type}")
        existing = await self._repo.find_by_org_type(org_id, add_on_type)
        if existing and existing.is_active:
            raise ValueError("Add-on already active")
        aid = new_id()
        await self._repo.create_add_on(
            aid, org_id, add_on_type, tier, enabled_by, limits
        )
        addon = await self._repo.find_by_org_type(org_id, add_on_type)
        return addon.to_dict(scope="admin") if addon else {"id": aid}

    async def update_add_on(self, org_id, add_on_type, tier, limits="{}"):
        existing = await self._repo.find_by_org_type(org_id, add_on_type)
        if not existing:
            raise ValueError("Add-on not found")
        await self._repo.update_add_on(org_id, add_on_type, tier, limits)
        updated = await self._repo.find_by_org_type(org_id, add_on_type)
        return updated.to_dict(scope="admin") if updated else {}

    async def disable_add_on(self, org_id, add_on_type):
        existing = await self._repo.find_by_org_type(org_id, add_on_type)
        if not existing:
            raise ValueError("Add-on not found")
        await self._repo.disable_add_on(org_id, add_on_type)

    async def list_add_ons(self, org_id):
        addons = await self._repo.find_by_org(org_id)
        return {"add_ons": [a.to_dict() for a in addons]}

    async def get_usage(self, org_id, add_on_type):
        addon = await self._repo.find_by_org_type(org_id, add_on_type)
        if not addon:
            raise ValueError("Add-on not found")
        return {
            "add_on_type": add_on_type,
            "tier": addon.tier,
            "limits": addon.limits,
            "is_active": addon.is_active,
        }

    async def summary(self):
        return {"summary": await self._repo.summary()}
