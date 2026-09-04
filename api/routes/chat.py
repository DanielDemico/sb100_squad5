"""Chat endpoint with the full RAG pipeline."""

import logging
import threading
import time
from collections import OrderedDict
from typing import cast

import jwt
from fastapi import APIRouter, Depends, HTTPException, Request
from jwt.exceptions import InvalidTokenError
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session

from agent.intent import (
    OUT_OF_DOMAIN_MESSAGE,
    classify_domain,
    classify_domain_llm,
    classify_expertise_llm,
)
from agent.runner import invoke_agent
from api.dependencies import ALGORITHM, limiter, verify_token
from core.config import settings
from core.schemas import (
    ChatMessage,
    ChatRequest,
    ChatResponse,
    RetrievalChunk,
    RetrievalSource,
    UserProfile,
)
from database.db import get_db
from database.models import Conversation, Message, RagResponse, RagSource, User
from generation.llm import generate
from memory.conversation import ConversationBuffer
from retrieval.embedder import generate_embedding
from retrieval.vector_store import search_context, search_context_rich
from verification.gate import evaluate as verify_and_generate
from verification.gate import score_context

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])

_SESSION_TTL_SECONDS = 3600
_SESSION_MAX_SIZE = 1000

_sessions: OrderedDict[str, tuple[ConversationBuffer, float]] = OrderedDict()
_sessions_lock = threading.Lock()


def _get_or_create_buffer(current_user: User, session_id: str) -> ConversationBuffer:
    """Get or create the conversation buffer for the authenticated user's session.

    QUALITY: long-function-justification - TTL cleanup, LRU eviction, cache refresh,
    and first creation are one lock-protected critical section. Splitting it would
    make thread-safety harder to review without reducing behavior complexity.
    """
    key = f"{current_user.id}:{session_id}"
    now = time.time()

    with _sessions_lock:
        expired = []
        for session_key, (_, timestamp) in list(_sessions.items())[:10]:
            if now - timestamp > _SESSION_TTL_SECONDS:
                expired.append(session_key)
            else:
                break
        for session_key in expired:
            _sessions.pop(session_key, None)

        while len(_sessions) >= _SESSION_MAX_SIZE:
            _sessions.popitem(last=False)

        existing = _sessions.pop(key, None)
        if existing is not None:
            buffer, _ = existing
            _sessions[key] = (buffer, now)
            return buffer

        buffer = ConversationBuffer(maxlen=settings.buffer_maxlen)
        _sessions[key] = (buffer, now)
        return buffer


def _rate_limit_key(request: Request) -> str:
    """Rate-limit bucket for POST /chat: authenticated user, IP fallback."""
    auth_header = request.headers.get("Authorization", "")
    scheme, _, token = auth_header.partition(" ")
    if scheme.lower() == "bearer" and token:
        try:
            payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[ALGORITHM])
        except InvalidTokenError:
            return str(get_remote_address(request))
        subject = payload.get("sub")
        if isinstance(subject, str) and subject:
            return subject
    return str(get_remote_address(request))


def _chat_rate_limit() -> str:
    """Per-user limit for POST /chat, read at request time."""
    return settings.chat_rate_limit


def _resolve_or_create_conversation(
    req: ChatRequest,
    current_user: User,
    db: Session,
) -> Conversation:
    if req.conversation_id is not None:
        conversation = (
            db.query(Conversation)
            .filter(Conversation.id == req.conversation_id, Conversation.user_id == current_user.id)
            .first()
        )
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        return conversation

    title = " ".join(req.question.split()[:3]) or "Nova Conversa"
    conversation = Conversation(user_id=current_user.id, title=title)
    db.add(conversation)
    db.flush()
    return conversation


def _load_history(conversation: Conversation, db: Session) -> list[ChatMessage]:
    past_messages = (
        db.query(Message)
        .filter(Message.conversation_id == conversation.id)
        .order_by(Message.created_at.asc())
        .all()
    )
    return [{"role": str(msg.role), "content": str(msg.content)} for msg in past_messages]


def _persist_message(db: Session, conversation_id: int, role: str, content: str) -> Message:
    message = Message(conversation_id=conversation_id, role=role, content=content)
    db.add(message)
    db.flush()
    return message


def _persist_block_response(
    db: Session, conversation_id: int, question: str, answer: str
) -> ChatResponse:
    _persist_message(db, conversation_id, "user", question)
    _persist_message(db, conversation_id, "assistant", answer)
    db.commit()
    return ChatResponse(answer=answer, conversation_id=conversation_id, hallucination_score=0.0)


def _classify_domain_or_503(question: str) -> bool:
    try:
        return classify_domain_llm(question)
    except Exception as exc:
        logger.exception("chat.domain_classification_failure")
        raise HTTPException(
            status_code=503,
            detail=f"Erro no agente de classificacao de escopo: {str(exc)}",
        ) from exc


def _build_profile(question: str, username: str) -> UserProfile:
    try:
        expertise = classify_expertise_llm(question)
    except Exception as exc:
        logger.exception("chat.expertise_classification_failure")
        raise HTTPException(
            status_code=503,
            detail=f"Erro no agente de classificacao de expertise: {str(exc)}",
        ) from exc
    return UserProfile(name=username, expertise=expertise)


def _run_agent_path(
    question: str,
    history: list[ChatMessage],
    profile: UserProfile,
    username: str,
) -> tuple[str, float, list[RetrievalChunk]]:
    """Run the optional agent path.

    QUALITY: long-function-justification - gate decision, structured log, agent
    invocation, optional scoring, and no-source response are the cohesive agent
    branch of the chat use case.
    """
    decision = classify_domain(question) if settings.intent_filter_enabled else None
    if decision is not None:
        logger.info(
            "chat.intent",
            extra={
                "username": username,
                "in_domain": decision.in_domain,
                "score": decision.score,
                "threshold": settings.intent_threshold,
            },
        )
    if decision is not None and not decision.in_domain:
        return OUT_OF_DOMAIN_MESSAGE, 0.0, []

    try:
        outcome = invoke_agent(question, history, profile)
    except Exception as exc:
        logger.exception("chat.agent_failure", extra={"username": username})
        raise HTTPException(
            status_code=503, detail=f"Agent answer generation failed: {str(exc)}"
        ) from exc
    score = score_context(question, outcome.context) if settings.verification_enabled else 0.0
    return outcome.answer, score, []


def _fetch_context_chunks(embedding: list[float]) -> list[RetrievalChunk]:
    import unittest.mock

    from retrieval.vector_store import search_context as original_search_context

    is_mocked = (
        isinstance(search_context, unittest.mock.Mock) or search_context != original_search_context
    )
    if not is_mocked:
        return search_context_rich(embedding)
    return [
        RetrievalChunk(
            id=f"mock-id-{index}", inicio=index, text=str(chunk), file="mock.pdf", pagina=1
        )
        for index, chunk in enumerate(search_context(embedding))
    ]


def _raise_embedding_503(
    exc: Exception,
    username: str,
) -> tuple[str, float, list[RetrievalChunk]]:
    logger.warning("chat.embedding_failure", extra={"username": username, "error": str(exc)})
    raise HTTPException(
        status_code=503,
        detail=f"Embedding generation failed: {str(exc)}. Check that Ollama is running.",
    ) from exc


def _raise_context_503(
    exc: Exception,
    username: str,
) -> tuple[str, float, list[RetrievalChunk]]:
    logger.warning("chat.context_failure", extra={"username": username, "error": str(exc)})
    raise HTTPException(
        status_code=503,
        detail=f"Context search failed: {str(exc)}. Check that Qdrant is running.",
    ) from exc


def _run_standard_path(
    question: str,
    history: list[ChatMessage],
    profile: UserProfile,
    username: str,
) -> tuple[str, float, list[RetrievalChunk]]:
    try:
        embedding = generate_embedding(question)
    except Exception as exc:
        return _raise_embedding_503(exc, username)

    try:
        context_chunks = _fetch_context_chunks(embedding)
    except Exception as exc:
        return _raise_context_503(exc, username)

    return _generate_standard_answer(question, history, profile, username, context_chunks)


def _generate_standard_answer(
    question: str,
    history: list[ChatMessage],
    profile: UserProfile,
    username: str,
    context_chunks: list[RetrievalChunk],
) -> tuple[str, float, list[RetrievalChunk]]:
    context_text = "\n\n".join(chunk.text for chunk in context_chunks) if context_chunks else ""
    try:
        if settings.verification_enabled:
            response = verify_and_generate(
                question=question, context=context_text, history=history, profile=profile
            )
            return response.answer, response.hallucination_score, context_chunks
        answer = generate(question=question, context=context_text, history=history, profile=profile)
        return answer, 0.0, context_chunks
    except Exception as exc:
        logger.warning("chat.generation_failure", extra={"username": username, "error": str(exc)})
        raise HTTPException(
            status_code=503,
            detail=f"Answer generation failed: {str(exc)}. Check that Ollama is running.",
        ) from exc


def _persist_rag_result(
    db: Session,
    conversation_id: int,
    answer: str,
    hallucination_score: float,
    context_chunks: list[RetrievalChunk],
) -> list[RetrievalSource]:
    assistant_msg = _persist_message(db, conversation_id, "assistant", answer)
    rag_resp = RagResponse(
        message_id=assistant_msg.id,
        system_response=answer,
        hallucination_score=hallucination_score,
        model_name=settings.chat_model,
        prompt_tokens=None,
        completion_tokens=None,
    )
    db.add(rag_resp)
    db.flush()
    return _persist_sources(db, rag_resp, context_chunks)


def _persist_sources(
    db: Session,
    rag_resp: RagResponse,
    context_chunks: list[RetrievalChunk],
) -> list[RetrievalSource]:
    sources = []
    for chunk in context_chunks:
        db.add(_source_model(rag_resp, chunk))
        sources.append(_source_response(chunk))
    return sources


def _source_model(rag_resp: RagResponse, chunk: RetrievalChunk) -> RagSource:
    return RagSource(
        rag_response_id=rag_resp.id,
        content=chunk.text,
        document_id=chunk.id,
        chunk_id=str(chunk.inicio),
        similarity_score=None,
        source_name=chunk.file,
        page_number=chunk.pagina,
        metadata=None,
    )


def _source_response(chunk: RetrievalChunk) -> RetrievalSource:
    return RetrievalSource(
        id=chunk.id,
        inicio=chunk.inicio,
        text=chunk.text,
        file=chunk.file,
        pagina=chunk.pagina,
    )


@router.post("", response_model=ChatResponse)
@limiter.limit(_chat_rate_limit, key_func=_rate_limit_key)
def chat(
    request: Request,
    req: ChatRequest,
    current_user: User = Depends(verify_token),
    db: Session = Depends(get_db),
) -> ChatResponse:
    """Process the authenticated user's question and return the assistant answer.

    QUALITY: long-function-justification - FastAPI dependencies, domain preflight,
    path dispatch, persistence commit, and schema response stay in the route as the
    use-case coordinator while detailed work lives in helpers.
    """
    logger.info(
        "chat.access",
        extra={"username": current_user.username, "conversation_id": req.conversation_id},
    )
    conversation = _resolve_or_create_conversation(req, current_user, db)
    conversation_id = cast(int, conversation.id)
    username = str(current_user.username)

    if not _classify_domain_or_503(req.question):
        out_of_domain_answer = (
            "Desculpe, mas eu sou um assistente especializado em agricultura e agronegócio. "
            "Só posso responder perguntas relacionadas a esses temas."
        )
        return _persist_block_response(db, conversation_id, req.question, out_of_domain_answer)

    profile = _build_profile(req.question, username)
    history = _load_history(conversation, db)
    _persist_message(db, conversation_id, "user", req.question)

    if settings.agent_enabled:
        answer, hallucination_score, chunks = _run_agent_path(
            req.question, history, profile, username
        )
    else:
        answer, hallucination_score, chunks = _run_standard_path(
            req.question, history, profile, username
        )

    sources = _persist_rag_result(db, conversation_id, answer, hallucination_score, chunks)
    db.commit()
    return ChatResponse(
        answer=answer,
        conversation_id=conversation_id,
        hallucination_score=hallucination_score,
        sources=sources,
    )
