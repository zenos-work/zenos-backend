from dataclasses import dataclass
from typing import Optional
import json
from models.base import BaseModel, row_get


@dataclass
class Survey(BaseModel):
    id: str
    title: str
    description: Optional[str]
    author_id: str
    article_id: Optional[str]
    is_active: bool
    created_at: str
    updated_at: str

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "author_id": self.author_id,
            "article_id": self.article_id,
            "is_active": self.is_active,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_row(cls, row) -> "Survey":
        if row is None:
            return None
        return cls(
            id=row_get(row, "id"),
            title=row_get(row, "title"),
            description=row_get(row, "description"),
            author_id=row_get(row, "author_id"),
            article_id=row_get(row, "article_id"),
            is_active=bool(row_get(row, "is_active", 1)),
            created_at=row_get(row, "created_at"),
            updated_at=row_get(row, "updated_at"),
        )


@dataclass
class SurveyQuestion(BaseModel):
    id: str
    survey_id: str
    question_text: str
    question_type: str
    options: list
    is_required: bool
    sort_order: int
    created_at: str
    updated_at: str

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "survey_id": self.survey_id,
            "question_text": self.question_text,
            "question_type": self.question_type,
            "options": self.options,
            "is_required": self.is_required,
            "sort_order": self.sort_order,
        }

    @classmethod
    def from_row(cls, row) -> "SurveyQuestion":
        if row is None:
            return None
        raw_options = row_get(row, "options_json", "[]")
        options = (
            json.loads(raw_options) if isinstance(raw_options, str) else raw_options
        )
        return cls(
            id=row_get(row, "id"),
            survey_id=row_get(row, "survey_id"),
            question_text=row_get(row, "question_text"),
            question_type=row_get(row, "question_type"),
            options=options,
            is_required=bool(row_get(row, "is_required", 1)),
            sort_order=int(row_get(row, "sort_order", 0)),
            created_at=row_get(row, "created_at"),
            updated_at=row_get(row, "updated_at"),
        )
