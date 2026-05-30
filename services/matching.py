from sqlalchemy.orm import Session
from models.user import User, UserRole
from utils.geo import haversine_km


def find_nearest_driver(db: Session, lat: float = None, lng: float = None, max_km: float = 10.0) -> User | None:
    drivers = (
        db.query(User)
        .filter(User.role == UserRole.DRIVER, User.is_online == True, User.is_kyc_verified == True)
        .all()
    )

    if not drivers:
        return None

    if lat is None or lng is None:
        return drivers[0]

    best_driver = None
    best_distance = float("inf")

    for driver in drivers:
        if hasattr(driver, "last_lat") and hasattr(driver, "last_lng"):
            if driver.last_lat and driver.last_lng:
                dist = haversine_km(lat, lng, driver.last_lat, driver.last_lng)
                if dist <= max_km and dist < best_distance:
                    best_distance = dist
                    best_driver = driver

    if best_driver:
        return best_driver

    return drivers[0]
