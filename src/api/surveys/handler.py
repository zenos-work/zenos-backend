from utils.helpers import json_resp, error
from middleware.auth import get_user
from api.surveys.service import SurveyService
from api.surveys.repository import SurveyRepository


async def handle_surveys(request, env, path, method, query, ctx):
    repo = SurveyRepository(env.DB, ctx)
    svc = SurveyService(repo, ctx)
    parts = path.rstrip("/").split("/")

    user = await get_user(request, env)
    uid = user["sub"] if user else None

    # GET /api/surveys - List author's surveys
    if method == "GET" and len(parts) == 3 and parts[2] == "surveys":
        if not uid:
            return error("Auth required", 401)
        return json_resp(await svc.get_user_surveys(uid))

    # POST /api/surveys - Create survey
    if method == "POST" and len(parts) == 3 and parts[2] == "surveys":
        if not uid:
            return error("Auth required", 401)
        body = await request.json()
        try:
            return json_resp(await svc.create_survey(uid, body), 201)
        except Exception as e:
            return error(str(e), 400)

    # ── Public / Reader Endpoints ──
    # GET /api/surveys/:id
    if method == "GET" and len(parts) == 4 and parts[2] == "surveys":
        survey_id = parts[3]
        try:
            return json_resp(await svc.get_survey_with_questions(survey_id))
        except Exception as e:
            return error(str(e), 404)

    # POST /api/surveys/:id/responses - Submit response
    if method == "POST" and len(parts) == 5 and parts[4] == "responses":
        survey_id = parts[3]
        body = await request.json()
        session_id = request.headers.get("X-Session-ID")
        try:
            result = await svc.submit_response(
                survey_id, body, user_id=uid, session_id=session_id
            )
            return json_resp(result, 201)
        except Exception as e:
            return error(str(e), 400)

    # ── Admin endpoints (Create / Edit surveys) ──
    # Note: A real app would have POST /api/admin/surveys

    return error("Not found", 404)
