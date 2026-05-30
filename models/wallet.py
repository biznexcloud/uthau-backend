from core.database import Base
from sqlalchemy import Column, Integer, String, Float, Enum, ForeignKey, DateTime
from sqlalchemy.sql import func
import enum


class WalletType(str, enum.Enum):
    CUSTOMER = "customer"
    DRIVER = "driver"


class TxnType(str, enum.Enum):
    CREDIT = "credit"
    DEBIT = "debit"


class TxnReference(str, enum.Enum):
    TOPUP = "topup"
    EARNING = "earning"
    WITHDRAW = "withdraw"
    REFUND = "refund"
    COMMISSION = "commission"
    PAYMENT = "payment"
    COIN_CONVERSION = "coin_conversion"


class Wallet(Base):
    __tablename__ = "wallets"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    balance = Column(Float, default=0)
    type = Column(Enum(WalletType), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class WalletTransaction(Base):
    __tablename__ = "wallet_transactions"
    id = Column(Integer, primary_key=True, index=True)
    wallet_id = Column(Integer, ForeignKey("wallets.id"), nullable=False)
    amount = Column(Float, nullable=False)
    type = Column(Enum(TxnType), nullable=False)
    reference = Column(Enum(TxnReference), nullable=False)
    ref_id = Column(Integer, nullable=True)
    description = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
