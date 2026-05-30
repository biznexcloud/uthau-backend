from core.database import SessionLocal
from core.security import hash_password
from models.user import User, UserRole
from models.vehicle import VehicleType

VEHICLES = [
    {"name": "Bike", "capacity_kg": 50, "base_fare": 30, "per_km_rate": 15, "per_min_rate": 2, "min_fare": 50},
    {"name": "Tempo (3-Wheeler)", "capacity_kg": 400, "base_fare": 80, "per_km_rate": 25, "per_min_rate": 3, "min_fare": 120},
    {"name": "Pickup", "capacity_kg": 1500, "base_fare": 150, "per_km_rate": 35, "per_min_rate": 4, "min_fare": 250},
    {"name": "Mini Truck (Ace)", "capacity_kg": 1000, "base_fare": 200, "per_km_rate": 40, "per_min_rate": 5, "min_fare": 350},
    {"name": "10ft Truck", "capacity_kg": 3000, "base_fare": 400, "per_km_rate": 55, "per_min_rate": 7, "min_fare": 600},
    {"name": "14ft Truck", "capacity_kg": 5000, "base_fare": 600, "per_km_rate": 70, "per_min_rate": 9, "min_fare": 900},
    {"name": "EV Rickshaw", "capacity_kg": 200, "base_fare": 40, "per_km_rate": 12, "per_min_rate": 1.5, "min_fare": 60},
]


def seed():
    db = SessionLocal()
    try:
        if not db.query(User).filter(User.role == UserRole.ADMIN).first():
            admin = User(
                name="Admin",
                phone="9800000000",
                email="admin@uthaunepal.com",
                password_hash=hash_password("admin123"),
                role=UserRole.ADMIN,
            )
            db.add(admin)
            print("Created admin user (phone: 9800000000, password: admin123)")

        existing = {v.name for v in db.query(VehicleType).all()}
        for vd in VEHICLES:
            if vd["name"] not in existing:
                db.add(VehicleType(**vd))
                print(f"Added vehicle: {vd['name']}")

        db.commit()
        print("Seed complete.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
