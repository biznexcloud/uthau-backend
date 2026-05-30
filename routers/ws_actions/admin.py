from core.ws_registry import on
from models.delivery import Delivery
from models.user import User, UserRole


@on("admin_stats")
async def admin_stats(data: dict, db, user: dict = None):
    if user and user.get("role") != "admin":
        raise PermissionError("Only admins can view stats")
    total_deliveries = db.query(Delivery).count()
    active_deliveries = db.query(Delivery).filter(
        Delivery.status.in_(["pending", "assigned", "picked_up", "in_transit"])
    ).count()
    online_drivers = db.query(User).filter(
        User.role == UserRole.DRIVER, User.is_online == True
    ).count()
    return {
        "total_deliveries": total_deliveries,
        "active_deliveries": active_deliveries,
        "online_drivers": online_drivers,
    }
