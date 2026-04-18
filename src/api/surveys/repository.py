from typing import Optional, List
from db.repository import BaseRepository
from api.surveys import queries as Q
from models.survey.model import Survey, SurveyQuestion


class SurveyRepository(BaseRepository):
    async def create_survey(
        self,
        survey_id: str,
        title: str,
        description: Optional[str],
        author_id: str,
        article_id: Optional[str],
        is_active: int,
    ) -> None:
        await self.execute(
            Q.INSERT_SURVEY,
            survey_id,
            title,
            description,
            author_id,
            article_id,
            is_active,
        )

    async def create_question(
        self,
        q_id: str,
        survey_id: str,
        text: str,
        q_type: str,
        options: str,
        is_req: int,
        sort: int,
    ) -> None:
        await self.execute(
            Q.INSERT_QUESTION, q_id, survey_id, text, q_type, options, is_req, sort
        )

    async def get_survey(self, survey_id: str) -> Optional[Survey]:
        row = await self.find_one(Q.GET_SURVEY, survey_id)
        return self.map_one(row, Survey)

    async def get_questions(self, survey_id: str) -> List[SurveyQuestion]:
        rows = await self.find_all(Q.GET_QUESTIONS_FOR_SURVEY, survey_id)
        return self.map_many(rows, SurveyQuestion)

    async def get_surveys_by_author(self, author_id: str) -> List[Survey]:
        rows = await self.find_all(Q.GET_SURVEYS_BY_AUTHOR, author_id)
        return self.map_many(rows, Survey)

    async def has_user_responded(self, question_id: str, user_id: str) -> bool:
        row = await self.find_one(Q.CHECK_IF_USER_RESPONDED, question_id, user_id)
        from models.base import row_get

        return row_get(row, "c", 0) > 0

    async def has_session_responded(self, question_id: str, session_id: str) -> bool:
        row = await self.find_one(Q.CHECK_IF_SESSION_RESPONDED, question_id, session_id)
        from models.base import row_get

        return row_get(row, "c", 0) > 0

    async def save_response(
        self,
        r_id: str,
        survey_id: str,
        q_id: str,
        user_id: Optional[str],
        session_id: Optional[str],
        txt: Optional[str],
        opt_idx: Optional[int],
    ) -> None:
        await self.execute(
            Q.INSERT_RESPONSE, r_id, survey_id, q_id, user_id, session_id, txt, opt_idx
        )
