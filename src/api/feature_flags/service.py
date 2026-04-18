import json
from dataclasses import dataclass
from typing import Optional
from api.feature_flags.repository import FeatureFlagRepository
from models.feature_flag.model import (
    FeatureFlag,
    VALID_CATEGORIES,
    VALID_TARGET_TYPES,
)
from utils.helpers import new_id
from models.common.enums import NotificationType


VALID_ANNOUNCEMENT_CHANNELS = {"in_app", "email", "push"}


@dataclass
class AnnouncementPreview:
    action: str
    message: str
    scope: str
    channels: list[str]
    recipient_count: int
    channel_recipient_counts: dict[str, int]

    def to_dict(self) -> dict:
        return {
            "action": self.action,
            "message": self.message,
            "scope": self.scope,
            "channels": self.channels,
            "recipient_count": self.recipient_count,
            "channel_recipient_counts": self.channel_recipient_counts,
        }


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
        if is_active:
            created = await self._repo.find_by_id(fid)
            if created:
                await self._announce_flag_status_change(
                    created,
                    actor_id=created_by,
                    action="enabled",
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
        prev_is_active = bool(flag.is_active)
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
        if updated and prev_is_active != bool(updated.is_active):
            await self._announce_flag_status_change(
                updated,
                actor_id=updated_by,
                action="enabled" if bool(updated.is_active) else "disabled",
            )
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
        if toggled:
            await self._announce_flag_status_change(
                toggled,
                actor_id=updated_by,
                action="enabled" if bool(toggled.is_active) else "disabled",
            )
        return toggled.to_dict(scope="admin") if toggled else {"id": flag_id}

    async def preview_announcement(self, payload: dict) -> dict:
        flag = self._preview_flag_from_payload(payload)
        action = (
            str(payload.get("action") or ("enabled" if flag.is_active else "disabled"))
            .strip()
            .lower()
        )
        if action not in {"enabled", "disabled"}:
            raise ValueError("action must be 'enabled' or 'disabled'")
        recipients = await self._resolve_flag_recipients(flag)
        delivery_plan = await self._resolve_delivery_plan(flag, recipients)
        return AnnouncementPreview(
            action=action,
            message=self._build_announcement_message(flag, action),
            scope=self._format_scope_text(flag),
            channels=list(delivery_plan.keys()),
            recipient_count=len(recipients),
            channel_recipient_counts={
                channel: len(user_ids) for channel, user_ids in delivery_plan.items()
            },
        ).to_dict()

    async def _announce_flag_status_change(
        self, flag, actor_id: str, action: str
    ) -> None:
        recipients = await self._resolve_flag_recipients(flag)
        if not recipients:
            return
        message = self._build_announcement_message(flag, action)
        group_key = f"feature_flag:{flag.flag_key}:{action}"
        delivery_plan = await self._resolve_delivery_plan(flag, recipients)

        for channel, channel_recipients in delivery_plan.items():
            for user_id in channel_recipients:
                await self._repo.insert_notification(
                    nid=new_id(),
                    user_id=user_id,
                    actor_id=actor_id,
                    type_=NotificationType.FEATURE_ANNOUNCEMENT,
                    message=message,
                    channel=channel,
                    delivery_status="delivered" if channel == "in_app" else "pending",
                    group_key=group_key,
                )

    def _build_announcement_message(self, flag, action: str) -> str:
        metadata = flag.metadata or {}
        announcement = metadata.get("announcement") or {}
        scope_text = self._format_scope_text(flag)

        title = (
            announcement.get(f"{action}_title")
            or announcement.get("title")
            or f"Feature {action.title()}: {flag.name}"
        )
        summary = (
            announcement.get(f"{action}_summary")
            or announcement.get("summary")
            or f"{flag.name} ({flag.flag_key}) was {action} by superadmin."
        )

        lines = [title, summary, f"Scope: {scope_text}."]

        effective_at = announcement.get("effective_at") or "Effective now."
        if effective_at:
            lines.append(f"Effective: {effective_at}")

        details = announcement.get("details")
        if details:
            lines.append(f"Details: {details}")

        action_required = announcement.get("action_required")
        if action_required:
            lines.append(f"Action required: {action_required}")

        reason = announcement.get("reason")
        if reason and action == "disabled":
            lines.append(f"Reason: {reason}")

        support_contact = announcement.get("support_contact")
        if support_contact:
            lines.append(f"Support: {support_contact}")

        rollback_plan = announcement.get("rollback_plan")
        if rollback_plan:
            lines.append(f"Rollback plan: {rollback_plan}")

        return " ".join(str(line).strip() for line in lines if str(line).strip())

    def _preview_flag_from_payload(self, payload: dict) -> FeatureFlag:
        metadata = payload.get("metadata") or {}
        return FeatureFlag(
            id=str(payload.get("id") or "preview-flag"),
            flag_key=str(payload.get("flag_key") or "preview_flag"),
            name=str(payload.get("name") or "Preview Feature"),
            description=str(payload.get("description") or "") or None,
            category=str(payload.get("category") or "general"),
            is_active=bool(payload.get("is_active", False)),
            target_type=str(payload.get("target_type") or "global"),
            targets=payload.get("targets") or [],
            rollout_pct=int(payload.get("rollout_pct") or 0),
            metadata=metadata,
            created_by=str(payload.get("created_by") or "preview"),
            updated_by=str(
                payload.get("updated_by") or payload.get("created_by") or "preview"
            ),
            created_at="",
            updated_at="",
        )

    def _format_scope_text(self, flag) -> str:
        targets = flag.targets or []
        scope_text = f"{flag.target_type}"
        if targets:
            scope_text = f"{flag.target_type}: {', '.join(str(t) for t in targets[:8])}"
            if len(targets) > 8:
                scope_text = f"{scope_text}, ..."
        if flag.target_type == "percentage":
            scope_text = f"percentage rollout ({flag.rollout_pct}%)"
        return scope_text

    async def _resolve_delivery_plan(
        self, flag, recipients: list[str]
    ) -> dict[str, list[str]]:
        channels = self._get_delivery_channels(flag)
        plan: dict[str, list[str]] = {}

        if "in_app" in channels:
            plan["in_app"] = sorted(set(recipients))

        if "email" in channels:
            email_recipients = await self._repo.list_user_ids_with_enabled_pref(
                recipients,
                NotificationType.FEATURE_ANNOUNCEMENT,
                "email",
            )
            plan["email"] = sorted(set(email_recipients))

        if "push" in channels:
            push_pref_recipients = await self._repo.list_user_ids_with_enabled_pref(
                recipients,
                NotificationType.FEATURE_ANNOUNCEMENT,
                "push",
            )
            push_ready_recipients = (
                await self._repo.list_user_ids_with_active_push_subs(
                    push_pref_recipients
                )
            )
            plan["push"] = sorted(set(push_ready_recipients))

        return plan

    def _get_delivery_channels(self, flag) -> list[str]:
        metadata = flag.metadata or {}
        delivery = metadata.get("delivery") or {}
        announcement = metadata.get("announcement") or {}
        raw_channels = (
            delivery.get("channels") or announcement.get("channels") or ["in_app"]
        )
        channels: list[str] = []
        for raw_channel in raw_channels:
            channel = str(raw_channel or "").strip()
            if channel in VALID_ANNOUNCEMENT_CHANNELS and channel not in channels:
                channels.append(channel)
        if "in_app" not in channels:
            channels.insert(0, "in_app")
        return channels

    async def _resolve_flag_recipients(self, flag) -> list[str]:
        target_type = (flag.target_type or "global").strip()
        targets = [str(t).strip() for t in (flag.targets or []) if str(t).strip()]

        if target_type == "global":
            users = await self._repo.list_active_user_ids()
            return sorted(set(users))

        if target_type == "user_ids":
            users = await self._repo.list_active_user_ids_by_ids(targets)
            return sorted(set(users))

        if target_type == "user_roles":
            users = await self._repo.list_active_user_ids_by_roles(targets)
            return sorted(set(users))

        if target_type == "org_ids":
            users = await self._repo.list_active_user_ids_by_org_ids(targets)
            return sorted(set(users))

        if target_type == "org_tiers":
            users = await self._repo.list_active_user_ids_by_org_tiers(targets)
            return sorted(set(users))

        if target_type == "membership_tiers":
            users = await self._repo.list_active_user_ids_by_membership_tiers(targets)
            return sorted(set(users))

        if target_type == "percentage":
            candidates = await self._repo.list_active_user_ids()
            users = [uid for uid in candidates if flag.evaluate(user_id=uid)]
            return sorted(set(users))

        return []
