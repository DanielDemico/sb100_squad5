"""Core module — shared settings and schemas.

This module centralizes the fundamental definitions of the SmartB100 system:

- **Settings**: Environment parameters and system defaults (via Pydantic Settings).
- **Schemas**: Pydantic models defining the public API contract (requests/responses).

Exports:
    settings: Singleton instance of the system settings.
    ChatMessage: Shared chat message contract.
    ExpertiseLevel: Enum of user expertise levels.
    UserProfile: User profile schema.
    ChatRequest: Chat request schema.
    ChatResponse: Chat response schema.
"""

from core.config import settings
from core.schemas import (
    ChatMessage,
    ChatRequest,
    ChatResponse,
    ExpertiseLevel,
    RegisterResponse,
    RetrievalChunk,
    RetrievalSource,
    Token,
    UserCreate,
    UserProfile,
)

__all__ = [
    "settings",
    "ChatMessage",
    "ExpertiseLevel",
    "UserProfile",
    "ChatRequest",
    "ChatResponse",
    "RetrievalSource",
    "RetrievalChunk",
    "UserCreate",
    "RegisterResponse",
    "Token",
]
