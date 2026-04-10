"""Tests for Phase 8 — Courses & Learning Paths (model + handler)."""

import asyncio
import importlib
import json
import sys
import types
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

if "js" not in sys.modules:
    js_stub = types.ModuleType("js")

    class _Headers:
        @staticmethod
        def new(values=None, **_kwargs):
            return (
                dict(values)
                if isinstance(values, dict)
                else ({} if values is None else {k: v for k, v in values})
            )

    class _Resp:
        def __init__(self, body=None, status=200, headers=None):
            self.status_code = status
            self.headers = headers or {}
            self._body = body

        def json(self):
            if self._body is None or self._body == "":
                return None
            if isinstance(self._body, (dict, list)):
                return self._body
            return json.loads(self._body)

    class _Response:
        @staticmethod
        def new(body=None, status=200, headers=None):
            return _Resp(body=body, status=status, headers=headers)

    js_stub.Headers = _Headers
    js_stub.Response = _Response
    sys.modules["js"] = js_stub

# ── Model imports ───────────────────────────────────────────
course_models = importlib.import_module("models.course.model")
Course = course_models.Course
CourseModule = course_models.CourseModule
CourseLesson = course_models.CourseLesson
LessonQuiz = course_models.LessonQuiz
QuizQuestion = course_models.QuizQuestion
CourseEnrollment = course_models.CourseEnrollment
LessonProgress = course_models.LessonProgress
Certificate = course_models.Certificate

course_handler = importlib.import_module("api.courses.handler")
create_token = importlib.import_module("auth.jwt_handler").create_token

_JWT_SECRET = "test-secret"


# ═══════════════════════════════════════════════════════════════
# Course Model Tests
# ═══════════════════════════════════════════════════════════════
class TestCourseModels:
    def test_course_from_row(self):
        row = {
            "id": "c1",
            "org_id": "org1",
            "instructor_id": "u1",
            "title": "Python 101",
            "slug": "python-101",
            "description": "Intro",
            "cover_image_url": "",
            "intro_video_url": "",
            "level": "beginner",
            "language": "en",
            "tags": '["python","beginner"]',
            "price_cents": 4999,
            "membership_tier": "",
            "status": "published",
            "enrollment_count": 50,
            "rating_avg": 4.5,
            "rating_count": 20,
            "total_duration_minutes": 360,
            "published_at": "2026-01-01",
            "created_at": "2026-01-01",
            "updated_at": "2026-01-01",
        }
        c = Course.from_row(row)
        assert c.title == "Python 101"
        assert c.tags == ["python", "beginner"]
        assert c.price_cents == 4999
        assert c.enrollment_count == 50
        assert c.rating_avg == 4.5

    def test_course_from_row_none(self):
        assert Course.from_row(None) is None

    def test_course_to_dict(self):
        c = Course(id="c1", title="Test", slug="test")
        d = c.to_dict()
        assert d["id"] == "c1"
        assert d["title"] == "Test"

    def test_module_from_row(self):
        row = {
            "id": "m1",
            "course_id": "c1",
            "title": "Basics",
            "description": "The basics",
            "sort_order": 0,
            "is_free": 1,
            "created_at": "2026-01-01",
        }
        m = CourseModule.from_row(row)
        assert m.title == "Basics"
        assert m.is_free is True

    def test_module_from_row_none(self):
        assert CourseModule.from_row(None) is None

    def test_lesson_from_row(self):
        row = {
            "id": "l1",
            "module_id": "m1",
            "course_id": "c1",
            "title": "Variables",
            "sort_order": 0,
            "lesson_type": "article",
            "article_id": "a1",
            "video_url": "",
            "duration_minutes": 15,
            "is_free": 0,
            "created_at": "2026-01-01",
        }
        lesson = CourseLesson.from_row(row)
        assert lesson.title == "Variables"
        assert lesson.lesson_type == "article"
        assert lesson.is_free is False

    def test_lesson_from_row_none(self):
        assert CourseLesson.from_row(None) is None

    def test_quiz_from_row(self):
        row = {
            "id": "q1",
            "lesson_id": "l1",
            "pass_score": 80,
            "created_at": "2026-01-01",
        }
        q = LessonQuiz.from_row(row)
        assert q.pass_score == 80

    def test_quiz_from_row_none(self):
        assert LessonQuiz.from_row(None) is None

    def test_question_from_row(self):
        row = {
            "id": "qq1",
            "quiz_id": "q1",
            "question_text": "What is 2+2?",
            "question_type": "mcq",
            "options": '[{"label":"3","correct":false},{"label":"4","correct":true}]',
            "sort_order": 0,
        }
        q = QuizQuestion.from_row(row)
        assert q.question_text == "What is 2+2?"
        assert len(q.options) == 2
        assert q.options[1]["correct"] is True

    def test_question_from_row_none(self):
        assert QuizQuestion.from_row(None) is None

    def test_enrollment_from_row(self):
        row = {
            "id": "e1",
            "course_id": "c1",
            "user_id": "u1",
            "status": "enrolled",
            "enrolled_at": "2026-01-01",
            "completed_at": "",
            "paid_cents": 4999,
            "payment_id": "pay1",
        }
        e = CourseEnrollment.from_row(row)
        assert e.status == "enrolled"
        assert e.paid_cents == 4999

    def test_enrollment_from_row_none(self):
        assert CourseEnrollment.from_row(None) is None

    def test_progress_from_row(self):
        row = {
            "enrollment_id": "e1",
            "lesson_id": "l1",
            "status": "completed",
            "progress_pct": 100,
            "quiz_score": 90,
            "completed_at": "2026-01-01",
            "last_viewed_at": "2026-01-01",
        }
        p = LessonProgress.from_row(row)
        assert p.progress_pct == 100
        assert p.quiz_score == 90

    def test_progress_from_row_none(self):
        assert LessonProgress.from_row(None) is None

    def test_certificate_from_row(self):
        row = {
            "id": "cert1",
            "course_id": "c1",
            "user_id": "u1",
            "enrollment_id": "e1",
            "certificate_url": "https://cert.example.com/cert1",
            "issued_at": "2026-01-01",
        }
        cert = Certificate.from_row(row)
        assert cert.certificate_url == "https://cert.example.com/cert1"

    def test_certificate_from_row_none(self):
        assert Certificate.from_row(None) is None


# ═══════════════════════════════════════════════════════════════
# Fake Course Service
# ═══════════════════════════════════════════════════════════════
class FakeCourseService:
    def __init__(self, env, ctx=None):
        self.calls = []

    # Courses
    async def list_courses(self, page=1, limit=20):
        self.calls.append(("list_courses",))
        return {"courses": [{"id": "c1"}], "page": page, "limit": limit}

    async def list_courses_by_instructor(self, instructor_id, page=1, limit=20):
        self.calls.append(("list_courses_by_instructor", instructor_id))
        return {"courses": [{"id": "c1"}], "page": page, "limit": limit}

    async def get_course(self, cid):
        self.calls.append(("get_course", cid))
        if cid == "missing":
            raise ValueError("Not found")
        return {"id": cid}

    async def create_course(self, **kw):
        self.calls.append(("create_course",))
        return {"id": "new-course"}

    async def update_course(self, cid, **kw):
        self.calls.append(("update_course", cid))
        if cid == "missing":
            raise ValueError("Not found")
        return {"id": cid}

    async def publish_course(self, cid):
        self.calls.append(("publish_course", cid))
        if cid == "missing":
            raise ValueError("Not found")
        return {"id": cid}

    async def delete_course(self, cid):
        self.calls.append(("delete_course", cid))
        if cid == "missing":
            raise ValueError("Not found")

    # Modules
    async def list_modules(self, course_id):
        self.calls.append(("list_modules", course_id))
        return [{"id": "m1"}]

    async def get_module(self, mid):
        self.calls.append(("get_module", mid))
        if mid == "missing":
            raise ValueError("Not found")
        return {"id": mid}

    async def create_module(self, **kw):
        self.calls.append(("create_module",))
        return {"id": "new-mod"}

    async def update_module(self, mid, **kw):
        self.calls.append(("update_module", mid))
        if mid == "missing":
            raise ValueError("Not found")
        return {"id": mid}

    async def delete_module(self, mid):
        self.calls.append(("delete_module", mid))
        if mid == "missing":
            raise ValueError("Not found")

    # Lessons
    async def list_lessons(self, module_id):
        self.calls.append(("list_lessons", module_id))
        return [{"id": "l1"}]

    async def list_lessons_by_course(self, course_id):
        self.calls.append(("list_lessons_by_course", course_id))
        return [{"id": "l1"}]

    async def get_lesson(self, lid):
        self.calls.append(("get_lesson", lid))
        if lid == "missing":
            raise ValueError("Not found")
        return {"id": lid}

    async def create_lesson(self, **kw):
        self.calls.append(("create_lesson",))
        return {"id": "new-lesson"}

    async def update_lesson(self, lid, **kw):
        self.calls.append(("update_lesson", lid))
        if lid == "missing":
            raise ValueError("Not found")
        return {"id": lid}

    async def delete_lesson(self, lid):
        self.calls.append(("delete_lesson", lid))
        if lid == "missing":
            raise ValueError("Not found")

    # Quizzes
    async def get_quiz(self, qid):
        self.calls.append(("get_quiz", qid))
        if qid == "missing":
            raise ValueError("Not found")
        return {"id": qid}

    async def get_quiz_by_lesson(self, lesson_id):
        self.calls.append(("get_quiz_by_lesson", lesson_id))
        if lesson_id == "missing":
            raise ValueError("Not found")
        return {"id": "q1", "lesson_id": lesson_id}

    async def create_quiz(self, **kw):
        self.calls.append(("create_quiz",))
        return {"id": "new-quiz"}

    async def update_quiz(self, qid, pass_score=70):
        self.calls.append(("update_quiz", qid))
        if qid == "missing":
            raise ValueError("Not found")
        return {"id": qid}

    async def delete_quiz(self, qid):
        self.calls.append(("delete_quiz", qid))
        if qid == "missing":
            raise ValueError("Not found")

    # Questions
    async def list_questions(self, quiz_id):
        self.calls.append(("list_questions", quiz_id))
        return [{"id": "qq1"}]

    async def get_question(self, qid):
        self.calls.append(("get_question", qid))
        if qid == "missing":
            raise ValueError("Not found")
        return {"id": qid}

    async def create_question(self, **kw):
        self.calls.append(("create_question",))
        return {"id": "new-q"}

    async def update_question(self, qid, **kw):
        self.calls.append(("update_question", qid))
        if qid == "missing":
            raise ValueError("Not found")
        return {"id": qid}

    async def delete_question(self, qid):
        self.calls.append(("delete_question", qid))
        if qid == "missing":
            raise ValueError("Not found")

    # Enrollments
    async def list_enrollments(self, course_id, page=1, limit=20):
        self.calls.append(("list_enrollments", course_id))
        return {"enrollments": [{"id": "e1"}], "page": page, "limit": limit}

    async def list_enrollments_by_user(self, user_id, page=1, limit=20):
        self.calls.append(("list_enrollments_by_user", user_id))
        return {"enrollments": [{"id": "e1"}], "page": page, "limit": limit}

    async def get_enrollment(self, eid):
        self.calls.append(("get_enrollment", eid))
        if eid == "missing":
            raise ValueError("Not found")
        return {"id": eid}

    async def enroll(self, course_id, user_id, paid_cents=0, payment_id=""):
        self.calls.append(("enroll", course_id, user_id))
        return {"id": "new-enroll"}

    async def complete_enrollment(self, eid):
        self.calls.append(("complete_enrollment", eid))
        if eid == "missing":
            raise ValueError("Not found")
        return {"id": eid}

    async def drop_enrollment(self, eid):
        self.calls.append(("drop_enrollment", eid))
        if eid == "missing":
            raise ValueError("Not found")
        return {"id": eid}

    # Progress
    async def list_progress(self, enrollment_id):
        self.calls.append(("list_progress", enrollment_id))
        return [{"enrollment_id": enrollment_id, "lesson_id": "l1"}]

    async def get_progress(self, enrollment_id, lesson_id):
        self.calls.append(("get_progress", enrollment_id, lesson_id))
        if lesson_id == "missing":
            raise ValueError("Not found")
        return {"enrollment_id": enrollment_id, "lesson_id": lesson_id}

    async def upsert_progress(
        self,
        enrollment_id,
        lesson_id,
        status="in_progress",
        progress_pct=0,
        quiz_score=0,
    ):
        self.calls.append(("upsert_progress", enrollment_id, lesson_id))
        return {"enrollment_id": enrollment_id, "lesson_id": lesson_id}

    async def complete_lesson(self, enrollment_id, lesson_id):
        self.calls.append(("complete_lesson", enrollment_id, lesson_id))
        return {"enrollment_id": enrollment_id, "lesson_id": lesson_id}

    # Certificates
    async def list_certificates_by_course(self, course_id):
        self.calls.append(("list_certificates_by_course", course_id))
        return [{"id": "cert1"}]

    async def get_certificate(self, cid):
        self.calls.append(("get_certificate", cid))
        if cid == "missing":
            raise ValueError("Not found")
        return {"id": cid}

    async def issue_certificate(
        self, course_id, user_id, enrollment_id, certificate_url=""
    ):
        self.calls.append(("issue_certificate", course_id, user_id))
        return {"id": "new-cert"}


# ═══════════════════════════════════════════════════════════════
# Test Helpers
# ═══════════════════════════════════════════════════════════════
class FakeRequest:
    def __init__(self, method, url, headers=None, json_body=None):
        self.method = method
        self.url = f"https://testserver{url}"
        self.headers = headers or {}
        self._json = json_body

    async def json(self):
        return self._json or {}


class FakeCtx:
    trace_id = "test-trace"


def _token(sub="u1", role="AUTHOR"):
    return create_token({"sub": sub, "role": role}, _JWT_SECRET)


class CourseClient:
    def __init__(self, svc_instance):
        self.svc = svc_instance

    def _dispatch(self, method, path, headers=None, json_body=None):
        parsed = urlparse(path)
        req = FakeRequest(
            method=method, url=path, headers=headers or {}, json_body=json_body
        )

        class _Env:
            JWT_SECRET = _JWT_SECRET

        orig = course_handler.CourseService
        course_handler.CourseService = lambda env, ctx=None: self.svc
        try:
            return asyncio.run(
                course_handler.handle_courses(
                    req,
                    _Env(),
                    parsed.path,
                    method,
                    parse_qs(parsed.query),
                    FakeCtx(),
                )
            )
        finally:
            course_handler.CourseService = orig

    def get(self, path, headers=None):
        return self._dispatch("GET", path, headers=headers)

    def post(self, path, headers=None, json_body=None):
        return self._dispatch("POST", path, headers=headers, json_body=json_body)

    def put(self, path, headers=None, json_body=None):
        return self._dispatch("PUT", path, headers=headers, json_body=json_body)

    def delete(self, path, headers=None, json_body=None):
        return self._dispatch("DELETE", path, headers=headers, json_body=json_body)


@pytest.fixture
def course_svc():
    return FakeCourseService(type("E", (), {})())


@pytest.fixture
def client(course_svc):
    return CourseClient(course_svc)


# ═══════════════════════════════════════════════════════════════
# Course Handler Tests
# ═══════════════════════════════════════════════════════════════
class TestCourseHandler:
    def _h(self):
        return {"Authorization": f"Bearer {_token()}"}

    def test_unauth_returns_401(self, client):
        resp = client.get("/api/courses")
        assert resp.status_code == 401

    # Course CRUD
    def test_list_courses(self, client):
        resp = client.get("/api/courses", headers=self._h())
        assert resp.status_code == 200
        assert "courses" in resp.json()

    def test_list_courses_by_instructor(self, client):
        resp = client.get("/api/courses?instructor_id=u1", headers=self._h())
        assert resp.status_code == 200

    def test_create_course(self, client):
        resp = client.post(
            "/api/courses",
            headers=self._h(),
            json_body={"title": "Python 101", "slug": "python-101"},
        )
        assert resp.status_code == 201
        assert resp.json()["id"] == "new-course"

    def test_get_course(self, client):
        resp = client.get("/api/courses/c1", headers=self._h())
        assert resp.status_code == 200

    def test_get_course_missing(self, client):
        resp = client.get("/api/courses/missing", headers=self._h())
        assert resp.status_code == 404

    def test_update_course(self, client):
        resp = client.put(
            "/api/courses/c1", headers=self._h(), json_body={"title": "Updated"}
        )
        assert resp.status_code == 200

    def test_delete_course(self, client):
        resp = client.delete("/api/courses/c1", headers=self._h())
        assert resp.status_code == 200
        assert resp.json()["deleted"] is True

    def test_delete_course_missing(self, client):
        resp = client.delete("/api/courses/missing", headers=self._h())
        assert resp.status_code == 404

    # Publish
    def test_publish_course(self, client):
        resp = client.post("/api/courses/c1/publish", headers=self._h())
        assert resp.status_code == 200


class TestModuleHandler:
    def _h(self):
        return {"Authorization": f"Bearer {_token()}"}

    def test_list_modules(self, client):
        resp = client.get("/api/courses/c1/modules", headers=self._h())
        assert resp.status_code == 200
        assert "modules" in resp.json()

    def test_create_module(self, client):
        resp = client.post(
            "/api/courses/c1/modules", headers=self._h(), json_body={"title": "Basics"}
        )
        assert resp.status_code == 201

    def test_get_module(self, client):
        resp = client.get("/api/courses/c1/modules/m1", headers=self._h())
        assert resp.status_code == 200

    def test_get_module_missing(self, client):
        resp = client.get("/api/courses/c1/modules/missing", headers=self._h())
        assert resp.status_code == 404

    def test_update_module(self, client):
        resp = client.put(
            "/api/courses/c1/modules/m1",
            headers=self._h(),
            json_body={"title": "Updated"},
        )
        assert resp.status_code == 200

    def test_delete_module(self, client):
        resp = client.delete("/api/courses/c1/modules/m1", headers=self._h())
        assert resp.status_code == 200


class TestLessonHandler:
    def _h(self):
        return {"Authorization": f"Bearer {_token()}"}

    def test_list_lessons(self, client):
        resp = client.get("/api/courses/c1/modules/m1/lessons", headers=self._h())
        assert resp.status_code == 200
        assert "lessons" in resp.json()

    def test_create_lesson(self, client):
        resp = client.post(
            "/api/courses/c1/modules/m1/lessons",
            headers=self._h(),
            json_body={"title": "Variables", "lesson_type": "article"},
        )
        assert resp.status_code == 201

    def test_get_lesson(self, client):
        resp = client.get("/api/courses/c1/modules/m1/lessons/l1", headers=self._h())
        assert resp.status_code == 200

    def test_get_lesson_missing(self, client):
        resp = client.get(
            "/api/courses/c1/modules/m1/lessons/missing", headers=self._h()
        )
        assert resp.status_code == 404

    def test_update_lesson(self, client):
        resp = client.put(
            "/api/courses/c1/modules/m1/lessons/l1",
            headers=self._h(),
            json_body={"title": "Updated"},
        )
        assert resp.status_code == 200

    def test_delete_lesson(self, client):
        resp = client.delete("/api/courses/c1/modules/m1/lessons/l1", headers=self._h())
        assert resp.status_code == 200


class TestQuizHandler:
    def _h(self):
        return {"Authorization": f"Bearer {_token()}"}

    def test_get_quiz(self, client):
        resp = client.get(
            "/api/courses/c1/modules/m1/lessons/l1/quiz", headers=self._h()
        )
        assert resp.status_code == 200

    def test_create_quiz(self, client):
        resp = client.post(
            "/api/courses/c1/modules/m1/lessons/l1/quiz",
            headers=self._h(),
            json_body={"pass_score": 80},
        )
        assert resp.status_code == 201

    def test_update_quiz(self, client):
        resp = client.put(
            "/api/courses/c1/modules/m1/lessons/l1/quiz",
            headers=self._h(),
            json_body={"pass_score": 90},
        )
        assert resp.status_code == 200

    def test_delete_quiz(self, client):
        resp = client.delete(
            "/api/courses/c1/modules/m1/lessons/l1/quiz", headers=self._h()
        )
        assert resp.status_code == 200

    # Questions
    def test_list_questions(self, client):
        resp = client.get(
            "/api/courses/c1/modules/m1/lessons/l1/quiz/questions", headers=self._h()
        )
        assert resp.status_code == 200

    def test_create_question(self, client):
        resp = client.post(
            "/api/courses/c1/modules/m1/lessons/l1/quiz/questions",
            headers=self._h(),
            json_body={"question_text": "What is 2+2?", "question_type": "mcq"},
        )
        assert resp.status_code == 201

    def test_get_question(self, client):
        resp = client.get(
            "/api/courses/c1/modules/m1/lessons/l1/quiz/questions/qq1",
            headers=self._h(),
        )
        assert resp.status_code == 200

    def test_update_question(self, client):
        resp = client.put(
            "/api/courses/c1/modules/m1/lessons/l1/quiz/questions/qq1",
            headers=self._h(),
            json_body={"question_text": "Updated"},
        )
        assert resp.status_code == 200

    def test_delete_question(self, client):
        resp = client.delete(
            "/api/courses/c1/modules/m1/lessons/l1/quiz/questions/qq1",
            headers=self._h(),
        )
        assert resp.status_code == 200


class TestEnrollmentHandler:
    def _h(self):
        return {"Authorization": f"Bearer {_token()}"}

    def test_list_enrollments(self, client):
        resp = client.get("/api/courses/c1/enrollments", headers=self._h())
        assert resp.status_code == 200
        assert "enrollments" in resp.json()

    def test_enroll(self, client):
        resp = client.post(
            "/api/courses/c1/enrollments",
            headers=self._h(),
            json_body={"paid_cents": 4999},
        )
        assert resp.status_code == 201
        assert resp.json()["id"] == "new-enroll"

    def test_get_enrollment(self, client):
        resp = client.get("/api/courses/c1/enrollments/e1", headers=self._h())
        assert resp.status_code == 200

    def test_get_enrollment_missing(self, client):
        resp = client.get("/api/courses/c1/enrollments/missing", headers=self._h())
        assert resp.status_code == 404

    def test_complete_enrollment(self, client):
        resp = client.post("/api/courses/c1/enrollments/e1/complete", headers=self._h())
        assert resp.status_code == 200

    def test_drop_enrollment(self, client):
        resp = client.post("/api/courses/c1/enrollments/e1/drop", headers=self._h())
        assert resp.status_code == 200

    # Progress
    def test_list_progress(self, client):
        resp = client.get("/api/courses/c1/enrollments/e1/progress", headers=self._h())
        assert resp.status_code == 200

    def test_upsert_progress(self, client):
        resp = client.post(
            "/api/courses/c1/enrollments/e1/progress",
            headers=self._h(),
            json_body={"lesson_id": "l1", "status": "in_progress", "progress_pct": 50},
        )
        assert resp.status_code == 201

    def test_get_progress(self, client):
        resp = client.get(
            "/api/courses/c1/enrollments/e1/progress/l1", headers=self._h()
        )
        assert resp.status_code == 200

    def test_complete_lesson(self, client):
        resp = client.post(
            "/api/courses/c1/enrollments/e1/progress/l1/complete", headers=self._h()
        )
        assert resp.status_code == 200


class TestCertificateHandler:
    def _h(self):
        return {"Authorization": f"Bearer {_token()}"}

    def test_list_certificates(self, client):
        resp = client.get("/api/courses/c1/certificates", headers=self._h())
        assert resp.status_code == 200
        assert "certificates" in resp.json()

    def test_issue_certificate(self, client):
        resp = client.post(
            "/api/courses/c1/certificates",
            headers=self._h(),
            json_body={"enrollment_id": "e1"},
        )
        assert resp.status_code == 201
        assert resp.json()["id"] == "new-cert"

    def test_get_certificate(self, client):
        resp = client.get("/api/courses/c1/certificates/cert1", headers=self._h())
        assert resp.status_code == 200

    def test_get_certificate_missing(self, client):
        resp = client.get("/api/courses/c1/certificates/missing", headers=self._h())
        assert resp.status_code == 404
