import importlib

import pytest


req_mod = importlib.import_module("models.article.requests")
ArticleCreateRequest = req_mod.ArticleCreateRequest
ArticleUpdateRequest = req_mod.ArticleUpdateRequest
RejectArticleRequest = req_mod.RejectArticleRequest


def _valid_content(words=90):
    return " ".join(["content"] * words)


def _base_payload():
    return {
        "title": "A valid fintech title",
        "content": _valid_content(),
    }


def test_create_validates_content_type_and_reading_level():
    with pytest.raises(ValueError, match="content_type"):
        ArticleCreateRequest.from_body({**_base_payload(), "content_type": "Bad_Type"})

    with pytest.raises(ValueError, match="reading_level"):
        ArticleCreateRequest.from_body({**_base_payload(), "reading_level": "Expert"})


def test_create_validates_datetime_and_citations_and_premium_fields():
    with pytest.raises(ValueError, match="Invalid datetime format"):
        ArticleCreateRequest.from_body({**_base_payload(), "last_verified_at": "nope"})

    with pytest.raises(ValueError, match=r"http\(s\) URL"):
        ArticleCreateRequest.from_body({**_base_payload(), "citations": ["ftp://bad"]})

    with pytest.raises(ValueError, match="premium_only"):
        ArticleCreateRequest.from_body({**_base_payload(), "premium_only": 2})

    with pytest.raises(ValueError, match="premium_teaser_words"):
        ArticleCreateRequest.from_body(
            {**_base_payload(), "premium_teaser_words": 3001}
        )


def test_create_normalizes_optional_text_values():
    req = ArticleCreateRequest.from_body(
        {
            **_base_payload(),
            "subtitle": " undefined ",
            "canonical_url": " null ",
            "content_type": "article",
            "citations": ["https://example.com/a"],
        }
    )

    assert req.subtitle is None
    assert req.canonical_url is None
    assert req.citations == ["https://example.com/a"]


def test_update_validates_limits_and_schema_type():
    with pytest.raises(ValueError, match="seo_schema_type"):
        ArticleUpdateRequest.from_body({"seo_schema_type": "NewsArticle"})

    with pytest.raises(ValueError, match="Cannot have more than 10 tags"):
        ArticleUpdateRequest.from_body({"tag_ids": list(range(11))})

    with pytest.raises(ValueError, match="premium_only"):
        ArticleUpdateRequest.from_body({"premium_only": 9})

    with pytest.raises(ValueError, match="premium_teaser_words"):
        ArticleUpdateRequest.from_body({"premium_teaser_words": -1})


def test_reject_article_request_accepts_reason_alias_and_validates_length():
    req = RejectArticleRequest.from_body({"reason": "Needs more evidence and details."})
    assert "Needs more evidence" in req.note

    with pytest.raises(ValueError, match="at least 10 characters"):
        RejectArticleRequest.from_body({"note": "too short"})
