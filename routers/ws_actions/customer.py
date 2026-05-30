from core.ws_registry import on
from crud import delivery as delivery_crud
from services.pricing import calculate_fare


@on("customer_track_delivery")
async def track_delivery(data: dict, db, user: dict = None):
    if user and user.get("role") != "customer":
        raise PermissionError("Only customers can track deliveries")
    delivery_id = data.get("delivery_id")
    delivery = delivery_crud.get_delivery(db, delivery_id)
    if not delivery:
        raise ValueError("Delivery not found")
    if user and delivery.customer_id != user.get("user_id"):
        raise PermissionError("Not your delivery")
    return {
        "id": delivery.id,
        "status": delivery.status.value,
        "driver_id": delivery.driver_id,
        "pickup_lat": delivery.pickup_lat,
        "pickup_lng": delivery.pickup_lng,
        "dropoff_lat": delivery.dropoff_lat,
        "dropoff_lng": delivery.dropoff_lng,
    }


@on("customer_fare_estimate")
async def fare_estimate(data: dict, db, user: dict = None):
    return calculate_fare(
        vehicle_id=data.get("vehicle_type_id"),
        distance_km=data.get("distance_km", 5),
        duration_min=data.get("duration_min", 10),
        db=db,
    )
