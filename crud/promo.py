from sqlalchemy.orm import Session
from models.promo import PromoCode, PromoUsage, PromoType
from datetime import datetime, timezone


def create_promo(db: Session, **kwargs) -> PromoCode:
    promo = PromoCode(**kwargs)
    db.add(promo)
    db.commit()
    db.refresh(promo)
    return promo


def list_promos(db: Session, skip: int = 0, limit: int = 10):
    q = db.query(PromoCode)
    total = q.count()
    items = q.offset(skip).limit(limit).all()
    return items, total


def validate_and_apply(db: Session, code: str, trip_amount: float, user_id: int):
    promo = db.query(PromoCode).filter(PromoCode.code == code, PromoCode.is_active == True).first()
    if not promo:
        return {"valid": False, "discount": 0, "final_amount": trip_amount, "message": "Invalid code"}
    if promo.expires_at and promo.expires_at < datetime.now(timezone.utc):
        return {"valid": False, "discount": 0, "final_amount": trip_amount, "message": "Code expired"}
    if promo.used_count >= promo.usage_limit:
        return {"valid": False, "discount": 0, "final_amount": trip_amount, "message": "Usage limit reached"}
    if trip_amount < promo.min_trip_value:
        return {"valid": False, "discount": 0, "final_amount": trip_amount, "message": f"Min trip Rs.{promo.min_trip_value}"}
    discount = (promo.value / 100 * trip_amount) if promo.type == PromoType.PERCENT else promo.value
    if promo.max_discount:
        discount = min(discount, promo.max_discount)
    final = max(0, trip_amount - discount)
    promo.used_count += 1
    usage = PromoUsage(promo_id=promo.id, user_id=user_id, discount_amount=discount)
    db.add(usage)
    db.commit()
    return {"valid": True, "discount": discount, "final_amount": final, "message": "Applied"}
