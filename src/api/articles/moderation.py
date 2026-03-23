from dataclasses import dataclass
from typing import Optional


_FORBIDDEN_TERMS = {
    "credit card dump",
    "stolen credentials",
    "buy followers",
    "fake review service",
}


@dataclass
class ModerationResult:
    decision: str
    state: str
    note: Optional[str] = None


class ArticleModerationEngine:
    """Rule-based moderation pass used before human approval.

    The goal is to auto-screen low quality or policy-breaking drafts while still
    requiring APPROVER/SUPERADMIN for final approval.
    """

    @staticmethod
    def _extract_text(content: str) -> str:
        return (content or "").strip().lower()

    def check(self, title: str, content: str) -> ModerationResult:
        safe_title = (title or "").strip()
        safe_content = self._extract_text(content)

        if len(safe_title) > 120:
            return ModerationResult(
                decision="rejected",
                state="AUTO_REJECTED",
                note="Title exceeds 120 characters.",
            )

        if len(safe_content.split()) < 80:
            return ModerationResult(
                decision="rejected",
                state="AUTO_REJECTED",
                note="Article is too short for review. Minimum 80 words required.",
            )

        for term in _FORBIDDEN_TERMS:
            if term in safe_content:
                return ModerationResult(
                    decision="rejected",
                    state="AUTO_REJECTED",
                    note="Content contains prohibited terms and requires rewrite.",
                )

        return ModerationResult(
            decision="pending_admin",
            state="AUTO_APPROVED_PENDING_ADMIN",
            note="Auto-check passed. Pending admin/superadmin approval.",
        )
