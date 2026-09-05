"""Routes to manage user conversations."""

import logging
from datetime import datetime
from typing import cast

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from api.dependencies import verify_token
from core.schemas import ConversationResponse
from database.db import get_db
from database.models import Conversation, User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.get("", response_model=list[ConversationResponse])
def list_conversations(
    db: Session = Depends(get_db),
    current_user: User = Depends(verify_token),
) -> list[ConversationResponse]:
    """Retrieve all conversations owned by the authenticated user.

    Args:
        db: SQLAlchemy session injected by FastAPI.
        current_user: User resolved from the bearer JWT.

    Returns:
        Conversation metadata sorted by creation time descending.
    """
    logger.info(
        "conversations.list",
        extra={"username": current_user.username, "user_id": current_user.id},
    )
    conversations = (
        db.query(Conversation)
        .filter(Conversation.user_id == current_user.id)
        .order_by(Conversation.created_at.desc())
        .all()
    )
    return [
        ConversationResponse(
            id=int(conversation.id),
            user_id=int(conversation.user_id),
            title=str(conversation.title),
            created_at=cast(datetime, conversation.created_at),
            updated_at=cast(datetime, conversation.updated_at),
        )
        for conversation in conversations
    ]
