from dataclasses import dataclass
from models.base import BaseModel, row_get


@dataclass
class Tag(BaseModel):
    id: str
    name: str
    slug: str
    article_count: int = 0

    @classmethod
    def from_row(cls, row) -> "Tag":
        return cls(
            id=row_get(row, "id"),
            name=row_get(row, "name"),
            slug=row_get(row, "slug"),
            article_count=row_get(row, "article_count", 0),
        )
