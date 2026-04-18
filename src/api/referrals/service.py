"""Phase 9 Step 34 — Referral service."""

import secrets
from api.referrals.repository import ReferralRepository
from utils.helpers import new_id, paginate


class ReferralService:
    def __init__(self, env, ctx=None):
        self._repo = ReferralRepository(env.DB, ctx)

    async def get_or_create_code(self, user_id):
        existing = await self._repo.get_code_by_user(user_id)
        if existing:
            return existing.to_dict()
        cid = new_id()
        code = secrets.token_urlsafe(8)
        await self._repo.create_code(cid, user_id, code)
        rc = await self._repo.get_code(cid)
        return rc.to_dict()

    async def get_stats(self, user_id):
        rc = await self._repo.get_code_by_user(user_id)
        if not rc:
            raise ValueError("No referral code found")
        return rc.to_dict()

    async def track_event(self, code, event_type, referred_user_id="", metadata=None):
        rc = await self._repo.get_code_by_code(code)
        if not rc:
            raise ValueError("Invalid referral code")
        eid = new_id()
        await self._repo.create_event(
            eid, rc.id, event_type, referred_user_id, metadata or {}
        )
        if event_type == "click":
            await self._repo.increment_clicks(rc.id)
        elif event_type == "signup":
            await self._repo.increment_signups(rc.id)
        elif event_type == "conversion":
            await self._repo.increment_conversions(rc.id)
        return {"id": eid}

    async def list_events(self, user_id, page=1, limit=20):
        rc = await self._repo.get_code_by_user(user_id)
        if not rc:
            raise ValueError("No referral code found")
        lim, off = paginate(page, limit)
        items = await self._repo.list_events(rc.id, lim, off)
        return {"events": [e.to_dict() for e in items], "page": page, "limit": lim}
