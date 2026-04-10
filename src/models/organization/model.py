from dataclasses import dataclass
from typing import Optional
from models.base import BaseModel, row_get


@dataclass
class Organization(BaseModel):
    id: str
    name: str
    slug: str
    plan_tier: str
    plan_status: str
    max_members: int
    max_workflows: int
    max_leads: int
    created_by: str
    created_at: str
    updated_at: str
    subdomain: Optional[str] = None
    logo_url: Optional[str] = None
    website: Optional[str] = None
    description: Optional[str] = None
    trial_ends_at: Optional[str] = None
    plan_started_at: Optional[str] = None
    stripe_customer_id: Optional[str] = None
    stripe_subscription_id: Optional[str] = None
    settings: Optional[str] = None

    def to_dict(self, scope: str = "public") -> dict:
        d = {
            "id": self.id,
            "name": self.name,
            "slug": self.slug,
            "subdomain": self.subdomain,
            "logo_url": self.logo_url,
            "website": self.website,
            "description": self.description,
            "plan_tier": self.plan_tier,
            "plan_status": self.plan_status,
            "max_members": self.max_members,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
        if scope == "admin":
            d["max_workflows"] = self.max_workflows
            d["max_leads"] = self.max_leads
            d["stripe_customer_id"] = self.stripe_customer_id
            d["stripe_subscription_id"] = self.stripe_subscription_id
            d["trial_ends_at"] = self.trial_ends_at
            d["plan_started_at"] = self.plan_started_at
            d["settings"] = self.settings
            d["created_by"] = self.created_by
        return {k: v for k, v in d.items() if v is not None}

    @classmethod
    def from_row(cls, row) -> "Organization":
        return cls(
            id=row_get(row, "id"),
            name=row_get(row, "name", ""),
            slug=row_get(row, "slug", ""),
            plan_tier=row_get(row, "plan_tier", "free"),
            plan_status=row_get(row, "plan_status", "active"),
            max_members=row_get(row, "max_members", 5),
            max_workflows=row_get(row, "max_workflows", 3),
            max_leads=row_get(row, "max_leads", 1000),
            created_by=row_get(row, "created_by", ""),
            created_at=row_get(row, "created_at", ""),
            updated_at=row_get(row, "updated_at", ""),
            subdomain=row_get(row, "subdomain"),
            logo_url=row_get(row, "logo_url"),
            website=row_get(row, "website"),
            description=row_get(row, "description"),
            trial_ends_at=row_get(row, "trial_ends_at"),
            plan_started_at=row_get(row, "plan_started_at"),
            stripe_customer_id=row_get(row, "stripe_customer_id"),
            stripe_subscription_id=row_get(row, "stripe_subscription_id"),
            settings=row_get(row, "settings"),
        )


@dataclass
class OrgMember(BaseModel):
    id: str
    org_id: str
    user_id: str
    org_role: str
    joined_at: str
    invited_by: Optional[str] = None

    def to_dict(self, scope: str = "public") -> dict:
        d = {
            "id": self.id,
            "org_id": self.org_id,
            "user_id": self.user_id,
            "org_role": self.org_role,
            "joined_at": self.joined_at,
        }
        if self.invited_by:
            d["invited_by"] = self.invited_by
        return d

    @classmethod
    def from_row(cls, row) -> "OrgMember":
        return cls(
            id=row_get(row, "id"),
            org_id=row_get(row, "org_id", ""),
            user_id=row_get(row, "user_id", ""),
            org_role=row_get(row, "org_role", "member"),
            joined_at=row_get(row, "joined_at", ""),
            invited_by=row_get(row, "invited_by"),
        )


@dataclass
class Team(BaseModel):
    id: str
    org_id: str
    name: str
    created_at: str
    updated_at: str
    description: Optional[str] = None
    created_by: Optional[str] = None

    def to_dict(self, scope: str = "public") -> dict:
        d = {
            "id": self.id,
            "org_id": self.org_id,
            "name": self.name,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
        if self.description:
            d["description"] = self.description
        return d

    @classmethod
    def from_row(cls, row) -> "Team":
        return cls(
            id=row_get(row, "id"),
            org_id=row_get(row, "org_id", ""),
            name=row_get(row, "name", ""),
            created_at=row_get(row, "created_at", ""),
            updated_at=row_get(row, "updated_at", ""),
            description=row_get(row, "description"),
            created_by=row_get(row, "created_by"),
        )


@dataclass
class TeamMember(BaseModel):
    team_id: str
    user_id: str
    added_at: str

    def to_dict(self, scope: str = "public") -> dict:
        return {
            "team_id": self.team_id,
            "user_id": self.user_id,
            "added_at": self.added_at,
        }

    @classmethod
    def from_row(cls, row) -> "TeamMember":
        return cls(
            team_id=row_get(row, "team_id", ""),
            user_id=row_get(row, "user_id", ""),
            added_at=row_get(row, "added_at", ""),
        )


@dataclass
class OrgInvitation(BaseModel):
    id: str
    org_id: str
    email: str
    org_role: str
    token: str
    status: str
    invited_by: str
    expires_at: str
    created_at: str
    team_id: Optional[str] = None
    accepted_at: Optional[str] = None

    def to_dict(self, scope: str = "public") -> dict:
        d = {
            "id": self.id,
            "org_id": self.org_id,
            "email": self.email,
            "org_role": self.org_role,
            "status": self.status,
            "expires_at": self.expires_at,
            "created_at": self.created_at,
        }
        if scope == "admin":
            d["token"] = self.token
            d["invited_by"] = self.invited_by
            d["team_id"] = self.team_id
            d["accepted_at"] = self.accepted_at
        return {k: v for k, v in d.items() if v is not None}

    @classmethod
    def from_row(cls, row) -> "OrgInvitation":
        return cls(
            id=row_get(row, "id"),
            org_id=row_get(row, "org_id", ""),
            email=row_get(row, "email", ""),
            org_role=row_get(row, "org_role", "member"),
            token=row_get(row, "token", ""),
            status=row_get(row, "status", "pending"),
            invited_by=row_get(row, "invited_by", ""),
            expires_at=row_get(row, "expires_at", ""),
            created_at=row_get(row, "created_at", ""),
            team_id=row_get(row, "team_id"),
            accepted_at=row_get(row, "accepted_at"),
        )
