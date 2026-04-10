"""Phase 8 Step 31 — Course handler."""

from utils.helpers import json_resp, error
from middleware.auth import get_user
from api.courses.service import CourseService


async def handle_courses(request, env, path, method, query, ctx):
    svc = CourseService(env, ctx)
    parts = path.rstrip("/").split("/")

    user = await get_user(request, env)
    if not user:
        return error("Unauthorised", 401)
    uid = user["sub"]

    # ── Modules sub-resource ─────────────────────────────────
    # /api/courses/:cid/modules[/:mid]
    if len(parts) >= 5 and parts[4] == "modules":
        course_id = parts[3]

        # Lessons sub-sub-resource: /api/courses/:cid/modules/:mid/lessons[/:lid]
        if len(parts) >= 7 and parts[6] == "lessons":
            module_id = parts[5]
            # Quiz sub-sub-sub: /api/courses/:cid/modules/:mid/lessons/:lid/quiz
            if len(parts) >= 9 and parts[8] == "quiz":
                lesson_id = parts[7]
                # Questions: /api/courses/:cid/modules/:mid/lessons/:lid/quiz/questions[/:qid]
                if len(parts) >= 10 and parts[9] == "questions":
                    if method == "GET" and len(parts) == 10:
                        quiz = await svc.get_quiz_by_lesson(lesson_id)
                        return json_resp(
                            {"questions": await svc.list_questions(quiz["id"])}
                        )
                    if method == "POST" and len(parts) == 10:
                        body = await request.json()
                        data = body if isinstance(body, dict) else {}
                        quiz = await svc.get_quiz_by_lesson(lesson_id)
                        try:
                            result = await svc.create_question(
                                quiz_id=quiz["id"],
                                question_text=data.get("question_text", ""),
                                question_type=data.get("question_type", "mcq"),
                                options=data.get("options"),
                                sort_order=data.get("sort_order", 0),
                            )
                            return json_resp(result, 201)
                        except ValueError as e:
                            return error(str(e), 400)
                    if method == "GET" and len(parts) == 11:
                        try:
                            return json_resp(await svc.get_question(parts[10]))
                        except ValueError as e:
                            return error(str(e), 404)
                    if method == "PUT" and len(parts) == 11:
                        body = await request.json()
                        data = body if isinstance(body, dict) else {}
                        try:
                            return json_resp(
                                await svc.update_question(parts[10], **data)
                            )
                        except ValueError as e:
                            return error(str(e), 400)
                    if method == "DELETE" and len(parts) == 11:
                        try:
                            await svc.delete_question(parts[10])
                            return json_resp({"deleted": True})
                        except ValueError as e:
                            return error(str(e), 404)
                    return error("Not found", 404)

                # GET /api/courses/:cid/modules/:mid/lessons/:lid/quiz
                if method == "GET" and len(parts) == 9:
                    try:
                        return json_resp(await svc.get_quiz_by_lesson(lesson_id))
                    except ValueError as e:
                        return error(str(e), 404)
                # POST /api/courses/:cid/modules/:mid/lessons/:lid/quiz
                if method == "POST" and len(parts) == 9:
                    body = await request.json()
                    data = body if isinstance(body, dict) else {}
                    try:
                        result = await svc.create_quiz(
                            lesson_id=lesson_id,
                            pass_score=data.get("pass_score", 70),
                        )
                        return json_resp(result, 201)
                    except ValueError as e:
                        return error(str(e), 400)
                # PUT /api/courses/:cid/modules/:mid/lessons/:lid/quiz
                if method == "PUT" and len(parts) == 9:
                    body = await request.json()
                    data = body if isinstance(body, dict) else {}
                    try:
                        quiz = await svc.get_quiz_by_lesson(lesson_id)
                        return json_resp(
                            await svc.update_quiz(
                                quiz["id"], data.get("pass_score", 70)
                            )
                        )
                    except ValueError as e:
                        return error(str(e), 400)
                # DELETE /api/courses/:cid/modules/:mid/lessons/:lid/quiz
                if method == "DELETE" and len(parts) == 9:
                    try:
                        quiz = await svc.get_quiz_by_lesson(lesson_id)
                        await svc.delete_quiz(quiz["id"])
                        return json_resp({"deleted": True})
                    except ValueError as e:
                        return error(str(e), 404)
                return error("Not found", 404)

            # GET /api/courses/:cid/modules/:mid/lessons
            if method == "GET" and len(parts) == 7:
                return json_resp({"lessons": await svc.list_lessons(module_id)})
            # POST /api/courses/:cid/modules/:mid/lessons
            if method == "POST" and len(parts) == 7:
                body = await request.json()
                data = body if isinstance(body, dict) else {}
                try:
                    result = await svc.create_lesson(
                        module_id=module_id,
                        course_id=course_id,
                        title=data.get("title", ""),
                        sort_order=data.get("sort_order", 0),
                        lesson_type=data.get("lesson_type", "article"),
                        article_id=data.get("article_id", ""),
                        video_url=data.get("video_url", ""),
                        duration_minutes=data.get("duration_minutes", 0),
                        is_free=data.get("is_free", False),
                    )
                    return json_resp(result, 201)
                except ValueError as e:
                    return error(str(e), 400)
            # GET /api/courses/:cid/modules/:mid/lessons/:lid
            if method == "GET" and len(parts) == 8:
                try:
                    return json_resp(await svc.get_lesson(parts[7]))
                except ValueError as e:
                    return error(str(e), 404)
            # PUT /api/courses/:cid/modules/:mid/lessons/:lid
            if method == "PUT" and len(parts) == 8:
                body = await request.json()
                data = body if isinstance(body, dict) else {}
                try:
                    return json_resp(await svc.update_lesson(parts[7], **data))
                except ValueError as e:
                    return error(str(e), 400)
            # DELETE /api/courses/:cid/modules/:mid/lessons/:lid
            if method == "DELETE" and len(parts) == 8:
                try:
                    await svc.delete_lesson(parts[7])
                    return json_resp({"deleted": True})
                except ValueError as e:
                    return error(str(e), 404)
            return error("Not found", 404)

        # GET /api/courses/:cid/modules
        if method == "GET" and len(parts) == 5:
            return json_resp({"modules": await svc.list_modules(course_id)})
        # POST /api/courses/:cid/modules
        if method == "POST" and len(parts) == 5:
            body = await request.json()
            data = body if isinstance(body, dict) else {}
            try:
                result = await svc.create_module(
                    course_id=course_id,
                    title=data.get("title", ""),
                    description=data.get("description", ""),
                    sort_order=data.get("sort_order", 0),
                    is_free=data.get("is_free", False),
                )
                return json_resp(result, 201)
            except ValueError as e:
                return error(str(e), 400)
        # GET /api/courses/:cid/modules/:mid
        if method == "GET" and len(parts) == 6:
            try:
                return json_resp(await svc.get_module(parts[5]))
            except ValueError as e:
                return error(str(e), 404)
        # PUT /api/courses/:cid/modules/:mid
        if method == "PUT" and len(parts) == 6:
            body = await request.json()
            data = body if isinstance(body, dict) else {}
            try:
                return json_resp(await svc.update_module(parts[5], **data))
            except ValueError as e:
                return error(str(e), 400)
        # DELETE /api/courses/:cid/modules/:mid
        if method == "DELETE" and len(parts) == 6:
            try:
                await svc.delete_module(parts[5])
                return json_resp({"deleted": True})
            except ValueError as e:
                return error(str(e), 404)
        return error("Not found", 404)

    # ── Enrollments sub-resource ─────────────────────────────
    # /api/courses/:cid/enrollments[/:eid]
    if len(parts) >= 5 and parts[4] == "enrollments":
        course_id = parts[3]

        # Progress sub: /api/courses/:cid/enrollments/:eid/progress[/:lid]
        if len(parts) >= 7 and parts[6] == "progress":
            enrollment_id = parts[5]
            # GET /api/courses/:cid/enrollments/:eid/progress
            if method == "GET" and len(parts) == 7:
                return json_resp({"progress": await svc.list_progress(enrollment_id)})
            # POST /api/courses/:cid/enrollments/:eid/progress
            if method == "POST" and len(parts) == 7:
                body = await request.json()
                data = body if isinstance(body, dict) else {}
                try:
                    result = await svc.upsert_progress(
                        enrollment_id=enrollment_id,
                        lesson_id=data.get("lesson_id", ""),
                        status=data.get("status", "in_progress"),
                        progress_pct=data.get("progress_pct", 0),
                        quiz_score=data.get("quiz_score", 0),
                    )
                    return json_resp(result, 201)
                except ValueError as e:
                    return error(str(e), 400)
            # GET /api/courses/:cid/enrollments/:eid/progress/:lid
            if method == "GET" and len(parts) == 8:
                try:
                    return json_resp(await svc.get_progress(enrollment_id, parts[7]))
                except ValueError as e:
                    return error(str(e), 404)
            # POST /api/courses/:cid/enrollments/:eid/progress/:lid/complete
            if len(parts) == 9 and parts[8] == "complete" and method == "POST":
                try:
                    return json_resp(await svc.complete_lesson(enrollment_id, parts[7]))
                except ValueError as e:
                    return error(str(e), 400)
            return error("Not found", 404)

        # Complete enrollment: POST /api/courses/:cid/enrollments/:eid/complete
        if len(parts) == 7 and parts[6] == "complete" and method == "POST":
            try:
                return json_resp(await svc.complete_enrollment(parts[5]))
            except ValueError as e:
                return error(str(e), 400)

        # Drop enrollment: POST /api/courses/:cid/enrollments/:eid/drop
        if len(parts) == 7 and parts[6] == "drop" and method == "POST":
            try:
                return json_resp(await svc.drop_enrollment(parts[5]))
            except ValueError as e:
                return error(str(e), 400)

        # GET /api/courses/:cid/enrollments
        if method == "GET" and len(parts) == 5:
            page = int(query.get("page", ["1"])[0])
            limit = int(query.get("limit", ["20"])[0])
            return json_resp(await svc.list_enrollments(course_id, page, limit))
        # POST /api/courses/:cid/enrollments
        if method == "POST" and len(parts) == 5:
            body = await request.json()
            data = body if isinstance(body, dict) else {}
            try:
                result = await svc.enroll(
                    course_id=course_id,
                    user_id=uid,
                    paid_cents=data.get("paid_cents", 0),
                    payment_id=data.get("payment_id", ""),
                )
                return json_resp(result, 201)
            except ValueError as e:
                return error(str(e), 400)
        # GET /api/courses/:cid/enrollments/:eid
        if method == "GET" and len(parts) == 6:
            try:
                return json_resp(await svc.get_enrollment(parts[5]))
            except ValueError as e:
                return error(str(e), 404)
        return error("Not found", 404)

    # ── Certificates sub-resource ────────────────────────────
    # /api/courses/:cid/certificates[/:cert_id]
    if len(parts) >= 5 and parts[4] == "certificates":
        course_id = parts[3]
        # GET /api/courses/:cid/certificates
        if method == "GET" and len(parts) == 5:
            return json_resp(
                {"certificates": await svc.list_certificates_by_course(course_id)}
            )
        # POST /api/courses/:cid/certificates
        if method == "POST" and len(parts) == 5:
            body = await request.json()
            data = body if isinstance(body, dict) else {}
            try:
                result = await svc.issue_certificate(
                    course_id=course_id,
                    user_id=uid,
                    enrollment_id=data.get("enrollment_id", ""),
                    certificate_url=data.get("certificate_url", ""),
                )
                return json_resp(result, 201)
            except ValueError as e:
                return error(str(e), 400)
        # GET /api/courses/:cid/certificates/:cert_id
        if method == "GET" and len(parts) == 6:
            try:
                return json_resp(await svc.get_certificate(parts[5]))
            except ValueError as e:
                return error(str(e), 404)
        return error("Not found", 404)

    # ── Publish action ───────────────────────────────────────
    # POST /api/courses/:cid/publish
    if len(parts) == 5 and parts[4] == "publish" and method == "POST":
        try:
            return json_resp(await svc.publish_course(parts[3]))
        except ValueError as e:
            return error(str(e), 400)

    # ── Course CRUD ──────────────────────────────────────────
    # GET /api/courses
    if method == "GET" and len(parts) == 3:
        page = int(query.get("page", ["1"])[0])
        limit = int(query.get("limit", ["20"])[0])
        instructor_id = query.get("instructor_id", [None])[0]
        if instructor_id:
            return json_resp(
                await svc.list_courses_by_instructor(instructor_id, page, limit)
            )
        return json_resp(await svc.list_courses(page, limit))
    # POST /api/courses
    if method == "POST" and len(parts) == 3:
        body = await request.json()
        data = body if isinstance(body, dict) else {}
        try:
            result = await svc.create_course(
                org_id=data.get("org_id", ""),
                instructor_id=uid,
                title=data.get("title", ""),
                slug=data.get("slug", ""),
                description=data.get("description", ""),
                cover_image_url=data.get("cover_image_url", ""),
                intro_video_url=data.get("intro_video_url", ""),
                level=data.get("level", "beginner"),
                language=data.get("language", "en"),
                tags=data.get("tags"),
                price_cents=data.get("price_cents", 0),
                membership_tier=data.get("membership_tier", ""),
                status=data.get("status", "draft"),
            )
            return json_resp(result, 201)
        except ValueError as e:
            return error(str(e), 400)
    # GET /api/courses/:cid
    if method == "GET" and len(parts) == 4:
        try:
            return json_resp(await svc.get_course(parts[3]))
        except ValueError as e:
            return error(str(e), 404)
    # PUT /api/courses/:cid
    if method == "PUT" and len(parts) == 4:
        body = await request.json()
        data = body if isinstance(body, dict) else {}
        try:
            return json_resp(await svc.update_course(parts[3], **data))
        except ValueError as e:
            return error(str(e), 400)
    # DELETE /api/courses/:cid
    if method == "DELETE" and len(parts) == 4:
        try:
            await svc.delete_course(parts[3])
            return json_resp({"deleted": True})
        except ValueError as e:
            return error(str(e), 404)

    return error("Not found", 404)
