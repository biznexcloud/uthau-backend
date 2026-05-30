from sqlalchemy.orm import Session
from models.delivery import Delivery, DeliveryStatus, PaymentStatus, GoodsType, PaymentMethod
from models.wallet import TxnReference, TxnType
from services.pricing import calculate_fare
from utils.helpers import generate_crn
from utils.geo import haversine_km
from core.config import settings
from datetime import datetime, timezone


def create_delivery(db: Session, customer_id: int, data: dict) -> Delivery:
    from crud.wallet import get_or_create_wallet, add_transaction

    dist = data.get("distance_km")
    dur = data.get("duration_min")
    if dist is None and data.get("pickup_lat") and data.get("dropoff_lat"):
        dist = haversine_km(data["pickup_lat"], data["pickup_lng"], data["dropoff_lat"], data["dropoff_lng"])
        dur = round(dist * 2, 1)
    fare = calculate_fare(
        vehicle_id=data.get("vehicle_type_id"),
        distance_km=dist or 1,
        duration_min=dur or 5,
        db=db,
    )
    scheduled = None
    if data.get("scheduled_at"):
        scheduled = datetime.fromisoformat(data["scheduled_at"])
    crn = generate_crn()
    while db.query(Delivery).filter(Delivery.crn == crn).first():
        crn = generate_crn()

    goods_type = data.get("goods_type")
    if goods_type and not isinstance(goods_type, GoodsType):
        try:
            goods_type = GoodsType(goods_type)
        except ValueError:
            goods_type = None

    payment_method = data.get("payment_method", "cash")
    if isinstance(payment_method, str):
        payment_method = PaymentMethod(payment_method)

    delivery = Delivery(
        crn=crn,
        customer_id=customer_id,
        pickup_address=data["pickup_address"],
        pickup_lat=data.get("pickup_lat"),
        pickup_lng=data.get("pickup_lng"),
        dropoff_address=data["dropoff_address"],
        dropoff_lat=data.get("dropoff_lat"),
        dropoff_lng=data.get("dropoff_lng"),
        vehicle_type_id=data.get("vehicle_type_id"),
        goods_type=goods_type,
        description=data.get("description"),
        distance_km=fare["distance_km"],
        duration_min=fare["duration_min"],
        total_fare=fare["total_fare"],
        base_fare=fare["base_fare"],
        surge_multiplier=fare["surge_multiplier"],
        commission_percent=settings.COMMISSION_PERCENT,
        payment_method=payment_method,
        scheduled_at=scheduled,
    )
    db.add(delivery)
    db.commit()
    db.refresh(delivery)

    if payment_method == PaymentMethod.WALLET:
        wallet = get_or_create_wallet(db, customer_id, "customer")
        if wallet.balance >= fare["total_fare"]:
            wallet.balance -= fare["total_fare"]
            add_transaction(
                db, wallet.id, fare["total_fare"], TxnType.DEBIT,
                TxnReference.PAYMENT, ref_id=delivery.id,
                description=f"Payment for delivery {crn}"
            )
            delivery.payment_status = PaymentStatus.PAID
            db.commit()
            db.refresh(delivery)

    return delivery


def get_delivery(db: Session, delivery_id: int) -> Delivery | None:
    return db.query(Delivery).filter(Delivery.id == delivery_id).first()


def list_deliveries(db: Session, user_id: int = None, role: str = None, status: str = None, skip: int = 0, limit: int = 10):
    q = db.query(Delivery)
    if role == "customer":
        q = q.filter(Delivery.customer_id == user_id)
    elif role == "driver":
        q = q.filter(Delivery.driver_id == user_id)
    if status:
        q = q.filter(Delivery.status == DeliveryStatus(status))
    total = q.count()
    items = q.order_by(Delivery.created_at.desc()).offset(skip).limit(limit).all()
    return items, total


def list_available_deliveries(db: Session, skip: int = 0, limit: int = 10):
    q = db.query(Delivery).filter(Delivery.status == DeliveryStatus.PENDING)
    total = q.count()
    items = q.order_by(Delivery.created_at.asc()).offset(skip).limit(limit).all()
    return items, total


def _calculate_net(total_fare: float, commission_percent: float) -> float:
    return round(total_fare * (1 - commission_percent / 100), 2)


def update_status(db: Session, delivery_id: int, status: str) -> Delivery | None:
    from crud.wallet import deposit_earning

    delivery = db.query(Delivery).filter(Delivery.id == delivery_id).first()
    if not delivery:
        return None
    delivery.status = DeliveryStatus(status)
    if status == "delivered":
        delivery.completed_at = datetime.now(timezone.utc)
        delivery.payment_status = PaymentStatus.PAID
        delivery.net_earnings = _calculate_net(delivery.total_fare, delivery.commission_percent)
        if delivery.driver_id and delivery.net_earnings > 0:
            deposit_earning(db, delivery.driver_id, delivery.net_earnings, delivery.id)
    elif status == "picked_up":
        delivery.started_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(delivery)
    return delivery


def assign_driver(db: Session, delivery_id: int, driver_id: int) -> Delivery | None:
    delivery = db.query(Delivery).filter(Delivery.id == delivery_id, Delivery.status == DeliveryStatus.PENDING).first()
    if not delivery:
        return None
    delivery.driver_id = driver_id
    delivery.status = DeliveryStatus.ASSIGNED
    db.commit()
    db.refresh(delivery)
    return delivery


def cancel_delivery(db: Session, delivery_id: int) -> Delivery | None:
    delivery = db.query(Delivery).filter(Delivery.id == delivery_id).first()
    if not delivery or delivery.status not in [DeliveryStatus.PENDING, DeliveryStatus.ASSIGNED]:
        return None
    delivery.status = DeliveryStatus.CANCELLED
    db.commit()
    db.refresh(delivery)
    return delivery


def complete_with_proof(db: Session, delivery_id: int, proof_url: str) -> Delivery | None:
    from crud.wallet import deposit_earning

    delivery = db.query(Delivery).filter(Delivery.id == delivery_id).first()
    if not delivery:
        return None
    delivery.proof_photo_url = proof_url
    delivery.status = DeliveryStatus.DELIVERED
    delivery.completed_at = datetime.now(timezone.utc)
    delivery.payment_status = PaymentStatus.PAID
    delivery.net_earnings = _calculate_net(delivery.total_fare, delivery.commission_percent)
    if delivery.driver_id and delivery.net_earnings > 0:
        deposit_earning(db, delivery.driver_id, delivery.net_earnings, delivery.id)
    db.commit()
    db.refresh(delivery)
    return delivery
