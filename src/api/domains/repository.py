from typing import Optional, List
from db.repository import BaseRepository
from api.domains import queries as Q
from models.domain.model import CustomDomain
from models.base import row_get


class DomainRepository(BaseRepository):
    async def create(
        self,
        domain_id: str,
        user_id: str,
        domain: str,
        resource_type: str,
        verification_method: str,
        verification_token: str,
        org_id: Optional[str] = None,
        resource_id: Optional[str] = None,
    ) -> None:
        await self.execute(
            Q.INSERT_DOMAIN,
            domain_id,
            org_id or "",
            user_id,
            domain,
            resource_type,
            resource_id or "",
            verification_method,
            verification_token,
        )

    async def find_by_user(
        self, user_id: str, limit: int, offset: int
    ) -> List[CustomDomain]:
        rows = await self.find_all(Q.SELECT_BY_USER, user_id, limit, offset)
        return self.map_many(rows, CustomDomain)

    async def count_by_user(self, user_id: str) -> int:
        row = await self.find_one(Q.COUNT_BY_USER, user_id)
        return row_get(row, "c", 0)

    async def find_by_id(self, domain_id: str) -> Optional[CustomDomain]:
        row = await self.find_one(Q.SELECT_BY_ID, domain_id)
        return self.map_one(row, CustomDomain)

    async def find_by_domain(self, domain: str) -> Optional[CustomDomain]:
        row = await self.find_one(Q.SELECT_BY_DOMAIN, domain)
        return self.map_one(row, CustomDomain)

    async def delete(self, domain_id: str, user_id: str) -> None:
        await self.execute(Q.DELETE_DOMAIN, domain_id, user_id)

    async def update_verification(
        self,
        domain_id: str,
        status: str,
        verified_at: Optional[str] = None,
        is_active: int = 0,
    ) -> None:
        await self.execute(
            Q.UPDATE_VERIFICATION, status, verified_at, is_active, domain_id
        )
