from core.database import Base
from sqlalchemy import Column, Integer, String, Float


class VehicleType(Base):
    __tablename__ = "vehicle_types"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    capacity_kg = Column(Float, default=0)
    image_url = Column(String, nullable=True)
    base_fare = Column(Float, default=0)
    per_km_rate = Column(Float, default=0)
    per_min_rate = Column(Float, default=0)
    min_fare = Column(Float, default=0)
    is_active = Column(Integer, default=1)
