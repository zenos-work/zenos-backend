"""Phase 11 Step 41 — Subdomain provisioning repository."""

from db.repository import BaseRepository
from api.subdomains import queries as Q
from models.subdomain.model import SubdomainConfig, OrgContext


class SubdomainRepository(BaseRepository):
    def _one(self, cls, row):
        return self.map_one(row, cls)

    def _many(self, rows, cls):
        return self.map_many(rows, cls)

    # ── Subdomain CRUD ───────────────────────────────────────
    async def get_by_subdomain(self, subdomain):
        return self._one(
            SubdomainConfig, await self.find_one(Q.GET_BY_SUBDOMAIN, subdomain)
        )

    async def get_by_org(self, org_id):
        return self._one(SubdomainConfig, await self.find_one(Q.GET_BY_ORG, org_id))

    async def list_all(self, limit=50, offset=0):
        return self._many(
            await self.find_all(Q.LIST_ALL, limit, offset), SubdomainConfig
        )

    async def create(
        self, org_id, subdomain, provisioned_by, custom_domain="", settings="{}"
    ):
        await self.execute(
            Q.INSERT_SUBDOMAIN,
            org_id,
            subdomain,
            provisioned_by,
            custom_domain,
            settings,
        )

    async def update_subdomain(self, org_id, new_subdomain):
        await self.execute(Q.UPDATE_SUBDOMAIN, new_subdomain, org_id)

    async def deactivate(self, org_id):
        await self.execute(Q.DEACTIVATE_SUBDOMAIN, org_id)

    async def activate(self, org_id):
        await self.execute(Q.ACTIVATE_SUBDOMAIN, org_id)

    async def delete(self, org_id):
        await self.execute(Q.DELETE_SUBDOMAIN, org_id)

    # ── Tenant routing ───────────────────────────────────────
    async def resolve_org(self, subdomain):
        return self._one(
            OrgContext, await self.find_one(Q.RESOLVE_ORG_BY_SUBDOMAIN, subdomain)
        )

    async def org_info(self, subdomain):
        return await self.find_one(Q.ORG_INFO_BY_SUBDOMAIN, subdomain)
