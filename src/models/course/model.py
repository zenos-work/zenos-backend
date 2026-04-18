"""Phase 8 Step 31 — Course models."""

import json
from dataclasses import dataclass, field


def _json_field(row, key, default=None):
    v = row.get(key)
    if v is None:
        return default if default is not None else []
    if isinstance(v, (dict, list)):
        return v
    try:
        return json.loads(v)
    except (json.JSONDecodeError, TypeError):
        return default if default is not None else []


@dataclass
class Course:
    id: str = ""
    org_id: str = ""
    instructor_id: str = ""
    title: str = ""
    slug: str = ""
    description: str = ""
    cover_image_url: str = ""
    intro_video_url: str = ""
    level: str = "beginner"
    language: str = "en"
    tags: list = field(default_factory=list)
    price_cents: int = 0
    membership_tier: str = ""
    status: str = "draft"
    enrollment_count: int = 0
    rating_avg: float = 0.0
    rating_count: int = 0
    total_duration_minutes: int = 0
    published_at: str = ""
    created_at: str = ""
    updated_at: str = ""

    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        return cls(
            id=row.get("id", ""),
            org_id=row.get("org_id", "") or "",
            instructor_id=row.get("instructor_id", ""),
            title=row.get("title", ""),
            slug=row.get("slug", ""),
            description=row.get("description", "") or "",
            cover_image_url=row.get("cover_image_url", "") or "",
            intro_video_url=row.get("intro_video_url", "") or "",
            level=row.get("level", "beginner"),
            language=row.get("language", "en"),
            tags=_json_field(row, "tags", []),
            price_cents=row.get("price_cents", 0) or 0,
            membership_tier=row.get("membership_tier", "") or "",
            status=row.get("status", "draft"),
            enrollment_count=row.get("enrollment_count", 0) or 0,
            rating_avg=row.get("rating_avg", 0.0) or 0.0,
            rating_count=row.get("rating_count", 0) or 0,
            total_duration_minutes=row.get("total_duration_minutes", 0) or 0,
            published_at=row.get("published_at", "") or "",
            created_at=row.get("created_at", ""),
            updated_at=row.get("updated_at", ""),
        )

    def to_dict(self, scope="public"):
        d = {
            "id": self.id,
            "org_id": self.org_id,
            "instructor_id": self.instructor_id,
            "title": self.title,
            "slug": self.slug,
            "description": self.description,
            "cover_image_url": self.cover_image_url,
            "intro_video_url": self.intro_video_url,
            "level": self.level,
            "language": self.language,
            "tags": self.tags,
            "price_cents": self.price_cents,
            "membership_tier": self.membership_tier,
            "status": self.status,
            "enrollment_count": self.enrollment_count,
            "rating_avg": self.rating_avg,
            "rating_count": self.rating_count,
            "total_duration_minutes": self.total_duration_minutes,
            "published_at": self.published_at,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
        return d


@dataclass
class CourseModule:
    id: str = ""
    course_id: str = ""
    title: str = ""
    description: str = ""
    sort_order: int = 0
    is_free: bool = False
    created_at: str = ""

    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        return cls(
            id=row.get("id", ""),
            course_id=row.get("course_id", ""),
            title=row.get("title", ""),
            description=row.get("description", "") or "",
            sort_order=row.get("sort_order", 0) or 0,
            is_free=bool(row.get("is_free", 0)),
            created_at=row.get("created_at", ""),
        )

    def to_dict(self, scope="public"):
        return {
            "id": self.id,
            "course_id": self.course_id,
            "title": self.title,
            "description": self.description,
            "sort_order": self.sort_order,
            "is_free": self.is_free,
            "created_at": self.created_at,
        }


@dataclass
class CourseLesson:
    id: str = ""
    module_id: str = ""
    course_id: str = ""
    title: str = ""
    sort_order: int = 0
    lesson_type: str = "article"
    article_id: str = ""
    video_url: str = ""
    duration_minutes: int = 0
    is_free: bool = False
    created_at: str = ""

    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        return cls(
            id=row.get("id", ""),
            module_id=row.get("module_id", ""),
            course_id=row.get("course_id", ""),
            title=row.get("title", ""),
            sort_order=row.get("sort_order", 0) or 0,
            lesson_type=row.get("lesson_type", "article"),
            article_id=row.get("article_id", "") or "",
            video_url=row.get("video_url", "") or "",
            duration_minutes=row.get("duration_minutes", 0) or 0,
            is_free=bool(row.get("is_free", 0)),
            created_at=row.get("created_at", ""),
        )

    def to_dict(self, scope="public"):
        return {
            "id": self.id,
            "module_id": self.module_id,
            "course_id": self.course_id,
            "title": self.title,
            "sort_order": self.sort_order,
            "lesson_type": self.lesson_type,
            "article_id": self.article_id,
            "video_url": self.video_url,
            "duration_minutes": self.duration_minutes,
            "is_free": self.is_free,
            "created_at": self.created_at,
        }


@dataclass
class LessonQuiz:
    id: str = ""
    lesson_id: str = ""
    pass_score: int = 70
    created_at: str = ""

    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        return cls(
            id=row.get("id", ""),
            lesson_id=row.get("lesson_id", ""),
            pass_score=row.get("pass_score", 70) or 70,
            created_at=row.get("created_at", ""),
        )

    def to_dict(self, scope="public"):
        return {
            "id": self.id,
            "lesson_id": self.lesson_id,
            "pass_score": self.pass_score,
            "created_at": self.created_at,
        }


@dataclass
class QuizQuestion:
    id: str = ""
    quiz_id: str = ""
    question_text: str = ""
    question_type: str = "mcq"
    options: list = field(default_factory=list)
    sort_order: int = 0

    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        return cls(
            id=row.get("id", ""),
            quiz_id=row.get("quiz_id", ""),
            question_text=row.get("question_text", ""),
            question_type=row.get("question_type", "mcq"),
            options=_json_field(row, "options", []),
            sort_order=row.get("sort_order", 0) or 0,
        )

    def to_dict(self, scope="public"):
        return {
            "id": self.id,
            "quiz_id": self.quiz_id,
            "question_text": self.question_text,
            "question_type": self.question_type,
            "options": self.options,
            "sort_order": self.sort_order,
        }


@dataclass
class CourseEnrollment:
    id: str = ""
    course_id: str = ""
    user_id: str = ""
    status: str = "enrolled"
    enrolled_at: str = ""
    completed_at: str = ""
    paid_cents: int = 0
    payment_id: str = ""

    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        return cls(
            id=row.get("id", ""),
            course_id=row.get("course_id", ""),
            user_id=row.get("user_id", ""),
            status=row.get("status", "enrolled"),
            enrolled_at=row.get("enrolled_at", ""),
            completed_at=row.get("completed_at", "") or "",
            paid_cents=row.get("paid_cents", 0) or 0,
            payment_id=row.get("payment_id", "") or "",
        )

    def to_dict(self, scope="public"):
        return {
            "id": self.id,
            "course_id": self.course_id,
            "user_id": self.user_id,
            "status": self.status,
            "enrolled_at": self.enrolled_at,
            "completed_at": self.completed_at,
            "paid_cents": self.paid_cents,
            "payment_id": self.payment_id,
        }


@dataclass
class LessonProgress:
    enrollment_id: str = ""
    lesson_id: str = ""
    status: str = "not_started"
    progress_pct: int = 0
    quiz_score: int = 0
    completed_at: str = ""
    last_viewed_at: str = ""

    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        return cls(
            enrollment_id=row.get("enrollment_id", ""),
            lesson_id=row.get("lesson_id", ""),
            status=row.get("status", "not_started"),
            progress_pct=row.get("progress_pct", 0) or 0,
            quiz_score=row.get("quiz_score", 0) or 0,
            completed_at=row.get("completed_at", "") or "",
            last_viewed_at=row.get("last_viewed_at", "") or "",
        )

    def to_dict(self, scope="public"):
        return {
            "enrollment_id": self.enrollment_id,
            "lesson_id": self.lesson_id,
            "status": self.status,
            "progress_pct": self.progress_pct,
            "quiz_score": self.quiz_score,
            "completed_at": self.completed_at,
            "last_viewed_at": self.last_viewed_at,
        }


@dataclass
class Certificate:
    id: str = ""
    course_id: str = ""
    user_id: str = ""
    enrollment_id: str = ""
    certificate_url: str = ""
    issued_at: str = ""

    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        return cls(
            id=row.get("id", ""),
            course_id=row.get("course_id", ""),
            user_id=row.get("user_id", ""),
            enrollment_id=row.get("enrollment_id", ""),
            certificate_url=row.get("certificate_url", "") or "",
            issued_at=row.get("issued_at", ""),
        )

    def to_dict(self, scope="public"):
        return {
            "id": self.id,
            "course_id": self.course_id,
            "user_id": self.user_id,
            "enrollment_id": self.enrollment_id,
            "certificate_url": self.certificate_url,
            "issued_at": self.issued_at,
        }
