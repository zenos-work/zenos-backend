"""Phase 9 Step 34 — Referral repository."""

import json
from db.repository import BaseRepository
from api.referrals import queries as Q
from models.referral.model import ReferralCode, ReferralEvent


class ReferralRepository(BaseRepository):
    def _one(self, cls, row):
        return self.map_one(row, cls)

    def _many(self, rows, cls):
        return self.map_many(rows, cls)

    async def get_code_by_user(self, user_id):
        return self._one(ReferralCode, await self.find_one(Q.GET_CODE_BY_USER, user_id))

    async def get_code_by_code(self, code):
        return self._one(ReferralCode, await self.find_one(Q.GET_CODE_BY_CODE, code))

    async def get_code(self, cid):
        return self._one(ReferralCode, await self.find_one(Q.GET_CODE, cid))

    async def create_code(self, cid, user_id, code):
        await self.execute(Q.INSERT_CODE, cid, user_id, code)

    async def increment_clicks(self, cid):
        await self.execute(Q.INCREMENT_CLICKS, cid)

    async def increment_signups(self, cid):
        await self.execute(Q.INCREMENT_SIGNUPS, cid)

    async def increment_conversions(self, cid):
        await self.execute(Q.INCREMENT_CONVERSIONS, cid)

    async def list_events(self, code_id, limit, offset):
        return self._many(
            await self.find_all(Q.LIST_EVENTS, code_id, limit, offset), ReferralEvent
        )

    async def create_event(self, eid, code_id, event_type, referred_user_id, metadata):
        await self.execute(
            Q.INSERT_EVENT,
            eid,
            code_id,
            event_type,
            referred_user_id,
            json.dumps(metadata),
        )
