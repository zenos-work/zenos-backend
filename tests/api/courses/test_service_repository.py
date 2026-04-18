import types

import pytest

from api.courses import service as courses_service_module
from api.courses.repository import CourseRepository
from api.courses.service import CourseService


class _Env:
    DB = object()


class Obj(types.SimpleNamespace):
    def to_dict(self, scope=None):
        data = dict(self.__dict__)
        if scope is not None:
            data["scope"] = scope
        return data


class RepoDyn:
    def __init__(self):
        self.responses = {}

    def __getattr__(self, name):
        async def _method(*_args, **_kwargs):
            value = self.responses.get(name)
            return value

        return _method


@pytest.fixture
def course_service(monkeypatch):
    svc = CourseService(_Env())
    repo = RepoDyn()
    svc._repo = repo
    seq = iter([f"id-{i}" for i in range(1, 40)])
    monkeypatch.setattr(courses_service_module, "new_id", lambda: next(seq))
    return svc, repo


@pytest.mark.asyncio
async def test_course_service_happy_paths(course_service):
    svc, repo = course_service

    repo.responses["list_courses"] = [Obj(id="c1")]
    repo.responses["list_courses_by_instructor"] = [Obj(id="c2")]
    assert (await svc.list_courses())["courses"][0]["id"] == "c1"
    assert (await svc.list_courses_by_instructor("i1"))["courses"][0]["id"] == "c2"

    repo.responses["get_course"] = Obj(
        id="c1",
        title="T",
        description="D",
        cover_image_url="",
        intro_video_url="",
        level="beginner",
        language="en",
        tags=[],
        price_cents=0,
        membership_tier="",
        status="draft",
    )
    assert (await svc.get_course("c1"))["id"] == "c1"
    assert (await svc.create_course(title="new"))["id"] == "id-1"
    assert (await svc.update_course("c1", title="U"))["id"] == "c1"
    assert (await svc.publish_course("c1"))["id"] == "c1"
    await svc.delete_course("c1")

    repo.responses["list_modules"] = [Obj(id="m1")]
    repo.responses["get_module"] = Obj(
        id="m1", title="M", description="", sort_order=1, is_free=False
    )
    assert (await svc.list_modules("c1"))[0]["id"] == "m1"
    assert (await svc.get_module("m1"))["id"] == "m1"
    assert (await svc.create_module("c1", title="M"))["id"] == "id-2"
    assert (await svc.update_module("m1", title="M2"))["id"] == "m1"
    await svc.delete_module("m1")

    repo.responses["list_lessons"] = [Obj(id="l1")]
    repo.responses["list_lessons_by_course"] = [Obj(id="l2")]
    repo.responses["get_lesson"] = Obj(
        id="l1",
        title="L",
        sort_order=1,
        lesson_type="article",
        article_id="a1",
        video_url="",
        duration_minutes=10,
        is_free=False,
    )
    assert (await svc.list_lessons("m1"))[0]["id"] == "l1"
    assert (await svc.list_lessons_by_course("c1"))[0]["id"] == "l2"
    assert (await svc.get_lesson("l1"))["id"] == "l1"
    assert (await svc.create_lesson("m1", "c1", title="L"))["id"] == "id-3"
    assert (await svc.update_lesson("l1", title="L2"))["id"] == "l1"
    await svc.delete_lesson("l1")

    repo.responses["get_quiz"] = Obj(id="q1", pass_score=70)
    repo.responses["get_quiz_by_lesson"] = Obj(id="q2")
    assert (await svc.get_quiz("q1"))["id"] == "q1"
    assert (await svc.get_quiz_by_lesson("l1"))["id"] == "q2"
    assert (await svc.create_quiz("l1"))["id"] == "id-4"
    assert (await svc.update_quiz("q1", 80))["id"] == "q1"
    await svc.delete_quiz("q1")

    repo.responses["list_questions"] = [Obj(id="qq1")]
    repo.responses["get_question"] = Obj(
        id="qq1", question_text="Q", question_type="mcq", options=[], sort_order=1
    )
    assert (await svc.list_questions("q1"))[0]["id"] == "qq1"
    assert (await svc.get_question("qq1"))["id"] == "qq1"
    assert (await svc.create_question("q1", "Q"))["id"] == "id-5"
    assert (await svc.update_question("qq1", question_text="Q2"))["id"] == "qq1"
    await svc.delete_question("qq1")

    repo.responses["list_enrollments"] = [Obj(id="e1")]
    repo.responses["list_enrollments_by_user"] = [Obj(id="e2")]
    repo.responses["get_enrollment"] = Obj(id="e1", course_id="c1")
    repo.responses["get_enrollment_by_user"] = None
    assert (await svc.list_enrollments("c1"))["enrollments"][0]["id"] == "e1"
    assert (await svc.list_enrollments_by_user("u1"))["enrollments"][0]["id"] == "e2"
    assert (await svc.get_enrollment("e1"))["id"] == "e1"
    assert (await svc.enroll("c1", "u1"))["id"] == "id-6"
    assert (await svc.update_enrollment_status("e1", "completed"))["id"] == "e1"
    assert (await svc.complete_enrollment("e1"))["id"] == "e1"
    assert (await svc.drop_enrollment("e1"))["id"] == "e1"

    repo.responses["list_progress"] = [Obj(id="p1")]
    repo.responses["get_progress"] = Obj(id="p1")
    assert (await svc.list_progress("e1"))[0]["id"] == "p1"
    assert (await svc.get_progress("e1", "l1"))["id"] == "p1"
    assert (await svc.upsert_progress("e1", "l1"))["lesson_id"] == "l1"
    assert (await svc.complete_lesson("e1", "l1"))["lesson_id"] == "l1"

    repo.responses["list_certificates_by_user"] = [Obj(id="cert1")]
    repo.responses["list_certificates_by_course"] = [Obj(id="cert2")]
    repo.responses["get_certificate"] = Obj(id="cert1")
    repo.responses["get_certificate_by_user_course"] = None
    assert (await svc.list_certificates_by_user("u1"))[0]["id"] == "cert1"
    assert (await svc.list_certificates_by_course("c1"))[0]["id"] == "cert2"
    assert (await svc.get_certificate("cert1"))["id"] == "cert1"
    assert (await svc.issue_certificate("c1", "u1", "e1"))["id"] == "id-7"


@pytest.mark.asyncio
async def test_course_service_not_found_and_duplicate(course_service):
    svc, repo = course_service

    repo.responses["get_course"] = None
    with pytest.raises(ValueError, match="Course not found"):
        await svc.get_course("missing")
    with pytest.raises(ValueError, match="Course not found"):
        await svc.update_course("missing")

    repo.responses["get_module"] = None
    with pytest.raises(ValueError, match="Module not found"):
        await svc.get_module("missing")

    repo.responses["get_lesson"] = None
    with pytest.raises(ValueError, match="Lesson not found"):
        await svc.get_lesson("missing")

    repo.responses["get_quiz"] = None
    with pytest.raises(ValueError, match="Quiz not found"):
        await svc.get_quiz("missing")

    repo.responses["get_question"] = None
    with pytest.raises(ValueError, match="Question not found"):
        await svc.get_question("missing")

    repo.responses["get_enrollment"] = None
    with pytest.raises(ValueError, match="Enrollment not found"):
        await svc.get_enrollment("missing")

    repo.responses["get_progress"] = None
    with pytest.raises(ValueError, match="Progress not found"):
        await svc.get_progress("e", "l")

    repo.responses["get_certificate"] = None
    with pytest.raises(ValueError, match="Certificate not found"):
        await svc.get_certificate("missing")

    repo.responses["get_enrollment_by_user"] = Obj(id="existing")
    with pytest.raises(ValueError, match="Already enrolled"):
        await svc.enroll("c1", "u1")

    repo.responses["get_certificate_by_user_course"] = Obj(id="existing")
    with pytest.raises(ValueError, match="Certificate already issued"):
        await svc.issue_certificate("c1", "u1", "e1")


@pytest.mark.asyncio
async def test_course_repository_methods(monkeypatch):
    repo = CourseRepository(db=object())
    execute_calls = []
    find_all_calls = []
    find_one_calls = []

    async def _execute(sql, *params):
        execute_calls.append((sql, params))

    async def _find_all(sql, *params):
        find_all_calls.append((sql, params))
        return [{"id": "x"}, {"id": "y"}]

    async def _find_one(sql, *params):
        find_one_calls.append((sql, params))
        return {"id": "x"}

    monkeypatch.setattr(repo, "execute", _execute)
    monkeypatch.setattr(repo, "find_all", _find_all)
    monkeypatch.setattr(repo, "find_one", _find_one)
    monkeypatch.setattr(repo, "map_many", lambda rows, _model: rows)
    monkeypatch.setattr(repo, "map_one", lambda row, _model: row)

    await repo.list_courses(10, 0)
    await repo.list_courses_by_instructor("i1", 10, 0)
    await repo.get_course("c1")
    await repo.get_course_by_slug("slug")
    await repo.create_course(
        "c1", "o", "i", "t", "s", "d", "", "", "beginner", "en", [], 0, "", "draft"
    )
    await repo.update_course(
        "c1", "t", "d", "", "", "beginner", "en", [], 0, "", "draft"
    )
    await repo.delete_course("c1")
    await repo.increment_enrollment("c1")
    await repo.decrement_enrollment("c1")
    await repo.publish_course("c1")
    await repo.list_modules("c1")
    await repo.get_module("m1")
    await repo.create_module("m1", "c1", "t", "d", 1, True)
    await repo.update_module("m1", "t", "d", 1, False)
    await repo.delete_module("m1")
    await repo.list_lessons("m1")
    await repo.list_lessons_by_course("c1")
    await repo.get_lesson("l1")
    await repo.create_lesson("l1", "m1", "c1", "t", 1, "article", "", "", 1, True)
    await repo.update_lesson("l1", "t", 1, "article", "", "", 1, False)
    await repo.delete_lesson("l1")
    await repo.get_quiz("q1")
    await repo.get_quiz_by_lesson("l1")
    await repo.create_quiz("q1", "l1", 70)
    await repo.update_quiz("q1", 80)
    await repo.delete_quiz("q1")
    await repo.list_questions("q1")
    await repo.get_question("qq1")
    await repo.create_question("qq1", "q1", "Q", "mcq", [], 1)
    await repo.update_question("qq1", "Q", "mcq", [], 1)
    await repo.delete_question("qq1")
    await repo.list_enrollments("c1", 10, 0)
    await repo.list_enrollments_by_user("u1", 10, 0)
    await repo.get_enrollment("e1")
    await repo.get_enrollment_by_user("c1", "u1")
    await repo.create_enrollment("e1", "c1", "u1", "enrolled", 0, "")
    await repo.update_enrollment_status("e1", "done")
    await repo.complete_enrollment("e1")
    await repo.delete_enrollment("e1")
    await repo.list_progress("e1")
    await repo.get_progress("e1", "l1")
    await repo.upsert_progress("e1", "l1", "in_progress", 50, 70)
    await repo.complete_progress("e1", "l1")
    await repo.list_certificates_by_user("u1")
    await repo.list_certificates_by_course("c1")
    await repo.get_certificate("cert")
    await repo.get_certificate_by_user_course("c1", "u1")
    await repo.create_certificate("cert", "c1", "u1", "e1", "url")
    await repo.delete_certificate("cert")

    assert len(execute_calls) == 26
    assert len(find_all_calls) == 11
    assert len(find_one_calls) == 12
