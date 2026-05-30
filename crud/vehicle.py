from sqlalchemy.orm import Session
from models.vehicle import VehicleType


def list_vehicles(db: Session):
    return db.query(VehicleType).filter(VehicleType.is_active == 1).all()


def get_vehicle(db: Session, vehicle_id: int) -> VehicleType | None:
    return db.query(VehicleType).filter(VehicleType.id == vehicle_id).first()


def update_vehicle(db: Session, vehicle_id: int, **kwargs) -> VehicleType | None:
    v = db.query(VehicleType).filter(VehicleType.id == vehicle_id).first()
    if v:
        for k, val in kwargs.items():
            if val is not None:
                setattr(v, k, val)
        db.commit()
        db.refresh(v)
    return v
