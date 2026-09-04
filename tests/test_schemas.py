"""Tests for the public-contract Pydantic schemas."""

import pytest
from pydantic import ValidationError

from core.schemas import (
    ChatRequest,
    ChatResponse,
    ExpertiseLevel,
    RegisterResponse,
    RetrievalChunk,
    Token,
    UserCreate,
    UserProfile,
)


def _profile() -> UserProfile:
    return UserProfile(name="tester", expertise=ExpertiseLevel.beginner)


def test_chat_request_rejects_empty_question() -> None:
    with pytest.raises(ValidationError):
        ChatRequest(conversation_id=1, question="")


def test_chat_request_rejects_oversized_question() -> None:
    with pytest.raises(ValidationError):
        ChatRequest(conversation_id=1, question="x" * 2001)


def test_chat_request_accepts_question_at_upper_boundary() -> None:
    req = ChatRequest(conversation_id=1, question="x" * 2000)
    assert len(req.question) == 2000


def test_chat_request_accepts_typical_question() -> None:
    req = ChatRequest(
        conversation_id=1,
        question="How to grow soybeans in the Cerrado?",
    )
    assert req.question == "How to grow soybeans in the Cerrado?"
    assert req.conversation_id == 1


def test_chat_request_accepts_none_conversation_id() -> None:
    req = ChatRequest(
        conversation_id=None,
        question="How to grow soybeans?",
    )
    assert req.conversation_id is None


# ----------------------------- additional bounds ---------------------------


def test_user_profile_rejects_empty_name() -> None:
    with pytest.raises(ValidationError):
        UserProfile(name="", expertise=ExpertiseLevel.beginner)


def test_user_profile_rejects_oversized_name() -> None:
    with pytest.raises(ValidationError):
        UserProfile(name="x" * 256, expertise=ExpertiseLevel.beginner)


def test_chat_response_rejects_score_below_zero() -> None:
    with pytest.raises(ValidationError):
        ChatResponse(answer="ok", hallucination_score=-0.01)


def test_chat_response_rejects_score_above_one() -> None:
    with pytest.raises(ValidationError):
        ChatResponse(answer="ok", hallucination_score=1.01)


def test_chat_response_accepts_score_boundaries() -> None:
    low = ChatResponse(answer="ok", hallucination_score=0.0)
    high = ChatResponse(answer="ok", hallucination_score=1.0)
    assert low.hallucination_score == 0.0
    assert high.hallucination_score == 1.0


def test_auth_public_schemas_live_in_core_schemas() -> None:
    user = UserCreate(username="alice_99-prod", password="strong-pw-12")
    token = Token(access_token="jwt", token_type="bearer")
    response = RegisterResponse(message="User created successfully", username=user.username)

    assert user.__class__.__module__ == "core.schemas"
    assert token.__class__.__module__ == "core.schemas"
    assert response.__class__.__module__ == "core.schemas"


def test_retrieval_chunk_contract_includes_internal_score() -> None:
    chunk = RetrievalChunk(
        id="chunk-1",
        inicio=12,
        text="conteudo",
        file="doc.pdf",
        pagina=3,
        score=0.88,
    )

    assert chunk.__class__.__module__ == "core.schemas"
    assert chunk.score == 0.88
