import types
import json

import pytest

from api.feature_flags import service as feature_flags_service_module
from api.feature_flags.repository import FeatureFlagRepository
from api.feature_flags.service import FeatureFlagService


class _Env:
    DB = object()


class FlagObj(types.SimpleNamespace):
    def to_dict(self, scope=None):
        data = dict(self.__dict__)
        if scope is not None:
            data["scope"] = scope
        return data

    def evaluate(self, **_kwargs):
        return bool(self.is_active)


class RepoStub:
    def __init__(self):
        self.by_id = {}
        self.by_key = {}
        self.notifications = []

    async def find_active(self):
        return list(self.by_id.values())

    async def find_by_key(self, flag_key):
        return self.by_key.get(flag_key)

    async def find_by_category(self, category):
        return [f for f in self.by_id.values() if f.category == category]

    async def find_all(self):
        return list(self.by_id.values())

    async def count_all(self):
        return len(self.by_id)

    async def find_by_id(self, flag_id):
        return self.by_id.get(flag_id)

    async def create(self, **kwargs):
        raw_targets = kwargs.get("targets", "[]")
        targets = (
            json.loads(raw_targets) if isinstance(raw_targets, str) else raw_targets
        )
        raw_metadata = kwargs.get("metadata", "{}")
        metadata = (
            json.loads(raw_metadata) if isinstance(raw_metadata, str) else raw_metadata
        )
        f = FlagObj(
            id=kwargs["flag_id"],
            flag_key=kwargs["flag_key"],
            name=kwargs["name"],
            description=kwargs["description"],
            category=kwargs["category"],
            is_active=kwargs["is_active"],
            target_type=kwargs["target_type"],
            targets=targets,
            rollout_pct=kwargs["rollout_pct"],
            metadata=metadata,
        )
        self.by_id[f.id] = f
        self.by_key[f.flag_key] = f

    async def update(self, **kwargs):
        f = self.by_id[kwargs["flag_id"]]
        f.name = kwargs["name"]
        f.description = kwargs["description"]
        f.category = kwargs["category"]
        f.is_active = kwargs["is_active"]
        f.target_type = kwargs["target_type"]
        f.rollout_pct = kwargs["rollout_pct"]
        raw_targets = kwargs.get("targets", "[]")
        f.targets = (
            json.loads(raw_targets) if isinstance(raw_targets, str) else raw_targets
        )
        raw_metadata = kwargs.get("metadata", "{}")
        f.metadata = (
            json.loads(raw_metadata) if isinstance(raw_metadata, str) else raw_metadata
        )

    async def delete(self, flag_id):
        f = self.by_id.pop(flag_id, None)
        if f:
            self.by_key.pop(f.flag_key, None)

    async def toggle(self, flag_id, _updated_by):
        f = self.by_id[flag_id]
        f.is_active = 0 if f.is_active else 1

    async def list_active_user_ids(self):
        return ["u1", "u2", "u3"]

    async def list_active_user_ids_by_roles(self, roles):
        return ["u-role"] if "AUTHOR" in roles else []

    async def list_active_user_ids_by_ids(self, user_ids):
        return [u for u in user_ids if u in {"u1", "u2", "u3"}]

    async def list_active_user_ids_by_membership_tiers(self, tiers):
        return ["u-tier"] if "creator_pro" in tiers else []

    async def list_active_user_ids_by_org_ids(self, org_ids):
        return ["u-org"] if "org-1" in org_ids else []

    async def list_active_user_ids_by_org_tiers(self, org_tiers):
        return ["u-org-tier"] if "enterprise" in org_tiers else []

    async def list_user_ids_with_enabled_pref(
        self, user_ids, notification_type, channel
    ):
        if notification_type != "FEATURE_ANNOUNCEMENT":
            return []
        if channel == "email":
            return [uid for uid in user_ids if uid in {"u1", "u-role", "u-tier"}]
        if channel == "push":
            return [uid for uid in user_ids if uid in {"u-role", "u-org-tier"}]
        return []

    async def list_user_ids_with_active_push_subs(self, user_ids):
        return [uid for uid in user_ids if uid != "u-org-tier"]

    async def insert_notification(self, **kwargs):
        self.notifications.append(kwargs)


@pytest.fixture
def ff_service(monkeypatch):
    svc = FeatureFlagService(_Env())
    svc._repo = RepoStub()
    monkeypatch.setattr(feature_flags_service_module, "new_id", lambda: "ff-new")
    return svc


@pytest.mark.asyncio
async def test_feature_flags_service_main_flows(ff_service):
    svc = ff_service

    await svc.create_flag("alpha", "Alpha", "admin", category="general", is_active=True)
    all_eval = await svc.evaluate_all(user_id="u1")
    assert all_eval["alpha"] is True

    one = await svc.evaluate_one("alpha", user_id="u1")
    assert one is True
    assert await svc.evaluate_one("missing") is False

    await svc.require_feature("alpha")
    with pytest.raises(PermissionError, match="not available"):
        await svc.require_feature("missing")

    listed_all = await svc.list_flags()
    assert listed_all["total"] == 1
    listed_cat = await svc.list_flags(category="general")
    assert listed_cat["flags"][0]["flag_key"] == "alpha"

    got = await svc.get_flag("ff-new")
    assert got["id"] == "ff-new"

    updated = await svc.update_flag(
        "ff-new", updated_by="admin", name="Alpha 2", rollout_pct=25
    )
    assert updated["name"] == "Alpha 2"
    assert updated["rollout_pct"] == 25

    toggled = await svc.toggle_flag("ff-new", updated_by="admin")
    assert toggled["is_active"] == 0

    await svc.delete_flag("ff-new")
    with pytest.raises(ValueError, match="Flag not found"):
        await svc.get_flag("ff-new")


@pytest.mark.asyncio
async def test_feature_flags_service_announcements_by_scope(ff_service):
    svc = ff_service

    await svc.create_flag(
        "ff-user-ids",
        "User IDs",
        "admin",
        is_active=True,
        target_type="user_ids",
        targets=["u1", "missing"],
    )

    created = await svc.get_flag("ff-new")
    assert created["flag_key"] == "ff-user-ids"
    assert len(svc._repo.notifications) == 1
    assert svc._repo.notifications[0]["user_id"] == "u1"
    assert svc._repo.notifications[0]["channel"] == "in_app"

    svc._repo.notifications.clear()

    await svc.create_flag(
        "ff-role",
        "Role",
        "admin",
        is_active=False,
        target_type="user_roles",
        targets=["AUTHOR"],
    )
    await svc.toggle_flag("ff-new", updated_by="admin")
    assert len(svc._repo.notifications) == 1
    assert svc._repo.notifications[0]["user_id"] == "u-role"

    svc._repo.notifications.clear()
    await svc.update_flag(
        "ff-new",
        updated_by="admin",
        is_active=False,
    )
    assert len(svc._repo.notifications) == 1
    assert "was disabled" in svc._repo.notifications[0]["message"]


@pytest.mark.asyncio
async def test_feature_flags_service_custom_announcement_metadata(ff_service):
    svc = ff_service

    await svc.create_flag(
        "ff-custom-announcement",
        "Custom Announcement",
        "admin",
        is_active=True,
        target_type="user_roles",
        targets=["AUTHOR"],
        metadata={
            "announcement": {
                "enabled_title": "New Capability Available",
                "enabled_summary": "Collaboration tools are now enabled for pilot users.",
                "details": "Draft sharing and review access are now visible in the editor.",
                "action_required": "Refresh the editor to see the new controls.",
                "support_contact": "#zenos-support",
                "rollback_plan": "Disable the flag if elevated error rates are observed.",
            }
        },
    )

    assert len(svc._repo.notifications) == 1
    enabled_message = svc._repo.notifications[0]["message"]
    assert "New Capability Available" in enabled_message
    assert "Collaboration tools are now enabled for pilot users." in enabled_message
    assert (
        "Action required: Refresh the editor to see the new controls."
        in enabled_message
    )
    assert "Support: #zenos-support" in enabled_message

    svc._repo.notifications.clear()

    await svc.update_flag(
        "ff-new",
        updated_by="admin",
        is_active=False,
        metadata={
            "announcement": {
                "disabled_title": "Feature Temporarily Disabled",
                "disabled_summary": "The pilot feature has been paused for affected users.",
                "reason": "We detected inconsistent permissions in shared drafts.",
                "support_contact": "support@zenos.work",
            }
        },
    )

    assert len(svc._repo.notifications) == 1
    disabled_message = svc._repo.notifications[0]["message"]
    assert "Feature Temporarily Disabled" in disabled_message
    assert "The pilot feature has been paused for affected users." in disabled_message
    assert (
        "Reason: We detected inconsistent permissions in shared drafts."
        in disabled_message
    )
    assert "Support: support@zenos.work" in disabled_message


@pytest.mark.asyncio
async def test_feature_flags_service_preview_and_multichannel_delivery(ff_service):
    svc = ff_service

    preview = await svc.preview_announcement(
        {
            "flag_key": "ff-preview",
            "name": "Preview Feature",
            "is_active": True,
            "action": "enabled",
            "target_type": "user_roles",
            "targets": ["AUTHOR"],
            "metadata": {
                "announcement": {
                    "enabled_title": "Preview Ready",
                    "enabled_summary": "Feature is being rolled out.",
                },
                "delivery": {
                    "channels": ["email", "push"],
                },
            },
        }
    )

    assert preview["action"] == "enabled"
    assert "Preview Ready" in preview["message"]
    assert preview["recipient_count"] == 1
    assert preview["channels"] == ["in_app", "email", "push"]
    assert preview["channel_recipient_counts"]["in_app"] == 1
    assert preview["channel_recipient_counts"]["email"] == 1
    assert preview["channel_recipient_counts"]["push"] == 1

    await svc.create_flag(
        "ff-multichannel",
        "Multi Channel",
        "admin",
        is_active=True,
        target_type="user_roles",
        targets=["AUTHOR"],
        metadata={
            "delivery": {"channels": ["email", "push"]},
        },
    )
    channels = [item["channel"] for item in svc._repo.notifications]
    assert channels == ["in_app", "email", "push"]


@pytest.mark.asyncio
async def test_feature_flags_service_validations(ff_service):
    svc = ff_service

    with pytest.raises(ValueError, match="Invalid category"):
        await svc.create_flag("bad-cat", "Bad", "admin", category="nope")

    with pytest.raises(ValueError, match="Invalid target_type"):
        await svc.create_flag("bad-tt", "Bad", "admin", target_type="nope")

    with pytest.raises(ValueError, match="rollout_pct"):
        await svc.create_flag("bad-pct", "Bad", "admin", rollout_pct=101)

    await svc.create_flag("dup", "Dup", "admin")
    with pytest.raises(ValueError, match="already exists"):
        await svc.create_flag("dup", "Dup2", "admin")

    with pytest.raises(ValueError, match="Flag not found"):
        await svc.update_flag("missing", updated_by="admin")

    with pytest.raises(ValueError, match="Invalid category"):
        await svc.update_flag("ff-new", updated_by="admin", category="invalid")

    with pytest.raises(ValueError, match="Invalid target_type"):
        await svc.update_flag("ff-new", updated_by="admin", target_type="invalid")

    with pytest.raises(ValueError, match="rollout_pct"):
        await svc.update_flag("ff-new", updated_by="admin", rollout_pct=-1)

    with pytest.raises(ValueError, match="Flag not found"):
        await svc.delete_flag("missing")

    with pytest.raises(ValueError, match="Flag not found"):
        await svc.toggle_flag("missing", updated_by="admin")


@pytest.mark.asyncio
async def test_feature_flags_repository_methods(monkeypatch):
    repo = FeatureFlagRepository(db=object())

    execute_calls = []
    find_one_calls = []
    find_all_calls = []

    async def _execute(sql, *params):
        execute_calls.append((sql, params))

    async def _find_one(sql, *params):
        find_one_calls.append((sql, params))
        return {"id": "f1", "c": 4}

    async def _find_all_rows(sql, *params):
        find_all_calls.append((sql, params))
        return [{"id": "f1"}, {"id": "f2"}]

    monkeypatch.setattr(repo, "execute", _execute)
    monkeypatch.setattr(repo, "find_one", _find_one)
    monkeypatch.setattr(repo, "find_all_rows", _find_all_rows)
    monkeypatch.setattr(repo, "map_one", lambda row, _model: row)
    monkeypatch.setattr(repo, "map_many", lambda rows, _model: rows)

    await repo.create(
        "f1",
        "alpha",
        "Alpha",
        "",
        "general",
        1,
        "global",
        "[]",
        0,
        "{}",
        "admin",
    )
    assert await repo.find_by_id("f1") == {"id": "f1", "c": 4}
    assert await repo.find_by_key("alpha") == {"id": "f1", "c": 4}
    assert await repo.find_all() == [{"id": "f1"}, {"id": "f2"}]
    assert await repo.find_active() == [{"id": "f1"}, {"id": "f2"}]
    assert await repo.find_by_category("general") == [{"id": "f1"}, {"id": "f2"}]
    assert await repo.count_all() == 4
    await repo.update(
        "f1",
        "Alpha 2",
        "desc",
        "general",
        0,
        "global",
        "[]",
        15,
        "{}",
        "admin",
    )
    await repo.delete("f1")
    await repo.toggle("f1", "admin")
    await repo.list_active_user_ids()
    await repo.list_active_user_ids_by_roles(["AUTHOR"])
    await repo.list_active_user_ids_by_ids(["u1"])
    await repo.list_active_user_ids_by_membership_tiers(["creator_pro"])
    await repo.list_active_user_ids_by_org_ids(["org-1"])
    await repo.list_active_user_ids_by_org_tiers(["enterprise"])
    await repo.list_user_ids_with_enabled_pref(["u1"], "FEATURE_ANNOUNCEMENT", "email")
    await repo.list_user_ids_with_active_push_subs(["u1"])
    await repo.insert_notification("n1", "u1", "admin", "FEATURE_ANNOUNCEMENT", "m")

    assert len(execute_calls) == 5
    assert len(find_one_calls) == 3
    assert len(find_all_calls) == 11
