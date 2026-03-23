from dataclasses import dataclass
from models.base import BaseModel, row_get


@dataclass
class Tag(BaseModel):
    id: str
    name: str
    slug: str
    tag_type: str = "topic"
    article_count: int = 0

    def to_dict(self, scope: str = "default") -> dict:
        data = {
            "id": self.id,
            "name": self.name,
            "slug": self.slug,
            "article_count": self.article_count,
        }
        if self.tag_type and self.tag_type != "topic":
            data["tag_type"] = self.tag_type
        return data

    @classmethod
    def from_row(cls, row) -> "Tag":
        return cls(
            id=row_get(row, "id"),
            name=row_get(row, "name"),
            slug=row_get(row, "slug"),
            tag_type=row_get(row, "tag_type", "topic"),
            article_count=row_get(row, "article_count", 0),
        )
