import importlib


mod = importlib.import_module("api.articles.moderation")


def _long_text(words=90):
    return " ".join(["fintech"] * words)


def test_extract_text_normalizes_none_and_case():
    engine = mod.ArticleModerationEngine()
    assert engine._extract_text(None) == ""
    assert engine._extract_text("  HELLO World  ") == "hello world"


def test_rejects_title_too_long():
    engine = mod.ArticleModerationEngine()
    result = engine.check("x" * 121, _long_text())
    assert result.decision == "rejected"
    assert result.state == "AUTO_REJECTED"


def test_rejects_short_content():
    engine = mod.ArticleModerationEngine()
    result = engine.check("Valid title", "too short")
    assert result.decision == "rejected"
    assert "Minimum 80 words" in result.note


def test_rejects_forbidden_term():
    engine = mod.ArticleModerationEngine()
    content = _long_text() + " stolen credentials " + _long_text(5)
    result = engine.check("Valid title", content)
    assert result.decision == "rejected"
    assert "prohibited terms" in result.note


def test_pending_admin_for_clean_content():
    engine = mod.ArticleModerationEngine()
    result = engine.check("Valid title", _long_text(120))
    assert result.decision == "pending_admin"
    assert result.state == "AUTO_APPROVED_PENDING_ADMIN"
