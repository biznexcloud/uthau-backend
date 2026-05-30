from sqlalchemy.orm import Session
from models.wallet import Wallet, WalletTransaction, WalletType, TxnType, TxnReference


def get_or_create_wallet(db: Session, user_id: int, wallet_type: str = "customer") -> Wallet:
    wallet = db.query(Wallet).filter(Wallet.user_id == user_id).first()
    if not wallet:
        wallet = Wallet(user_id=user_id, balance=0, type=WalletType(wallet_type))
        db.add(wallet)
        db.commit()
        db.refresh(wallet)
    return wallet


def get_balance(db: Session, user_id: int) -> float:
    wallet = get_or_create_wallet(db, user_id)
    return wallet.balance


def add_transaction(db: Session, wallet_id: int, amount: float, txn_type: TxnType, reference: TxnReference, ref_id: int = None, description: str = None) -> WalletTransaction:
    txn = WalletTransaction(
        wallet_id=wallet_id, amount=amount, type=txn_type,
        reference=reference, ref_id=ref_id, description=description,
    )
    db.add(txn)
    return txn


def topup(db: Session, user_id: int, amount: float) -> Wallet:
    wallet = get_or_create_wallet(db, user_id)
    wallet.balance += amount
    add_transaction(db, wallet.id, amount, TxnType.CREDIT, TxnReference.TOPUP, description=f"Topup Rs.{amount}")
    db.commit()
    db.refresh(wallet)
    return wallet


def deduct(db: Session, user_id: int, amount: float, ref_id: int = None) -> Wallet:
    wallet = get_or_create_wallet(db, user_id)
    if wallet.balance < amount:
        raise ValueError("Insufficient balance")
    wallet.balance -= amount
    add_transaction(db, wallet.id, amount, TxnType.DEBIT, TxnReference.PAYMENT, ref_id=ref_id, description=f"Payment Rs.{amount}")
    db.commit()
    db.refresh(wallet)
    return wallet


def deposit_earning(db: Session, user_id: int, amount: float, delivery_id: int = None) -> Wallet:
    wallet = get_or_create_wallet(db, user_id, wallet_type="driver")
    wallet.balance += amount
    add_transaction(db, wallet.id, amount, TxnType.CREDIT, TxnReference.EARNING, ref_id=delivery_id, description=f"Earning Rs.{amount}")
    db.commit()
    db.refresh(wallet)
    return wallet


def withdraw(db: Session, user_id: int, amount: float) -> Wallet:
    wallet = get_or_create_wallet(db, user_id, wallet_type="driver")
    if wallet.balance < amount:
        raise ValueError("Insufficient balance")
    wallet.balance -= amount
    add_transaction(db, wallet.id, amount, TxnType.DEBIT, TxnReference.WITHDRAW, description=f"Withdraw Rs.{amount}")
    db.commit()
    db.refresh(wallet)
    return wallet


def list_transactions(db: Session, user_id: int, skip: int = 0, limit: int = 10):
    wallet = get_or_create_wallet(db, user_id)
    q = db.query(WalletTransaction).filter(WalletTransaction.wallet_id == wallet.id)
    total = q.count()
    items = q.order_by(WalletTransaction.created_at.desc()).offset(skip).limit(limit).all()
    return items, total
