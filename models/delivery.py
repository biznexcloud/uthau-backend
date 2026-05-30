from core.database import Base
from sqlalchemy import Column, Integer, String, Float, Enum, ForeignKey, DateTime, Text
from sqlalchemy.sql import func
import enum


class DeliveryStatus(str, enum.Enum):
    PENDING = "pending"
    ASSIGNED = "assigned"
    ARRIVED_PICKUP = "arrived_pickup"
    PICKED_UP = "picked_up"
    IN_TRANSIT = "in_transit"
    ARRIVED_DROP = "arrived_drop"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class PaymentMethod(str, enum.Enum):
    CASH = "cash"
    WALLET = "wallet"
    ESEWA = "esewa"
    KHALTI = "khalti"
    CONNECTIPS = "connectips"
    CARD = "card"


class PaymentStatus(str, enum.Enum):
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"
    REFUNDED = "refunded"


class GoodsType(str, enum.Enum):
    BUILDING_MATERIALS = "building_materials"
    EVENT_MANAGEMENT = "event_management"
    CERAMIC_SANITARY = "ceramic_sanitary"
    PAINTS_CHEMICALS = "paints_chemicals"
    ELECTRICAL = "electrical"
    ELECTRONICS = "electronics"
    FMCG = "fmcg"
    HOMEMADE_FOOD = "homemade_food"
    FURNITURE = "furniture"
    GENERAL_GOODS = "general_goods"
    HARDWARES = "hardwares"
    HOUSE_SHIFTING = "house_shifting"
    MACHINES_EQUIPMENT = "machines_equipment"
    PHARMACEUTICAL = "pharmaceutical"
    PLASTIC_PRODUCTS = "plastic_products"
    RUBBER_PRODUCTS = "rubber_products"
    TEXTILES_GARMENTS = "textiles_garments"
    TIMBERS_PLYWOODS = "timbers_plywoods"
    STATIONERY_GIFTS = "stationery_gifts"
    OTHER = "other"


class Delivery(Base):
    __tablename__ = "deliveries"
    id = Column(Integer, primary_key=True, index=True)
    crn = Column(String, unique=True, nullable=True)
    customer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    driver_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    pickup_address = Column(String, nullable=False)
    pickup_lat = Column(Float, nullable=True)
    pickup_lng = Column(Float, nullable=True)
    dropoff_address = Column(String, nullable=False)
    dropoff_lat = Column(Float, nullable=True)
    dropoff_lng = Column(Float, nullable=True)

    vehicle_type_id = Column(Integer, ForeignKey("vehicle_types.id"), nullable=True)
    goods_type = Column(Enum(GoodsType), nullable=True)
    description = Column(Text, nullable=True)

    status = Column(Enum(DeliveryStatus), default=DeliveryStatus.PENDING)
    scheduled_at = Column(DateTime(timezone=True), nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    distance_km = Column(Float, default=0)
    duration_min = Column(Float, default=0)
    base_fare = Column(Float, default=0)
    surge_multiplier = Column(Float, default=1.0)
    total_fare = Column(Float, default=0)
    commission_percent = Column(Float, default=20.0)
    net_earnings = Column(Float, default=0)

    payment_method = Column(Enum(PaymentMethod), default=PaymentMethod.CASH)
    payment_status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING)
    proof_photo_url = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
