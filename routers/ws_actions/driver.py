from core.ws_registry import on
from crud import delivery as delivery_crud
from crud import user as user_crud


@on("driver_accept")
async def accept_delivery(data: dict, db, user: dict = None):
    if user and user.get("role") != "driver":
        raise PermissionError("Only drivers can accept deliveries")
    delivery_id = data.get("delivery_id")
    driver_id = data.get("driver_id")
    if user and not data.get("driver_id"):
        driver_id = user.get("user_id")
    delivery = delivery_crud.assign_driver(db, delivery_id, driver_id)
    if not delivery:
        raise ValueError("Unable to accept delivery")
    return {"id": delivery.id, "status": delivery.status.value}


@on("driver_update_status")
async def update_status(data: dict, db, user: dict = None):
    if user and user.get("role") not in ("driver", "admin"):
        raise PermissionError("Only drivers or admins can update status")
    delivery_id = data.get("delivery_id")
    status = data.get("status")
    delivery = delivery_crud.update_status(db, delivery_id, status)
    if not delivery:
        raise ValueError("Unable to update status")
    return {"id": delivery.id, "status": delivery.status.value}


@on("driver_toggle_online")
async def toggle_online(data: dict, db, user: dict = None):
    if user and user.get("role") != "driver":
        raise PermissionError("Only drivers can toggle online status")
    driver_id = data.get("driver_id")
    if user and not data.get("driver_id"):
        driver_id = user.get("user_id")
    online = data.get("online", True)
    result = user_crud.toggle_online(db, driver_id, online)
    return {"is_online": result.is_online}
