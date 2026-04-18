import uuid
import json
from typing import Optional, List
from api.surveys.repository import SurveyRepository


class BadRequestError(Exception):
    pass


class NotFoundError(Exception):
    pass


class ForbiddenError(Exception):
    pass


class SurveyService:
    def __init__(self, repo: SurveyRepository, ctx):
        self._repo = repo
        self._ctx = ctx

    async def get_survey_with_questions(self, survey_id: str) -> dict:
        survey = await self._repo.get_survey(survey_id)
        if not survey:
            raise NotFoundError("Survey not found or inactive")

        questions = await self._repo.get_questions(survey_id)

        data = survey.to_dict()
        data["questions"] = [q.to_dict() for q in questions]
        return data

    async def get_user_surveys(self, author_id: str) -> List[dict]:
        surveys = await self._repo.get_surveys_by_author(author_id)
        return [s.to_dict() for s in surveys]

    async def create_survey(self, author_id: str, data: dict) -> dict:
        survey_id = str(uuid.uuid4())
        title = data.get("title")
        if not title:
            raise BadRequestError("Title is required")

        description = data.get("description")
        questions = data.get("questions", [])

        await self._repo.create_survey(
            survey_id, title, description, author_id, None, 1
        )

        for idx, q in enumerate(questions):
            q_id = str(uuid.uuid4())
            q_text = q.get("question_text")
            q_type = q.get("question_type", "MULTIPLE_CHOICE")
            options = json.dumps(q.get("options", []))
            is_req = 1 if q.get("is_required") else 0
            await self._repo.create_question(
                q_id, survey_id, q_text, q_type, options, is_req, idx
            )

        return {"id": survey_id, "title": title}

    async def submit_response(
        self,
        survey_id: str,
        data: dict,
        user_id: Optional[str],
        session_id: Optional[str],
    ):
        survey = await self._repo.get_survey(survey_id)
        if not survey:
            raise NotFoundError("Survey not found")

        questions = await self._repo.get_questions(survey_id)
        q_map = {q.id: q for q in questions}

        answers = data.get("answers", [])
        if not answers:
            raise BadRequestError("No answers provided")

        for ans in answers:
            q_id = ans.get("question_id")
            if q_id not in q_map:
                raise BadRequestError(f"Question {q_id} does not belong to survey")

            # Check if already answered
            if user_id:
                if await self._repo.has_user_responded(q_id, user_id):
                    continue  # optionally skip or raise error
            elif session_id:
                if await self._repo.has_session_responded(q_id, session_id):
                    continue

            q = q_map[q_id]
            txt = ans.get("answer_text")
            opt_idx = ans.get("answer_option_index")

            if q.question_type == "MULTIPLE_CHOICE" and opt_idx is None:
                raise BadRequestError(
                    f"Multiple choice question {q_id} requires an option index"
                )

            r_id = str(uuid.uuid4())
            await self._repo.save_response(
                r_id, survey_id, q_id, user_id, session_id, txt, opt_idx
            )

        return {"success": True}
