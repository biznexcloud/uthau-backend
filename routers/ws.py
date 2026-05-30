import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from core.database import SessionLocal
from core.security import decode_token
from core.ws_registry import dispatch
from models.user import User
from . import ws_actions

router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str = Query(None)):
    if not token:
        await websocket.close(code=4001, reason="Token required")
        return

    db = SessionLocal()
    try:
        try:
            payload = decode_token(token)
            user_id = payload.get("user_id")
            user_role = payload.get("role")
        except Exception:
            await websocket.close(code=4003, reason="Invalid token")
            return

        if not user_id:
            await websocket.close(code=4003, reason="Invalid token payload")
            return

        user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
        if not user:
            await websocket.close(code=4003, reason="User not found or inactive")
            return

        await websocket.accept()
        user_info = {"user_id": user.id, "role": user.role.value}

        while True:
            raw = await websocket.receive_text()
            message = json.loads(raw)
            action = message.get("action")
            data = message.get("data", {})

            try:
                result = await dispatch(action, data, db, user=user_info)
                await websocket.send_json(
                    {"action": action, "data": result, "status": "ok"}
                )
            except PermissionError as e:
                await websocket.send_json(
                    {
                        "action": action,
                        "data": None,
                        "status": "error",
                        "message": f"Unauthorized: {str(e)}",
                    }
                )
            except Exception as e:
                await websocket.send_json(
                    {
                        "action": action,
                        "data": None,
                        "status": "error",
                        "message": str(e),
                    }
                )

    except WebSocketDisconnect:
        pass
    finally:
        db.close()
