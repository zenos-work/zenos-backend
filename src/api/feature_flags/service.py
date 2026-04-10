import json
from typing import Optional
from api.feature_flags.repository import FeatureFlagRepository
from models.feature_flag.model import (
    VALID_CATEGORIES,
    VALID_TARGET_TYPES,
)
from utils.helpers import new_id


class FeatureFlagService:
    def __init__(self, env, ctx=None):
        self._repo = FeatureFlagRepository(env.DB, ctx)

    # ── Public API ──────────────────────────────────────────────

    async def evaluate_all(
        self,
        user_id=None,
        user_role=None,
        org_id=None,
        org_tier=None,
        membership_tier=None,
    ) -> dict:
        """Return a dict of flag_key → bool for all active flags."""
        flags = await self._repo.find_active()
        result = {}
        for f in flags:
            result[f.flag_key] = f.evaluate(
                user_id=user_id,
                user_role=user_role,
                org_id=org_id,
                org_tier=org_tier,
                membership_tier=membership_tier,
            )
        return result

    async def evaluate_one(
        self,
        flag_key: str,
        user_id=None,
        user_role=None,
        org_id=None,
        org_tier=None,
        membership_tier=None,
    ) -> bool:
        """Check a single flag."""
        flag = await self._repo.find_by_key(flag_key)
        if not flag:
            return False
        return flag.evaluate(
            user_id=user_id,
            user_role=user_role,
            org_id=org_id,
            org_tier=org_tier,
            membership_tier=membership_tier,
        )

    async def require_feature(
        self,
        flag_key: str,
        user_id=None,
        user_role=None,
        org_id=None,
        org_tier=None,
        membership_tier=None,
    ) -> None:
        """Raise PermissionError if feature is not enabled."""
        enabled = await self.evaluate_one(
            flag_key,
            user_id=user_id,
            user_role=user_role,
            org_id=org_id,
            org_tier=org_tier,
            membership_tier=membership_tier,
        )
        if not enabled:
            raise PermissionError(f"Feature '{flag_key}' is not available")

    # ── Admin CRUD ──────────────────────────────────────────────

    async def list_flags(self, category: Optional[str] = None) -> dict:
        if category:
            flags = await self._repo.find_by_category(category)
        else:
            flags = await self._repo.find_all()
        total = await self._repo.count_all()
        return {
            "flags": [f.to_dict(scope="admin") for f in flags],
            "total": total,
        }

    async def get_flag(self, flag_id: str) -> dict:
        flag = await self._repo.find_by_id(flag_id)
        if not flag:
            raise ValueError("Flag not found")
        return flag.to_dict(scope="admin")

    async def create_flag(
        self,
        flag_key: str,
        name: str,
        created_by: str,
        description: str = "",
        category: str = "general",
        is_active: bool = False,
        target_type: str = "global",
        targets: list = None,
        rollout_pct: int = 0,
        metadata: dict = None,
    ) -> dict:
        if category not in VALID_CATEGORIES:
            raise ValueError(f"Invalid category: {category}")
        if target_type not in VALID_TARGET_TYPES:
            raise ValueError(f"Invalid target_type: {target_type}")
        if rollout_pct < 0 or rollout_pct > 100:
            raise ValueError("rollout_pct must be 0-100")
        existing = await self._repo.find_by_key(flag_key)
        if existing:
            raise ValueError(f"Flag key '{flag_key}' already exists")

        fid = new_id()
        await self._repo.create(
            flag_id=fid,
            flag_key=flag_key,
            name=name,
            description=description,
            category=category,
            is_active=1 if is_active else 0,
            target_type=target_type,
            targets=json.dumps(targets or []),
            rollout_pct=rollout_pct,
            metadata=json.dumps(metadata or {}),
            created_by=created_by,
        )
        return {"id": fid, "flag_key": flag_key}

    async def update_flag(
        self,
        flag_id: str,
        updated_by: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        category: Optional[str] = None,
        is_active: Optional[bool] = None,
        target_type: Optional[str] = None,
        targets: Optional[list] = None,
        rollout_pct: Optional[int] = None,
        metadata: Optional[dict] = None,
    ) -> dict:
        flag = await self._repo.find_by_id(flag_id)
        if not flag:
            raise ValueError("Flag not found")
        new_cat = category if category is not None else flag.category
        if new_cat not in VALID_CATEGORIES:
            raise ValueError(f"Invalid category: {new_cat}")
        new_tt = target_type if target_type is not None else flag.target_type
        if new_tt not in VALID_TARGET_TYPES:
            raise ValueError(f"Invalid target_type: {new_tt}")
        new_pct = rollout_pct if rollout_pct is not None else flag.rollout_pct
        if new_pct < 0 or new_pct > 100:
            raise ValueError("rollout_pct must be 0-100")

        await self._repo.update(
            flag_id=flag_id,
            name=name if name is not None else flag.name,
            description=description
            if description is not None
            else (flag.description or ""),
            category=new_cat,
            is_active=1
            if (is_active if is_active is not None else flag.is_active)
            else 0,
            target_type=new_tt,
            targets=json.dumps(targets if targets is not None else flag.targets),
            rollout_pct=new_pct,
            metadata=json.dumps(
                metadata if metadata is not None else (flag.metadata or {})
            ),
            updated_by=updated_by,
        )
        updated = await self._repo.find_by_id(flag_id)
        return updated.to_dict(scope="admin") if updated else {"id": flag_id}

    async def delete_flag(self, flag_id: str) -> None:
        flag = await self._repo.find_by_id(flag_id)
        if not flag:
            raise ValueError("Flag not found")
        await self._repo.delete(flag_id)

    async def toggle_flag(self, flag_id: str, updated_by: str) -> dict:
        flag = await self._repo.find_by_id(flag_id)
        if not flag:
            raise ValueError("Flag not found")
        await self._repo.toggle(flag_id, updated_by)
        toggled = await self._repo.find_by_id(flag_id)
        return toggled.to_dict(scope="admin") if toggled else {"id": flag_id}
