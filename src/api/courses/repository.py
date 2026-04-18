"""Phase 8 Step 31 — Course repository."""

import json
from db.repository import BaseRepository
from api.courses import queries as Q
from models.course.model import (
    Course,
    CourseModule,
    CourseLesson,
    LessonQuiz,
    QuizQuestion,
    CourseEnrollment,
    LessonProgress,
    Certificate,
)


class CourseRepository(BaseRepository):
    def _one(self, cls, row):
        return self.map_one(row, cls)

    def _many(self, rows, cls):
        return self.map_many(rows, cls)

    # ── Courses ──────────────────────────────────────────────
    async def list_courses(self, limit, offset):
        return self._many(await self.find_all(Q.LIST_COURSES, limit, offset), Course)

    async def list_courses_by_instructor(self, instructor_id, limit, offset):
        return self._many(
            await self.find_all(
                Q.LIST_COURSES_BY_INSTRUCTOR, instructor_id, limit, offset
            ),
            Course,
        )

    async def get_course(self, cid):
        return self._one(Course, await self.find_one(Q.GET_COURSE, cid))

    async def get_course_by_slug(self, slug):
        return self._one(Course, await self.find_one(Q.GET_COURSE_BY_SLUG, slug))

    async def create_course(
        self,
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
        tags,
        price_cents,
        membership_tier,
        status,
    ):
        await self.execute(
            Q.INSERT_COURSE,
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
            json.dumps(tags),
            price_cents,
            membership_tier,
            status,
        )

    async def update_course(
        self,
        cid,
        title,
        description,
        cover_image_url,
        intro_video_url,
        level,
        language,
        tags,
        price_cents,
        membership_tier,
        status,
    ):
        await self.execute(
            Q.UPDATE_COURSE,
            title,
            description,
            cover_image_url,
            intro_video_url,
            level,
            language,
            json.dumps(tags),
            price_cents,
            membership_tier,
            status,
            cid,
        )

    async def delete_course(self, cid):
        await self.execute(Q.DELETE_COURSE, cid)

    async def increment_enrollment(self, cid):
        await self.execute(Q.INCREMENT_ENROLLMENT, cid)

    async def decrement_enrollment(self, cid):
        await self.execute(Q.DECREMENT_ENROLLMENT, cid)

    async def publish_course(self, cid):
        await self.execute(Q.PUBLISH_COURSE, cid)

    # ── Course Modules ───────────────────────────────────────
    async def list_modules(self, course_id):
        return self._many(await self.find_all(Q.LIST_MODULES, course_id), CourseModule)

    async def get_module(self, mid):
        return self._one(CourseModule, await self.find_one(Q.GET_MODULE, mid))

    async def create_module(
        self, mid, course_id, title, description, sort_order, is_free
    ):
        await self.execute(
            Q.INSERT_MODULE,
            mid,
            course_id,
            title,
            description,
            sort_order,
            int(is_free),
        )

    async def update_module(self, mid, title, description, sort_order, is_free):
        await self.execute(
            Q.UPDATE_MODULE, title, description, sort_order, int(is_free), mid
        )

    async def delete_module(self, mid):
        await self.execute(Q.DELETE_MODULE, mid)

    # ── Course Lessons ───────────────────────────────────────
    async def list_lessons(self, module_id):
        return self._many(await self.find_all(Q.LIST_LESSONS, module_id), CourseLesson)

    async def list_lessons_by_course(self, course_id):
        return self._many(
            await self.find_all(Q.LIST_LESSONS_BY_COURSE, course_id), CourseLesson
        )

    async def get_lesson(self, lid):
        return self._one(CourseLesson, await self.find_one(Q.GET_LESSON, lid))

    async def create_lesson(
        self,
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
    ):
        await self.execute(
            Q.INSERT_LESSON,
            lid,
            module_id,
            course_id,
            title,
            sort_order,
            lesson_type,
            article_id,
            video_url,
            duration_minutes,
            int(is_free),
        )

    async def update_lesson(
        self,
        lid,
        title,
        sort_order,
        lesson_type,
        article_id,
        video_url,
        duration_minutes,
        is_free,
    ):
        await self.execute(
            Q.UPDATE_LESSON,
            title,
            sort_order,
            lesson_type,
            article_id,
            video_url,
            duration_minutes,
            int(is_free),
            lid,
        )

    async def delete_lesson(self, lid):
        await self.execute(Q.DELETE_LESSON, lid)

    # ── Lesson Quizzes ───────────────────────────────────────
    async def get_quiz(self, qid):
        return self._one(LessonQuiz, await self.find_one(Q.GET_QUIZ, qid))

    async def get_quiz_by_lesson(self, lesson_id):
        return self._one(
            LessonQuiz, await self.find_one(Q.GET_QUIZ_BY_LESSON, lesson_id)
        )

    async def create_quiz(self, qid, lesson_id, pass_score):
        await self.execute(Q.INSERT_QUIZ, qid, lesson_id, pass_score)

    async def update_quiz(self, qid, pass_score):
        await self.execute(Q.UPDATE_QUIZ, pass_score, qid)

    async def delete_quiz(self, qid):
        await self.execute(Q.DELETE_QUIZ, qid)

    # ── Quiz Questions ───────────────────────────────────────
    async def list_questions(self, quiz_id):
        return self._many(await self.find_all(Q.LIST_QUESTIONS, quiz_id), QuizQuestion)

    async def get_question(self, qid):
        return self._one(QuizQuestion, await self.find_one(Q.GET_QUESTION, qid))

    async def create_question(
        self, qid, quiz_id, question_text, question_type, options, sort_order
    ):
        await self.execute(
            Q.INSERT_QUESTION,
            qid,
            quiz_id,
            question_text,
            question_type,
            json.dumps(options),
            sort_order,
        )

    async def update_question(
        self, qid, question_text, question_type, options, sort_order
    ):
        await self.execute(
            Q.UPDATE_QUESTION,
            question_text,
            question_type,
            json.dumps(options),
            sort_order,
            qid,
        )

    async def delete_question(self, qid):
        await self.execute(Q.DELETE_QUESTION, qid)

    # ── Course Enrollments ───────────────────────────────────
    async def list_enrollments(self, course_id, limit, offset):
        return self._many(
            await self.find_all(Q.LIST_ENROLLMENTS, course_id, limit, offset),
            CourseEnrollment,
        )

    async def list_enrollments_by_user(self, user_id, limit, offset):
        return self._many(
            await self.find_all(Q.LIST_ENROLLMENTS_BY_USER, user_id, limit, offset),
            CourseEnrollment,
        )

    async def get_enrollment(self, eid):
        return self._one(CourseEnrollment, await self.find_one(Q.GET_ENROLLMENT, eid))

    async def get_enrollment_by_user(self, course_id, user_id):
        return self._one(
            CourseEnrollment,
            await self.find_one(Q.GET_ENROLLMENT_BY_USER, course_id, user_id),
        )

    async def create_enrollment(
        self, eid, course_id, user_id, status, paid_cents, payment_id
    ):
        await self.execute(
            Q.INSERT_ENROLLMENT, eid, course_id, user_id, status, paid_cents, payment_id
        )

    async def update_enrollment_status(self, eid, status):
        await self.execute(Q.UPDATE_ENROLLMENT_STATUS, status, eid)

    async def complete_enrollment(self, eid):
        await self.execute(Q.COMPLETE_ENROLLMENT, eid)

    async def delete_enrollment(self, eid):
        await self.execute(Q.DELETE_ENROLLMENT, eid)

    # ── Lesson Progress ──────────────────────────────────────
    async def list_progress(self, enrollment_id):
        return self._many(
            await self.find_all(Q.LIST_PROGRESS, enrollment_id), LessonProgress
        )

    async def get_progress(self, enrollment_id, lesson_id):
        return self._one(
            LessonProgress,
            await self.find_one(Q.GET_PROGRESS, enrollment_id, lesson_id),
        )

    async def upsert_progress(
        self, enrollment_id, lesson_id, status, progress_pct, quiz_score
    ):
        await self.execute(
            Q.UPSERT_PROGRESS,
            enrollment_id,
            lesson_id,
            status,
            progress_pct,
            quiz_score,
        )

    async def complete_progress(self, enrollment_id, lesson_id):
        await self.execute(Q.COMPLETE_PROGRESS, enrollment_id, lesson_id)

    # ── Certificates ─────────────────────────────────────────
    async def list_certificates_by_user(self, user_id):
        return self._many(
            await self.find_all(Q.LIST_CERTIFICATES_BY_USER, user_id), Certificate
        )

    async def list_certificates_by_course(self, course_id):
        return self._many(
            await self.find_all(Q.LIST_CERTIFICATES_BY_COURSE, course_id), Certificate
        )

    async def get_certificate(self, cid):
        return self._one(Certificate, await self.find_one(Q.GET_CERTIFICATE, cid))

    async def get_certificate_by_user_course(self, course_id, user_id):
        return self._one(
            Certificate,
            await self.find_one(Q.GET_CERTIFICATE_BY_USER_COURSE, course_id, user_id),
        )

    async def create_certificate(
        self, cid, course_id, user_id, enrollment_id, certificate_url
    ):
        await self.execute(
            Q.INSERT_CERTIFICATE,
            cid,
            course_id,
            user_id,
            enrollment_id,
            certificate_url,
        )

    async def delete_certificate(self, cid):
        await self.execute(Q.DELETE_CERTIFICATE, cid)
