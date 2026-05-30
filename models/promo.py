from core.database import Base
from sqlalchemy import Column, Integer, String, Float, Enum, ForeignKey, DateTime, Boolean
from sqlalchemy.sql import func
import enum


class PromoType(str, enum.Enum):
    PERCENT = "percent"
    FLAT = "flat"


class PromoCode(Base):
    __tablename__ = "promo_codes"
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, nullable=False)
    type = Column(Enum(PromoType), nullable=False)
    value = Column(Float, nullable=False)
    min_trip_value = Column(Float, default=0)
    max_discount = Column(Float, nullable=True)
    usage_limit = Column(Integer, default=100)
    used_count = Column(Integer, default=0)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class PromoUsage(Base):
    __tablename__ = "promo_usages"
    id = Column(Integer, primary_key=True, index=True)
    promo_id = Column(Integer, ForeignKey("promo_codes.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    delivery_id = Column(Integer, ForeignKey("deliveries.id"), nullable=True)
    discount_amount = Column(Float, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Referral(Base):
    __tablename__ = "referrals"
    id = Column(Integer, primary_key=True, index=True)
    referrer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    referee_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    reward_amount = Column(Float, default=0)
    status = Column(String, default="pending")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
