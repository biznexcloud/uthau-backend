from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from core.database import get_db
from core.deps import require_role
from models.user import User as UserModel
from schemas.common import MessageResponse

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.post("/support/notifications", response_model=MessageResponse)
def broadcast_notification(title: str, body: str, current_user: UserModel = Depends(require_role("admin"))):
    return {"message": f"Notification queued: {title}"}
