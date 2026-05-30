from datetime import datetime
from sqlalchemy.orm import Session
from core.config import settings
from models.vehicle import VehicleType


def calculate_fare(vehicle_id: int, distance_km: float, duration_min: float, db: Session) -> dict:
    vehicle = db.query(VehicleType).filter(VehicleType.id == vehicle_id).first()
    if not vehicle:
        raise ValueError("Invalid vehicle type")

    base = vehicle.base_fare
    dist_charge = round(vehicle.per_km_rate * distance_km, 2)
    time_charge = round(vehicle.per_min_rate * duration_min, 2)
    subtotal = base + dist_charge + time_charge
    final = max(subtotal, vehicle.min_fare)

    now = datetime.now()
    hour = now.hour
    surge = 1.0
    if hour >= settings.NIGHT_SURGE_START or hour < settings.NIGHT_SURGE_END:
        surge = settings.NIGHT_SURGE_MULTIPLIER

    total = round(final * surge, 2)

    return {
        "base_fare": round(base, 2),
        "distance_km": round(distance_km, 2),
        "duration_min": round(duration_min, 2),
        "distance_charge": dist_charge,
        "time_charge": time_charge,
        "surge_multiplier": surge,
        "total_fare": total,
    }
