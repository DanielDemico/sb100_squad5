"""Pydantic schemas for the public API contract (shared request/response)."""

import re
from datetime import datetime
from enum import StrEnum
from typing import Literal, Protocol, TypedDict

from pydantic import BaseModel, ConfigDict, Field, field_validator

_USERNAME_PATTERN = re.compile(r"^[a-zA-Z0-9_-]+$")


class ChatMessage(TypedDict):
    """Single chat message exchanged between generation, verification and agent layers."""

    role: str
    content: str


class AgentGraph(Protocol):
    """Minimal graph contract consumed by the agent runner."""

    def invoke(self, payload: dict[str, list[ChatMessage]]) -> dict[str, list[object]]:
        """Run a graph invocation and return emitted messages."""
        ...


class ExpertiseLevel(StrEnum):
    """User's familiarity level with the agricultural domain.
    Values: ``beginner``, ``intermediate``, ``expert``.
    """

    beginner = "beginner"
    intermediate = "intermediate"
    expert = "expert"


class UserProfile(BaseModel):
    """User profile used to contextualize answers."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "name": "John Silva",
                    "expertise": "intermediate",
                }
            ]
        }
    )

    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="User display name or identifier (1 to 255 characters).",
    )
    expertise: ExpertiseLevel = Field(
        ...,
        description="User's experience level in the domain (beginner, intermediate or expert).",
    )


class ChatRequest(BaseModel):
    """Message request within a chat session."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "conversation_id": 42,
                    "question": "What is the ideal soybean planting window in the Midwest region?",
                }
            ]
        }
    )

    conversation_id: int | None = Field(
        default=None,
        description="Conversation identifier from the database. If None, a new conversation is created.",
    )
    question: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="Text of the question sent by the user (1 to 2000 characters).",
    )


class RetrievalSource(BaseModel):
    """Metadata representing a single retrieved text chunk from the vector store."""

    id: str = Field(..., description="Unique chunk ID (Qdrant point ID).")
    inicio: int = Field(..., description="Starting chunk index or character offset.")
    text: str = Field(..., description="Text content of the retrieved chunk.")
    file: str | None = Field(default=None, description="Source PDF file name.")
    pagina: int | None = Field(default=None, description="PDF page number.")


class RetrievalChunk(RetrievalSource):
    """Internal retrieval result shared between vector search and the API layer."""

    score: float | None = Field(default=None, description="Vector similarity score.")


class ChatResponse(BaseModel):
    """Assistant answer after processing the question."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "answer": "Based on the indexed documentation, the recommended window is...",
                    "conversation_id": 42,
                    "hallucination_score": 0.18,
                    "sources": [
                        {
                            "id": "000d0064-f08d-4197-bca3-698a3df364d9",
                            "inicio": 16,
                            "text": "dos materiais revelaram que...",
                            "file": "Zanetti(2003)-Fino carvao2.pdf",
                            "pagina": 2,
                        }
                    ],
                }
            ]
        }
    )

    answer: str = Field(..., description="Text content of the answer to the user.")
    conversation_id: int | None = Field(
        default=None,
        description="Unique conversation identifier.",
    )
    hallucination_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Estimated hallucination risk (0.0 grounded — 1.0 likely hallucinated).",
    )
    sources: list[RetrievalSource] = Field(
        default_factory=list,
        description="The list of retrieval sources used to answer the question.",
    )


class ConversationResponse(BaseModel):
    """Metadata representing a single conversation."""

    id: int = Field(..., description="Unique conversation identifier.")
    user_id: int = Field(..., description="User owner identifier.")
    title: str = Field(..., description="Title of the conversation.")
    created_at: datetime = Field(..., description="Time the conversation was created.")
    updated_at: datetime = Field(..., description="Time the conversation was last updated.")


class UserCreate(BaseModel):
    """Schema for creating a new user."""

    username: str = Field(..., min_length=1, max_length=50)
    password: str = Field(..., min_length=8, max_length=128)

    @field_validator("username")
    @classmethod
    def _validate_username(cls, value: str) -> str:
        if not _USERNAME_PATTERN.match(value):
            raise ValueError("username must contain only letters, digits, hyphen and underscore")
        return value


class RegisterResponse(BaseModel):
    """Response schema for successful user registration."""

    message: str
    username: str


class Token(BaseModel):
    """Response schema containing the JWT."""

    access_token: str
    token_type: Literal["bearer"]
