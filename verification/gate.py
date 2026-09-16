"""Hallucination verification gate with retry and fallback.

If the entropy computation fails, verification degrades to a neutral score
(0.5) while keeping the generated answer — without masking generator
failures, which must propagate to the caller as usual.
"""

import logging

from core.config import settings
from core.schemas import ChatMessage, ChatResponse, UserProfile
from generation.llm import generate
from verification.entropy import compute_entropy_score

logger = logging.getLogger(__name__)

MAX_RETRIES = 2
FALLBACK_MESSAGE = "I cannot answer this topic with confidence."
NEUTRAL_SCORE = 0.5


def evaluate(
    question: str,
    context: str,
    history: list[ChatMessage],
    profile: UserProfile,
) -> ChatResponse:
    """Evaluates and regenerates the answer if the entropy score exceeds the threshold.

    Logic:
        1. Generate the answer — if it fails, propagate (generator errors are
           a real 503 case).
        2. Compute the entropy score — if it fails, return the answer with a
           neutral 0.5 score (verification is optional; its failure must not
           take down the pipeline).
        3. If score <= threshold, return the answer.
        4. If it exceeds, regenerate up to ``MAX_RETRIES``.
        5. After exhausting attempts, return ``FALLBACK_MESSAGE`` with the last score.

    Args:
        question: Current user question.
        context: Retrieved context used by generation and verification.
        history: Previous chat turns included in generation.
        profile: User profile that selects the answer style.

    Returns:
        Chat response with the accepted answer and entropy score, a neutral
        score if verification fails, or a fallback message after retries.

    Raises:
        Exception: Propagates answer-generation failures; verification failures
            are intentionally degraded to ``NEUTRAL_SCORE``.

    QUALITY: long-function-justification - generation, entropy scoring, retry,
    verifier-failure degradation, and final fallback are the atomic gate policy.
    """
    last_score = 0.0

    for attempt in range(MAX_RETRIES):
        answer = generate(
            question=question,
            context=context,
            history=history,
            profile=profile,
        )

        try:
            last_score = compute_entropy_score(
                question=question,
                context=context,
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception(
                "verification.gate.entropy_failure",
                extra={"attempt": attempt, "error": str(exc)},
            )
            return ChatResponse(answer=answer, hallucination_score=NEUTRAL_SCORE)

        if last_score <= settings.hallucination_threshold:
            return ChatResponse(answer=answer, hallucination_score=last_score)

    return ChatResponse(answer=FALLBACK_MESSAGE, hallucination_score=last_score)


def score_context(question: str, context: str) -> float:
    """Score the trustworthiness of an answer grounded in ``context`` for the agent path.

    Returns the neutral score when there is no context to verify; otherwise runs the
    semantic-entropy score with the same neutral fallback as ``evaluate`` on verifier failure.

    Args:
        question: User question associated with the agent answer.
        context: Context retrieved by the agent's corpus-search tool.

    Returns:
        Semantic entropy score, or ``NEUTRAL_SCORE`` when context is empty or
        verification fails.
    """
    if not context.strip():
        return NEUTRAL_SCORE
    try:
        return compute_entropy_score(question=question, context=context)
    except Exception as exc:  # noqa: BLE001
        logger.exception("verification.score_context.failure", extra={"error": str(exc)})
        return NEUTRAL_SCORE
