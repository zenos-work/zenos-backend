"""Phase 8 Step 31 — Course service."""

from api.courses.repository import CourseRepository
from utils.helpers import new_id, paginate


class CourseService:
    def __init__(self, env, ctx=None):
        self._repo = CourseRepository(env.DB, ctx)

    # ── Courses ──────────────────────────────────────────────
    async def list_courses(self, page=1, limit=20):
        lim, off = paginate(page, limit)
        items = await self._repo.list_courses(lim, off)
        return {"courses": [c.to_dict() for c in items], "page": page, "limit": lim}

    async def list_courses_by_instructor(self, instructor_id, page=1, limit=20):
        lim, off = paginate(page, limit)
        items = await self._repo.list_courses_by_instructor(instructor_id, lim, off)
        return {"courses": [c.to_dict() for c in items], "page": page, "limit": lim}

    async def get_course(self, cid):
        c = await self._repo.get_course(cid)
        if not c:
            raise ValueError("Course not found")
        return c.to_dict()

    async def create_course(
        self,
        org_id="",
        instructor_id="",
        title="",
        slug="",
        description="",
        cover_image_url="",
        intro_video_url="",
        level="beginner",
        language="en",
        tags=None,
        price_cents=0,
        membership_tier="",
        status="draft",
    ):
        cid = new_id()
        await self._repo.create_course(
            cid,
            org_id,
            instructor_id,
            title,
            slug,
            description,
            cover_image_url,
            intro_video_url,
            level,
            language,
            tags or [],
            price_cents,
            membership_tier,
            status,
        )
        return {"id": cid}

    async def update_course(self, cid, **kwargs):
        existing = await self._repo.get_course(cid)
        if not existing:
            raise ValueError("Course not found")
        await self._repo.update_course(
            cid,
            title=kwargs.get("title") or existing.title,
            description=kwargs.get("description")
            if kwargs.get("description") is not None
            else existing.description,
            cover_image_url=kwargs.get("cover_image_url")
            if kwargs.get("cover_image_url") is not None
            else existing.cover_image_url,
            intro_video_url=kwargs.get("intro_video_url")
            if kwargs.get("intro_video_url") is not None
            else existing.intro_video_url,
            level=kwargs.get("level") or existing.level,
            language=kwargs.get("language") or existing.language,
            tags=kwargs.get("tags")
            if kwargs.get("tags") is not None
            else existing.tags,
            price_cents=kwargs.get("price_cents")
            if kwargs.get("price_cents") is not None
            else existing.price_cents,
            membership_tier=kwargs.get("membership_tier")
            if kwargs.get("membership_tier") is not None
            else existing.membership_tier,
            status=kwargs.get("status") or existing.status,
        )
        return {"id": cid}

    async def publish_course(self, cid):
        existing = await self._repo.get_course(cid)
        if not existing:
            raise ValueError("Course not found")
        await self._repo.publish_course(cid)
        return {"id": cid}

    async def delete_course(self, cid):
        existing = await self._repo.get_course(cid)
        if not existing:
            raise ValueError("Course not found")
        await self._repo.delete_course(cid)

    # ── Course Modules ───────────────────────────────────────
    async def list_modules(self, course_id):
        items = await self._repo.list_modules(course_id)
        return [m.to_dict() for m in items]

    async def get_module(self, mid):
        m = await self._repo.get_module(mid)
        if not m:
            raise ValueError("Module not found")
        return m.to_dict()

    async def create_module(
        self, course_id, title="", description="", sort_order=0, is_free=False
    ):
        mid = new_id()
        await self._repo.create_module(
            mid, course_id, title, description, sort_order, is_free
        )
        return {"id": mid}

    async def update_module(self, mid, **kwargs):
        existing = await self._repo.get_module(mid)
        if not existing:
            raise ValueError("Module not found")
        await self._repo.update_module(
            mid,
            title=kwargs.get("title") or existing.title,
            description=kwargs.get("description")
            if kwargs.get("description") is not None
            else existing.description,
            sort_order=kwargs.get("sort_order")
            if kwargs.get("sort_order") is not None
            else existing.sort_order,
            is_free=kwargs.get("is_free")
            if kwargs.get("is_free") is not None
            else existing.is_free,
        )
        return {"id": mid}

    async def delete_module(self, mid):
        existing = await self._repo.get_module(mid)
        if not existing:
            raise ValueError("Module not found")
        await self._repo.delete_module(mid)

    # ── Course Lessons ───────────────────────────────────────
    async def list_lessons(self, module_id):
        items = await self._repo.list_lessons(module_id)
        return [lesson.to_dict() for lesson in items]

    async def list_lessons_by_course(self, course_id):
        items = await self._repo.list_lessons_by_course(course_id)
        return [lesson.to_dict() for lesson in items]

    async def get_lesson(self, lid):
        lesson = await self._repo.get_lesson(lid)
        if not lesson:
            raise ValueError("Lesson not found")
        return lesson.to_dict()

    async def create_lesson(
        self,
        module_id,
        course_id,
        title="",
        sort_order=0,
        lesson_type="article",
        article_id="",
        video_url="",
        duration_minutes=0,
        is_free=False,
    ):
        lid = new_id()
        await self._repo.create_lesson(
            lid,
            module_id,
            course_id,
            title,
            sort_order,
            lesson_type,
            article_id,
            video_url,
            duration_minutes,
            is_free,
        )
        return {"id": lid}

    async def update_lesson(self, lid, **kwargs):
        existing = await self._repo.get_lesson(lid)
        if not existing:
            raise ValueError("Lesson not found")
        await self._repo.update_lesson(
            lid,
            title=kwargs.get("title") or existing.title,
            sort_order=kwargs.get("sort_order")
            if kwargs.get("sort_order") is not None
            else existing.sort_order,
            lesson_type=kwargs.get("lesson_type") or existing.lesson_type,
            article_id=kwargs.get("article_id")
            if kwargs.get("article_id") is not None
            else existing.article_id,
            video_url=kwargs.get("video_url")
            if kwargs.get("video_url") is not None
            else existing.video_url,
            duration_minutes=kwargs.get("duration_minutes")
            if kwargs.get("duration_minutes") is not None
            else existing.duration_minutes,
            is_free=kwargs.get("is_free")
            if kwargs.get("is_free") is not None
            else existing.is_free,
        )
        return {"id": lid}

    async def delete_lesson(self, lid):
        existing = await self._repo.get_lesson(lid)
        if not existing:
            raise ValueError("Lesson not found")
        await self._repo.delete_lesson(lid)

    # ── Lesson Quizzes ───────────────────────────────────────
    async def get_quiz(self, qid):
        q = await self._repo.get_quiz(qid)
        if not q:
            raise ValueError("Quiz not found")
        return q.to_dict()

    async def get_quiz_by_lesson(self, lesson_id):
        q = await self._repo.get_quiz_by_lesson(lesson_id)
        if not q:
            raise ValueError("Quiz not found")
        return q.to_dict()

    async def create_quiz(self, lesson_id, pass_score=70):
        qid = new_id()
        await self._repo.create_quiz(qid, lesson_id, pass_score)
        return {"id": qid}

    async def update_quiz(self, qid, pass_score=70):
        existing = await self._repo.get_quiz(qid)
        if not existing:
            raise ValueError("Quiz not found")
        await self._repo.update_quiz(qid, pass_score)
        return {"id": qid}

    async def delete_quiz(self, qid):
        existing = await self._repo.get_quiz(qid)
        if not existing:
            raise ValueError("Quiz not found")
        await self._repo.delete_quiz(qid)

    # ── Quiz Questions ───────────────────────────────────────
    async def list_questions(self, quiz_id):
        items = await self._repo.list_questions(quiz_id)
        return [q.to_dict() for q in items]

    async def get_question(self, qid):
        q = await self._repo.get_question(qid)
        if not q:
            raise ValueError("Question not found")
        return q.to_dict()

    async def create_question(
        self, quiz_id, question_text="", question_type="mcq", options=None, sort_order=0
    ):
        qid = new_id()
        await self._repo.create_question(
            qid, quiz_id, question_text, question_type, options or [], sort_order
        )
        return {"id": qid}

    async def update_question(self, qid, **kwargs):
        existing = await self._repo.get_question(qid)
        if not existing:
            raise ValueError("Question not found")
        await self._repo.update_question(
            qid,
            question_text=kwargs.get("question_text") or existing.question_text,
            question_type=kwargs.get("question_type") or existing.question_type,
            options=kwargs.get("options")
            if kwargs.get("options") is not None
            else existing.options,
            sort_order=kwargs.get("sort_order")
            if kwargs.get("sort_order") is not None
            else existing.sort_order,
        )
        return {"id": qid}

    async def delete_question(self, qid):
        existing = await self._repo.get_question(qid)
        if not existing:
            raise ValueError("Question not found")
        await self._repo.delete_question(qid)

    # ── Course Enrollments ───────────────────────────────────
    async def list_enrollments(self, course_id, page=1, limit=20):
        lim, off = paginate(page, limit)
        items = await self._repo.list_enrollments(course_id, lim, off)
        return {"enrollments": [e.to_dict() for e in items], "page": page, "limit": lim}

    async def list_enrollments_by_user(self, user_id, page=1, limit=20):
        lim, off = paginate(page, limit)
        items = await self._repo.list_enrollments_by_user(user_id, lim, off)
        return {"enrollments": [e.to_dict() for e in items], "page": page, "limit": lim}

    async def get_enrollment(self, eid):
        e = await self._repo.get_enrollment(eid)
        if not e:
            raise ValueError("Enrollment not found")
        return e.to_dict()

    async def enroll(self, course_id, user_id, paid_cents=0, payment_id=""):
        existing = await self._repo.get_enrollment_by_user(course_id, user_id)
        if existing:
            raise ValueError("Already enrolled")
        eid = new_id()
        await self._repo.create_enrollment(
            eid, course_id, user_id, "enrolled", paid_cents, payment_id
        )
        await self._repo.increment_enrollment(course_id)
        return {"id": eid}

    async def update_enrollment_status(self, eid, status):
        existing = await self._repo.get_enrollment(eid)
        if not existing:
            raise ValueError("Enrollment not found")
        await self._repo.update_enrollment_status(eid, status)
        return {"id": eid}

    async def complete_enrollment(self, eid):
        existing = await self._repo.get_enrollment(eid)
        if not existing:
            raise ValueError("Enrollment not found")
        await self._repo.complete_enrollment(eid)
        return {"id": eid}

    async def drop_enrollment(self, eid):
        existing = await self._repo.get_enrollment(eid)
        if not existing:
            raise ValueError("Enrollment not found")
        await self._repo.update_enrollment_status(eid, "dropped")
        await self._repo.decrement_enrollment(existing.course_id)
        return {"id": eid}

    # ── Lesson Progress ──────────────────────────────────────
    async def list_progress(self, enrollment_id):
        items = await self._repo.list_progress(enrollment_id)
        return [p.to_dict() for p in items]

    async def get_progress(self, enrollment_id, lesson_id):
        p = await self._repo.get_progress(enrollment_id, lesson_id)
        if not p:
            raise ValueError("Progress not found")
        return p.to_dict()

    async def upsert_progress(
        self,
        enrollment_id,
        lesson_id,
        status="in_progress",
        progress_pct=0,
        quiz_score=0,
    ):
        await self._repo.upsert_progress(
            enrollment_id, lesson_id, status, progress_pct, quiz_score
        )
        return {"enrollment_id": enrollment_id, "lesson_id": lesson_id}

    async def complete_lesson(self, enrollment_id, lesson_id):
        await self._repo.complete_progress(enrollment_id, lesson_id)
        return {"enrollment_id": enrollment_id, "lesson_id": lesson_id}

    # ── Certificates ─────────────────────────────────────────
    async def list_certificates_by_user(self, user_id):
        items = await self._repo.list_certificates_by_user(user_id)
        return [c.to_dict() for c in items]

    async def list_certificates_by_course(self, course_id):
        items = await self._repo.list_certificates_by_course(course_id)
        return [c.to_dict() for c in items]

    async def get_certificate(self, cid):
        c = await self._repo.get_certificate(cid)
        if not c:
            raise ValueError("Certificate not found")
        return c.to_dict()

    async def issue_certificate(
        self, course_id, user_id, enrollment_id, certificate_url=""
    ):
        existing = await self._repo.get_certificate_by_user_course(course_id, user_id)
        if existing:
            raise ValueError("Certificate already issued")
        cid = new_id()
        await self._repo.create_certificate(
            cid, course_id, user_id, enrollment_id, certificate_url
        )
        return {"id": cid}
