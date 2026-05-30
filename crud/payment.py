from sqlalchemy.orm import Session
from models.payment import Payment
from models.delivery import PaymentStatus


def create_payment(db: Session, delivery_id: int, user_id: int, amount: float, method: str) -> Payment:
    pmt = Payment(delivery_id=delivery_id, user_id=user_id, amount=amount, method=method)
    db.add(pmt)
    db.commit()
    db.refresh(pmt)
    return pmt


def verify_payment(db: Session, payment_id: int, gateway_ref: str) -> Payment | None:
    pmt = db.query(Payment).filter(Payment.id == payment_id).first()
    if pmt:
        pmt.status = PaymentStatus.PAID
        pmt.gateway_ref = gateway_ref
        db.commit()
        db.refresh(pmt)
    return pmt


def refund_payment(db: Session, delivery_id: int) -> Payment | None:
    pmt = db.query(Payment).filter(Payment.delivery_id == delivery_id).first()
    if pmt:
        pmt.status = PaymentStatus.REFUNDED
        db.commit()
        db.refresh(pmt)
    return pmt
