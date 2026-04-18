"""Phase 9 Step 32 — Community service."""

from api.community.repository import CommunityRepository
from utils.helpers import new_id, paginate


class CommunityService:
    def __init__(self, env, ctx=None):
        self._repo = CommunityRepository(env.DB, ctx)

    # ── Spaces ───────────────────────────────────────────────
    async def list_spaces(self, org_id, page=1, limit=20):
        lim, off = paginate(page, limit)
        items = await self._repo.list_spaces(org_id, lim, off)
        return {"spaces": [s.to_dict() for s in items], "page": page, "limit": lim}

    async def list_spaces_public(self, page=1, limit=20):
        lim, off = paginate(page, limit)
        items = await self._repo.list_spaces_public(lim, off)
        return {"spaces": [s.to_dict() for s in items], "page": page, "limit": lim}

    async def get_space(self, sid):
        s = await self._repo.get_space(sid)
        if not s:
            raise ValueError("Space not found")
        return s.to_dict()

    async def create_space(
        self,
        org_id,
        created_by,
        name,
        slug,
        description="",
        cover_image_url="",
        icon="",
        space_type="open",
        membership_tier="",
    ):
        sid = new_id()
        await self._repo.create_space(
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
        return {"id": sid}

    async def update_space(self, sid, **kwargs):
        existing = await self._repo.get_space(sid)
        if not existing:
            raise ValueError("Space not found")
        await self._repo.update_space(
            sid,
            name=kwargs.get("name") or existing.name,
            description=kwargs.get("description")
            if kwargs.get("description") is not None
            else existing.description,
            cover_image_url=kwargs.get("cover_image_url")
            if kwargs.get("cover_image_url") is not None
            else existing.cover_image_url,
            icon=kwargs.get("icon")
            if kwargs.get("icon") is not None
            else existing.icon,
            space_type=kwargs.get("space_type") or existing.space_type,
            membership_tier=kwargs.get("membership_tier")
            if kwargs.get("membership_tier") is not None
            else existing.membership_tier,
        )
        return {"id": sid}

    async def delete_space(self, sid):
        existing = await self._repo.get_space(sid)
        if not existing:
            raise ValueError("Space not found")
        await self._repo.delete_space(sid)

    # ── Members ──────────────────────────────────────────────
    async def list_members(self, space_id, page=1, limit=20):
        lim, off = paginate(page, limit)
        items = await self._repo.list_members(space_id, lim, off)
        return {"members": [m.to_dict() for m in items], "page": page, "limit": lim}

    async def join_space(self, space_id, user_id):
        existing = await self._repo.get_member(space_id, user_id)
        if existing:
            raise ValueError("Already a member")
        await self._repo.add_member(space_id, user_id)
        await self._repo.increment_member_count(space_id)
        return {"joined": True}

    async def leave_space(self, space_id, user_id):
        existing = await self._repo.get_member(space_id, user_id)
        if not existing:
            raise ValueError("Not a member")
        await self._repo.remove_member(space_id, user_id)
        await self._repo.decrement_member_count(space_id)
        return {"left": True}

    async def update_member_role(self, space_id, user_id, role):
        existing = await self._repo.get_member(space_id, user_id)
        if not existing:
            raise ValueError("Member not found")
        await self._repo.update_member_role(space_id, user_id, role)
        return {"updated": True}

    # ── Posts ────────────────────────────────────────────────
    async def list_posts(self, space_id, page=1, limit=20):
        lim, off = paginate(page, limit)
        items = await self._repo.list_posts(space_id, lim, off)
        return {"posts": [p.to_dict() for p in items], "page": page, "limit": lim}

    async def list_replies(self, parent_id, page=1, limit=20):
        lim, off = paginate(page, limit)
        items = await self._repo.list_replies(parent_id, lim, off)
        return {"replies": [p.to_dict() for p in items], "page": page, "limit": lim}

    async def get_post(self, pid):
        p = await self._repo.get_post(pid)
        if not p:
            raise ValueError("Post not found")
        return p.to_dict()

    async def create_post(
        self,
        space_id,
        author_id,
        title="",
        body="",
        post_type="discussion",
        article_id="",
        parent_id="",
        status="published",
        pinned=False,
    ):
        pid = new_id()
        await self._repo.create_post(
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
        )
        await self._repo.increment_post_count(space_id)
        if parent_id:
            await self._repo.increment_reply_count(parent_id)
        return {"id": pid}

    async def update_post(self, pid, **kwargs):
        existing = await self._repo.get_post(pid)
        if not existing:
            raise ValueError("Post not found")
        await self._repo.update_post(
            pid,
            title=kwargs.get("title")
            if kwargs.get("title") is not None
            else existing.title,
            body=kwargs.get("body")
            if kwargs.get("body") is not None
            else existing.body,
            post_type=kwargs.get("post_type") or existing.post_type,
            status=kwargs.get("status") or existing.status,
            pinned=kwargs.get("pinned")
            if kwargs.get("pinned") is not None
            else existing.pinned,
        )
        return {"id": pid}

    async def delete_post(self, pid):
        existing = await self._repo.get_post(pid)
        if not existing:
            raise ValueError("Post not found")
        await self._repo.delete_post(pid)
        await self._repo.decrement_post_count(existing.space_id)

    async def like_post(self, pid):
        existing = await self._repo.get_post(pid)
        if not existing:
            raise ValueError("Post not found")
        await self._repo.increment_like_count(pid)
        return {"liked": True}
