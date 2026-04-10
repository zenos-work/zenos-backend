"""
Phase 13 - Step 51: AI Content Detection Pipeline
Detect AI-generated content to protect monetized pool from programmatic draining.
"""

from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple
from enum import Enum
import json


class DetectionProvider(str, Enum):
    """Supported AI detection providers"""

    GPTZERO = "gptzero"
    ORIGINALITY_AI = "originality_ai"
    HEURISTIC = "heuristic"


@dataclass
class DetectionHeuristics:
    """Heuristic-based AI detection metrics"""

    vocabulary_diversity: float  # Type-Token Ratio (TTR): 0-1 (higher = more human)
    sentence_length_variance: float  # Std dev of sentence lengths: 0-100+
    perplexity_score: float  # Estimated perplexity: 1-200+ (higher = more natural)
    repetition_rate: float  # % of repeated n-grams: 0-100
    entropy_score: float  # Shannon entropy of word distribution: 0-10

    def calculate_score(self) -> float:
        """Combine heuristics into single 0-100 AI probability score"""
        # Normalize each metric to 0-100.
        # Higher = more likely AI

        # TTR: Lower is more AI-like (avg 0.4-0.6)
        ttr_score = max(0, 100 - (self.vocabulary_diversity * 100))

        # Sentence variance: Very consistent is AI-like
        variance_score = max(0, 100 - min(self.sentence_length_variance, 30))

        # Perplexity: 1-50 (low) more AI, 50-200+ (high) more human
        if self.perplexity_score < 50:
            perplexity_score = 80  # Likely AI
        elif self.perplexity_score > 100:
            perplexity_score = 20  # Likely human
        else:
            perplexity_score = 50 - (self.perplexity_score - 50) // 2

        # Repetition: > 15% more AI-like
        repetition_score = min(self.repetition_rate * 5, 100)

        # Entropy: Lower entropy = more AI
        entropy_score = max(0, 100 - (self.entropy_score * 10))

        # Weighted average
        weights = {
            "ttr": 0.2,
            "variance": 0.1,
            "perplexity": 0.4,
            "repetition": 0.15,
            "entropy": 0.15,
        }

        combined = (
            ttr_score * weights["ttr"]
            + variance_score * weights["variance"]
            + perplexity_score * weights["perplexity"]
            + repetition_score * weights["repetition"]
            + entropy_score * weights["entropy"]
        )

        return min(100, max(0, combined))


@dataclass
class DetectionResult:
    """Result of AI detection analysis"""

    article_id: str
    heuristic_score: float  # 0-100, higher = more likely AI
    external_api_score: Optional[float]  # 0-100 (if external API called)
    combined_score: float  # Weighted combination
    ai_probability: float  # Final 0-1 probability score
    decision: str  # auto_approved, flagged_for_review, auto_rejected
    heuristics: DetectionHeuristics
    provider: str
    provider_details: Optional[Dict[str, Any]]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "article_id": self.article_id,
            "heuristic_score": self.heuristic_score,
            "external_api_score": self.external_api_score,
            "combined_score": self.combined_score,
            "ai_probability": self.ai_probability,
            "decision": self.decision,
            "provider": self.provider,
            "provider_details": self.provider_details,
        }


class HeuristicDetector:
    """Pure heuristic-based AI detection (no external API)"""

    @staticmethod
    def analyze(text: str) -> DetectionHeuristics:
        """Analyze text with heuristics"""
        words = text.lower().split()
        sentences = text.split(". ")

        # 1. Type-Token Ratio (vocabulary diversity)
        unique_words = len(set(words))
        total_words = len(words)
        ttr = unique_words / max(1, total_words)

        # 2. Sentence length variance
        sentence_lengths = [len(s.split()) for s in sentences if s.strip()]
        if sentence_lengths:
            avg_length = sum(sentence_lengths) / len(sentence_lengths)
            variance = sum((x - avg_length) ** 2 for x in sentence_lengths) / len(
                sentence_lengths
            )
            variance_score = variance**0.5  # Standard deviation
        else:
            variance_score = 0

        # 3. Simple perplexity estimation (word frequency)
        word_counts = {}
        for word in words:
            word_counts[word] = word_counts.get(word, 0) + 1

        perplexity_estimate = (
            sum(
                (count / total_words) * -import_math_log(count / total_words)
                for count in word_counts.values()
                if count > 0
            )
            if total_words > 0
            else 0
        )

        # 4. Repetition rate (% of repeated bigrams)
        bigrams = [" ".join(words[i : i + 2]) for i in range(len(words) - 1)]
        repeated_bigrams = sum(1 for b in set(bigrams) if bigrams.count(b) > 1)
        repetition_rate = (
            (repeated_bigrams / max(1, len(bigrams))) * 100 if bigrams else 0
        )

        # 5. Shannon entropy of word distribution
        entropy = (
            sum(
                -(count / total_words) * import_math_log(count / total_words)
                for count in word_counts.values()
                if count > 0
            )
            if total_words > 0
            else 0
        )
        entropy = min(10, entropy)  # Normalize to 0-10

        return DetectionHeuristics(
            vocabulary_diversity=ttr,
            sentence_length_variance=variance_score,
            perplexity_score=perplexity_estimate,
            repetition_rate=repetition_rate,
            entropy_score=entropy,
        )


def import_math_log(x: float) -> float:
    """Log helper to avoid import at module level"""
    import math

    return math.log(x) if x > 0 else 0


class AIDetectionService:
    """Complete AI detection pipeline with heuristics + external API"""

    # Decision thresholds
    THRESHOLD_AUTO_APPROVED = 0.30  # < 30% = auto-approve
    THRESHOLD_FLAGGED = 0.70  # 30-70% = flag for human review
    THRESHOLD_AUTO_REJECTED = 0.70  # > 70% = auto-reject

    def __init__(self, db: Any, external_api_key: Optional[str] = None):
        """
        Initialize detection service.

        Args:
            db: D1 database connection
            external_api_key: Optional API key for external service (GPT Zero, etc)
        """
        self.db = db
        self.external_api_key = external_api_key
        self.heuristic_detector = HeuristicDetector()

    async def scan_article(
        self,
        article_id: str,
        content: str,
        use_external_api: bool = False,
        provider: str = "originality_ai",
    ) -> DetectionResult:
        """
        Scan article for AI-generated content.

        Args:
            article_id: Article to scan
            content: Article content (title + body)
            use_external_api: Whether to call external detection service
            provider: Which external provider to use

        Returns:
            DetectionResult with decision
        """
        # Step 1: Heuristic analysis
        heuristics = self.heuristic_detector.analyze(content)
        heuristic_score = heuristics.calculate_score()

        # Step 2: Optional external API call
        external_score = None
        provider_details = None

        if use_external_api and self.external_api_key:
            try:
                external_score, provider_details = await self._call_external_api(
                    content, provider
                )
            except Exception as e:
                # Log but don't fail if external API unavailable
                provider_details = {"error": str(e)}

        # Step 3: Combine scores
        if external_score is not None:
            # Weight: 40% heuristic, 60% external
            combined_score = (heuristic_score * 0.4) + (external_score * 0.6)
        else:
            combined_score = heuristic_score

        # Step 4: Make decision
        ai_probability = combined_score / 100.0

        if ai_probability < self.THRESHOLD_AUTO_APPROVED:
            decision = "auto_approved"
        elif ai_probability > self.THRESHOLD_AUTO_REJECTED:
            decision = "auto_rejected"
        else:
            decision = "flagged_for_review"

        result = DetectionResult(
            article_id=article_id,
            heuristic_score=heuristic_score,
            external_api_score=external_score,
            combined_score=combined_score,
            ai_probability=ai_probability,
            decision=decision,
            heuristics=heuristics,
            provider=provider if external_score else "heuristic",
            provider_details=provider_details,
        )

        return result

    async def _call_external_api(
        self, content: str, provider: str
    ) -> Tuple[Optional[float], Optional[Dict[str, Any]]]:
        """
        Call external AI detection API.

        Returns (score, details) or (None, error_details) on failure
        """
        if provider == "gptzero":
            return await self._call_gptzero(content)
        elif provider == "originality_ai":
            return await self._call_originality_ai(content)
        else:
            return None, {"error": f"Unknown provider: {provider}"}

    async def _call_gptzero(
        self, content: str
    ) -> Tuple[Optional[float], Dict[str, Any]]:
        """Call GPT Zero API"""
        # Mock implementation - actual would use fetch to call API
        return None, {"note": "GPTZero integration requires API setup"}

    async def _call_originality_ai(
        self, content: str
    ) -> Tuple[Optional[float], Dict[str, Any]]:
        """Call Originality.ai API"""
        # Mock implementation - actual would use fetch to call API
        return None, {"note": "Originality.ai integration requires API setup"}

    async def log_detection(
        self,
        article_id: str,
        result: DetectionResult,
    ) -> None:
        """Log detection result to article_events table"""
        try:
            query = """
                INSERT INTO article_events (
                    article_id, event_type, event_data, created_at
                ) VALUES (?, ?, ?, datetime('now'))
            """

            event_data = json.dumps(result.to_dict())

            await (
                self.db.prepare(query)
                .bind(article_id, "ai_detection", event_data)
                .run()
            )
        except Exception as e:
            # Log but don't fail
            print(f"Failed to log AI detection: {str(e)}")

    async def get_detection_score(self, article_id: str) -> Optional[DetectionResult]:
        """Retrieve stored detection score"""
        query = """
            SELECT event_data FROM article_events
            WHERE article_id = ? AND event_type = 'ai_detection'
            ORDER BY created_at DESC
            LIMIT 1
        """

        try:
            row = await self.db.prepare(query).bind(article_id).first()

            if not row:
                return None

            data = json.loads(row["event_data"])

            # Reconstruct DetectionResult from stored data
            return DetectionResult(
                article_id=data["article_id"],
                heuristic_score=data["heuristic_score"],
                external_api_score=data.get("external_api_score"),
                combined_score=data["combined_score"],
                ai_probability=data["ai_probability"],
                decision=data["decision"],
                heuristics=DetectionHeuristics(
                    vocabulary_diversity=0,  # Heuristics not stored
                    sentence_length_variance=0,
                    perplexity_score=0,
                    repetition_rate=0,
                    entropy_score=0,
                ),
                provider=data.get("provider", "unknown"),
                provider_details=data.get("provider_details"),
            )
        except Exception as e:
            print(f"Failed to get detection score: {str(e)}")
            return None
