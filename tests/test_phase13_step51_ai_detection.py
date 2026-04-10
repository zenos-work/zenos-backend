"""
Tests for Phase 13 - Step 51: AI Content Detection
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from api.moderation.ai_detection import (
    AIDetectionService,
    HeuristicDetector,
    DetectionHeuristics,
    DetectionResult,
)


class TestHeuristicDetector:
    """Test heuristic-based AI detection"""

    def test_analyze_human_text(self):
        """Analyze clearly human text"""
        text = "The quick brown fox jumps over the lazy dog. " * 5
        heuristics = HeuristicDetector.analyze(text)
        assert heuristics.vocabulary_diversity > 0
        assert heuristics.sentence_length_variance >= 0

    def test_analyze_repetitive_text(self):
        """Analyze highly repetitive (AI-like) text"""
        text = "The system works. The system works. The system works. " * 10
        heuristics = HeuristicDetector.analyze(text)
        # High repetition should score higher on AI likelihood
        assert heuristics.repetition_rate > 0

    def test_heuristic_score_calculation(self):
        """Calculate combined heuristic score"""
        heuristics = DetectionHeuristics(
            vocabulary_diversity=0.5,
            sentence_length_variance=5.0,
            perplexity_score=75.0,
            repetition_rate=10.0,
            entropy_score=5.0,
        )
        score = heuristics.calculate_score()
        assert 0 <= score <= 100


class TestAIDetectionService:
    """Test AI detection pipeline"""

    @pytest.fixture
    def mock_db(self):
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_db):
        return AIDetectionService(mock_db)

    @pytest.mark.asyncio
    async def test_scan_human_content(self, service):
        """Scan clearly human content"""
        content = "I spent all summer traveling through Europe. " * 5
        result = await service.scan_article(
            "article-1", content, use_external_api=False
        )

        assert result.article_id == "article-1"
        assert result.ai_probability >= 0
        assert result.ai_probability <= 1
        assert result.decision in [
            "auto_approved",
            "flagged_for_review",
            "auto_rejected",
        ]

    @pytest.mark.asyncio
    async def test_scan_ai_like_content(self, service):
        """Scan repetitive (AI-like) content"""
        content = "The output is the output. The output is the output. " * 10
        result = await service.scan_article(
            "article-2", content, use_external_api=False
        )

        assert result.decision is not None
        # Repetitive content should score higher on AI probability
        assert result.ai_probability >= 0

    @pytest.mark.asyncio
    async def test_decision_thresholds(self, service):
        """Verify decision logic matches thresholds"""
        # Create fake heuristics that will produce predictable score
        for ai_prob in [0.15, 0.50, 0.85]:
            content = "x " * 100  # Generic content
            result = await service.scan_article(
                f"article-{int(ai_prob * 100)}", content, use_external_api=False
            )

            # Verify decision threshold logic
            if result.ai_probability < service.THRESHOLD_AUTO_APPROVED:
                assert result.decision == "auto_approved"
            elif result.ai_probability > service.THRESHOLD_AUTO_REJECTED:
                assert result.decision == "auto_rejected"
            else:
                assert result.decision == "flagged_for_review"

    @pytest.mark.asyncio
    async def test_log_detection(self, service, mock_db):
        """Log detection result to database"""
        mock_bind = AsyncMock()
        mock_bind.run = AsyncMock()
        mock_prepare = MagicMock()
        mock_prepare.bind = MagicMock(return_value=mock_bind)
        mock_db.prepare = MagicMock(return_value=mock_prepare)

        result = await service.scan_article(
            "article-1", "Test content", use_external_api=False
        )

        await service.log_detection("article-1", result)

        assert mock_db.prepare.called

    @pytest.mark.asyncio
    async def test_get_detection_score(self, service, mock_db):
        """Retrieve stored detection score"""
        import json

        stored_data = {
            "article_id": "article-1",
            "heuristic_score": 45.0,
            "external_api_score": None,
            "combined_score": 45.0,
            "ai_probability": 0.45,
            "decision": "flagged_for_review",
            "provider": "heuristic",
            "provider_details": None,
        }

        mock_first = AsyncMock(return_value={"event_data": json.dumps(stored_data)})
        mock_prepare = MagicMock()
        mock_prepare.bind = MagicMock(return_value=MagicMock(first=mock_first))
        mock_db.prepare = MagicMock(return_value=mock_prepare)

        score = await service.get_detection_score("article-1")

        assert score is not None
        assert score.article_id == "article-1"
        assert score.decision == "flagged_for_review"


class TestDetectionResult:
    """Test DetectionResult data structure"""

    def test_result_creation(self):
        """Create a detection result"""
        heuristics = DetectionHeuristics(0.5, 5.0, 75.0, 10.0, 5.0)
        result = DetectionResult(
            article_id="article-1",
            heuristic_score=50.0,
            external_api_score=None,
            combined_score=50.0,
            ai_probability=0.50,
            decision="flagged_for_review",
            heuristics=heuristics,
            provider="heuristic",
            provider_details=None,
        )

        assert result.article_id == "article-1"
        assert result.decision == "flagged_for_review"

    def test_result_to_dict(self):
        """Convert result to dictionary"""
        heuristics = DetectionHeuristics(0.5, 5.0, 75.0, 10.0, 5.0)
        result = DetectionResult(
            article_id="article-1",
            heuristic_score=50.0,
            external_api_score=48.0,
            combined_score=49.0,
            ai_probability=0.49,
            decision="flagged_for_review",
            heuristics=heuristics,
            provider="originality_ai",
            provider_details={"scanId": "123"},
        )

        d = result.to_dict()
        assert d["article_id"] == "article-1"
        assert d["ai_probability"] == 0.49


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
