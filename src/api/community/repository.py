"""Phase 9 Step 32 — Community repository."""

from db.repository import BaseRepository
from api.community import queries as Q
from models.community.model import CommunitySpace, SpaceMember, CommunityPost


class CommunityRepository(BaseRepository):
    def _one(self, cls, row):
        return self.map_one(row, cls)

    def _many(self, rows, cls):
        return self.map_many(rows, cls)

    # ── Spaces ───────────────────────────────────────────────
    async def list_spaces(self, org_id, limit, offset):
        return self._many(
            await self.find_all(Q.LIST_SPACES, org_id, limit, offset), CommunitySpace
        )

    async def list_spaces_public(self, limit, offset):
        return self._many(
            await self.find_all(Q.LIST_SPACES_PUBLIC, limit, offset), CommunitySpace
        )

    async def get_space(self, sid):
        return self._one(CommunitySpace, await self.find_one(Q.GET_SPACE, sid))

    async def create_space(
        self,
        sid,
        org_id,
        name,
        slug,
        description,
        cover_image_url,
        icon,
        space_type,
        membership_tier,
        created_by,
    ):
        await self.execute(
            Q.INSERT_SPACE,
            sid,
            org_id,
            name,
            slug,
            description,
            cover_image_url,
            icon,
            space_type,
            membership_tier,
            created_by,
        )

    async def update_space(
        self, sid, name, description, cover_image_url, icon, space_type, membership_tier
    ):
        await self.execute(
            Q.UPDATE_SPACE,
            name,
            description,
            cover_image_url,
            icon,
            space_type,
            membership_tier,
            sid,
        )

    async def delete_space(self, sid):
        await self.execute(Q.DELETE_SPACE, sid)

    async def increment_member_count(self, sid):
        await self.execute(Q.INCREMENT_MEMBER_COUNT, sid)

    async def decrement_member_count(self, sid):
        await self.execute(Q.DECREMENT_MEMBER_COUNT, sid)

    async def increment_post_count(self, sid):
        await self.execute(Q.INCREMENT_POST_COUNT, sid)

    async def decrement_post_count(self, sid):
        await self.execute(Q.DECREMENT_POST_COUNT, sid)

    # ── Members ──────────────────────────────────────────────
    async def list_members(self, space_id, limit, offset):
        return self._many(
            await self.find_all(Q.LIST_MEMBERS, space_id, limit, offset), SpaceMember
        )

    async def get_member(self, space_id, user_id):
        return self._one(
            SpaceMember, await self.find_one(Q.GET_MEMBER, space_id, user_id)
        )

    async def add_member(self, space_id, user_id, role="member"):
        await self.execute(Q.INSERT_MEMBER, space_id, user_id, role)

    async def update_member_role(self, space_id, user_id, role):
        await self.execute(Q.UPDATE_MEMBER_ROLE, role, space_id, user_id)

    async def remove_member(self, space_id, user_id):
        await self.execute(Q.DELETE_MEMBER, space_id, user_id)

    # ── Posts ────────────────────────────────────────────────
    async def list_posts(self, space_id, limit, offset):
        return self._many(
            await self.find_all(Q.LIST_POSTS, space_id, limit, offset), CommunityPost
        )

    async def list_replies(self, parent_id, limit, offset):
        return self._many(
            await self.find_all(Q.LIST_REPLIES, parent_id, limit, offset), CommunityPost
        )

    async def get_post(self, pid):
        return self._one(CommunityPost, await self.find_one(Q.GET_POST, pid))

    async def create_post(
        self,
        pid,
        space_id,
        author_id,
        parent_id,
        title,
        body,
        post_type,
        article_id,
        status,
        pinned,
    ):
        await self.execute(
            Q.INSERT_POST,
            pid,
            space_id,
            author_id,
            parent_id,
            title,
            body,
            post_type,
            article_id,
            status,
            int(pinned),
        )

    async def update_post(self, pid, title, body, post_type, status, pinned):
        await self.execute(
            Q.UPDATE_POST, title, body, post_type, status, int(pinned), pid
        )

    async def delete_post(self, pid):
        await self.execute(Q.DELETE_POST, pid)

    async def increment_reply_count(self, pid):
        await self.execute(Q.INCREMENT_REPLY_COUNT, pid)

    async def increment_like_count(self, pid):
        await self.execute(Q.INCREMENT_LIKE_COUNT, pid)
