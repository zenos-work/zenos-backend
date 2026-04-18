import secrets
from typing import Optional
from api.domains.repository import DomainRepository
from utils.helpers import new_id, paginate

VALID_RESOURCE_TYPES = {"newsletter", "publication", "blog", "landing_page"}
VALID_VERIFICATION_METHODS = {"cname", "txt"}


class DomainService:
    def __init__(self, env, ctx=None):
        self._repo = DomainRepository(env.DB, ctx)

    async def register_domain(
        self,
        user_id: str,
        domain: str,
        resource_type: str,
        verification_method: str = "cname",
        org_id: Optional[str] = None,
        resource_id: Optional[str] = None,
    ) -> dict:
        if resource_type not in VALID_RESOURCE_TYPES:
            raise ValueError(f"Invalid resource_type: {resource_type}")
        if verification_method not in VALID_VERIFICATION_METHODS:
            raise ValueError(f"Invalid verification_method: {verification_method}")
        existing = await self._repo.find_by_domain(domain)
        if existing:
            raise ValueError("Domain already registered")
        did = new_id()
        token = secrets.token_hex(16)
        await self._repo.create(
            did,
            user_id,
            domain,
            resource_type,
            verification_method,
            token,
            org_id,
            resource_id,
        )
        return {"id": did, "verification_token": token}

    async def list_domains(self, user_id: str, page: int = 1, limit: int = 20):
        _limit, offset = paginate(page, limit)
        items = await self._repo.find_by_user(user_id, _limit, offset)
        total = await self._repo.count_by_user(user_id)
        return {
            "domains": [d.to_dict() for d in items],
            "pagination": {
                "page": page,
                "limit": _limit,
                "total": total,
                "pages": (total + _limit - 1) // _limit if _limit else 0,
            },
        }

    async def verify_domain(self, domain_id: str, user_id: str) -> dict:
        dom = await self._repo.find_by_id(domain_id)
        if not dom or dom.user_id != user_id:
            raise ValueError("Domain not found")
        if dom.verification_status == "verified":
            raise ValueError("Domain already verified")
        # In production, this would verify DNS records.
        # For now, mark as verified.
        from datetime import datetime, timezone

        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        await self._repo.update_verification(domain_id, "verified", now, 1)
        return {"id": domain_id, "verification_status": "verified"}

    async def delete_domain(self, domain_id: str, user_id: str) -> None:
        dom = await self._repo.find_by_id(domain_id)
        if not dom or dom.user_id != user_id:
            raise ValueError("Domain not found")
        await self._repo.delete(domain_id, user_id)
