import sys, random, hmac
from pathlib import Path
from datetime import datetime, timedelta, timezone
sys.path.insert(0, str(Path(__file__).parent))

from mcp.server.fastmcp import FastMCP
from core.database import SessionLocal
from core.security import (
    verify_password, create_access_token, decode_token,
    create_reset_token, hash_password,
)
from crud import user as user_crud, delivery as delivery_crud, wallet as wallet_crud
from crud import promo as promo_crud, rating as rating_crud, vehicle as vehicle_crud
from crud import address as address_crud, auth as auth_crud, payment as payment_crud
from services.pricing import calculate_fare
from services.notification import send_otp_sms
from utils.geo import haversine_km
from models.user import User, UserRole
from models.delivery import Delivery
from models.wallet import WalletTransaction, Wallet, TxnReference
from sqlalchemy import desc

mcp = FastMCP("Uthau Nepal")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@mcp.tool()
def auth_register(name: str, phone: str, password: str, role: str = "customer"):
    db = next(get_db())
    try:
        if role not in ("customer", "driver"):
            return {"error": "Role must be customer or driver"}
        if len(password) < 6:
            return {"error": "Password must be at least 6 characters"}
        existing = user_crud.get_by_phone(db, phone)
        if existing:
            return {"error": "Phone already registered"}
        user = user_crud.create_user(db, name=name, phone=phone, password=password, role=role)
        token = create_access_token({"user_id": user.id, "role": user.role.value})
        return {"access_token": token, "user_id": user.id, "name": user.name, "role": user.role.value}
    finally:
        db.close()

@mcp.tool()
def auth_login(phone: str, password: str):
    db = next(get_db())
    try:
        user = user_crud.get_by_phone(db, phone)
        if not user or not verify_password(password, user.password_hash):
            return {"error": "Invalid credentials"}
        if not user.is_active:
            return {"error": "Account disabled"}
        token = create_access_token({"user_id": user.id, "role": user.role.value})
        return {"access_token": token, "user_id": user.id, "name": user.name, "role": user.role.value}
    finally:
        db.close()

@mcp.tool()
def auth_forgot_password(phone: str):
    db = next(get_db())
    try:
        user = user_crud.get_by_phone(db, phone)
        if not user:
            return {"message": "If that phone is registered, an OTP has been sent"}
        otp = "".join([str(random.randint(0, 9)) for _ in range(6)])
        otp_hash = hash_password(otp)
        expires = datetime.now(timezone.utc) + timedelta(minutes=5)
        user.otp_code = otp_hash
        user.otp_expires_at = expires
        db.commit()
        send_otp_sms(phone, otp)
        return {"message": "If that phone is registered, an OTP has been sent"}
    finally:
        db.close()

@mcp.tool()
def auth_reset_password(token: str, new_password: str):
    db = next(get_db())
    try:
        user = db.query(User).filter(User.reset_password_token == token, User.reset_password_token_expires > datetime.now(timezone.utc)).first()
        if not user:
            return {"error": "Invalid or expired token"}
        if len(new_password) < 6:
            return {"error": "Password must be at least 6 characters"}
        auth_crud.reset_password(db, user, new_password)
        return {"message": "Password reset successfully"}
    finally:
        db.close()

@mcp.tool()
def auth_refresh_token(refresh_token: str):
    db = next(get_db())
    try:
        try:
            payload = decode_token(refresh_token)
        except Exception:
            return {"error": "Invalid refresh token"}
        user_id = payload.get("user_id")
        if not user_id:
            return {"error": "Invalid token payload"}
        user = user_crud.get_user(db, user_id)
        if not user or not user.is_active:
            return {"error": "User not found or inactive"}
        new_token = create_access_token({"user_id": user.id, "role": user.role.value})
        return {"access_token": new_token}
    finally:
        db.close()

@mcp.tool()
def auth_send_otp(phone: str):
    db = next(get_db())
    try:
        if not phone or len(phone) < 10:
            return {"error": "Invalid phone number"}
        user = user_crud.get_by_phone(db, phone)
        if not user:
            return {"message": "OTP sent if phone is registered"}
        otp = "".join([str(random.randint(0, 9)) for _ in range(6)])
        otp_hash = hash_password(otp)
        expires = datetime.now(timezone.utc) + timedelta(minutes=5)
        user.otp_code = otp_hash
        user.otp_expires_at = expires
        db.commit()
        send_otp_sms(phone, otp)
        return {"message": "OTP sent if phone is registered"}
    finally:
        db.close()

@mcp.tool()
def auth_verify_otp(phone: str, otp: str):
    db = next(get_db())
    try:
        user = user_crud.get_by_phone(db, phone)
        if not user:
            return {"error": "Phone not registered. Please register first."}
        if not user.otp_code or not hmac.compare_digest(user.otp_code, hash_password(otp)):
            return {"error": "Invalid OTP"}
        if not user.otp_expires_at or user.otp_expires_at < datetime.now(timezone.utc):
            return {"error": "OTP expired"}
        user.otp_code = None
        user.otp_expires_at = None
        db.commit()
        token = create_access_token({"user_id": user.id, "role": user.role.value})
        return {"message": "Login successful", "access_token": token, "user_id": user.id, "name": user.name, "role": user.role.value}
    finally:
        db.close()

@mcp.tool()
def auth_logout(token: str):
    db = next(get_db())
    try:
        try:
            payload = decode_token(token)
            exp = datetime.fromtimestamp(payload["exp"], tz=timezone.utc) if payload.get("exp") else None
        except Exception:
            exp = None
        auth_crud.blacklist_token(db, token, exp)
        return {"message": "Logged out successfully"}
    finally:
        db.close()

@mcp.tool()
def auth_get_current_user(user_id: int):
    db = next(get_db())
    try:
        user = user_crud.get_user(db, user_id)
        if not user:
            return {"error": "User not found"}
        return {"id": user.id, "name": user.name, "phone": user.phone, "role": user.role.value, "is_active": user.is_active, "is_kyc_verified": user.is_kyc_verified, "is_online": user.is_online, "created_at": str(user.created_at) if user.created_at else None}
    finally:
        db.close()

# ──────────────────────────────────────────────
#  CUSTOMER (13 endpoints → 13 tools)
# ──────────────────────────────────────────────

@mcp.tool()
def customer_fare_estimate(pickup_lat: float, pickup_lng: float, dropoff_lat: float, dropoff_lng: float, vehicle_type_id: int):
    db = next(get_db())
    try:
        distance_km = haversine_km(pickup_lat, pickup_lng, dropoff_lat, dropoff_lng)
        duration_min = round(distance_km * 2, 1)
        fare = calculate_fare(vehicle_id=vehicle_type_id, distance_km=distance_km, duration_min=duration_min, db=db)
        return fare
    finally:
        db.close()

@mcp.tool()
def customer_create_delivery(customer_id: int, pickup_address: str, dropoff_address: str, pickup_lat: float, pickup_lng: float, dropoff_lat: float, dropoff_lng: float, vehicle_type_id: int, distance_km: float = 0, duration_min: float = 0, payment_method: str = "cash"):
    db = next(get_db())
    try:
        data = {"pickup_address": pickup_address, "dropoff_address": dropoff_address, "pickup_lat": pickup_lat, "pickup_lng": pickup_lng, "dropoff_lat": dropoff_lat, "dropoff_lng": dropoff_lng, "vehicle_type_id": vehicle_type_id, "payment_method": payment_method}
        if distance_km: data["distance_km"] = distance_km
        if duration_min: data["duration_min"] = duration_min
        d = delivery_crud.create_delivery(db, customer_id, data)
        return {"id": d.id, "crn": d.crn, "status": d.status.value, "total_fare": float(d.total_fare), "net_earnings": float(d.net_earnings) if d.net_earnings else None}
    finally:
        db.close()

@mcp.tool()
def customer_list_deliveries(customer_id: int, status: str = "", page: int = 1, size: int = 10):
    db = next(get_db())
    try:
        skip = (page - 1) * size
        items, total = delivery_crud.list_deliveries(db, user_id=customer_id, role="customer", status=status or None, skip=skip, limit=size)
        return {"items": [{"id": d.id, "crn": d.crn, "status": d.status.value, "total_fare": float(d.total_fare), "pickup_address": d.pickup_address, "dropoff_address": d.dropoff_address} for d in items], "total": total, "page": page, "size": size}
    finally:
        db.close()

@mcp.tool()
def customer_get_delivery(delivery_id: int, customer_id: int):
    db = next(get_db())
    try:
        d = delivery_crud.get_delivery(db, delivery_id)
        if not d or d.customer_id != customer_id:
            return {"error": "Delivery not found"}
        return {"id": d.id, "crn": d.crn, "status": d.status.value, "pickup_address": d.pickup_address, "dropoff_address": d.dropoff_address, "total_fare": float(d.total_fare), "net_earnings": float(d.net_earnings) if d.net_earnings else None, "driver_id": d.driver_id, "customer_id": d.customer_id}
    finally:
        db.close()

@mcp.tool()
def customer_cancel_delivery(delivery_id: int, customer_id: int):
    db = next(get_db())
    try:
        d = delivery_crud.get_delivery(db, delivery_id)
        if not d or d.customer_id != customer_id:
            return {"error": "Delivery not found"}
        result = delivery_crud.cancel_delivery(db, delivery_id)
        if not result:
            return {"error": "Cannot cancel at current status"}
        return {"id": result.id, "status": result.status.value}
    finally:
        db.close()

@mcp.tool()
def customer_get_wallet(user_id: int):
    db = next(get_db())
    try:
        balance = wallet_crud.get_balance(db, user_id)
        return {"user_id": user_id, "balance": balance}
    finally:
        db.close()

@mcp.tool()
def customer_topup_wallet(user_id: int, amount: float):
    db = next(get_db())
    try:
        wallet = wallet_crud.topup(db, user_id, amount)
        return {"user_id": user_id, "balance": float(wallet.balance)}
    finally:
        db.close()

@mcp.tool()
def customer_wallet_transactions(user_id: int, skip: int = 0, limit: int = 10):
    db = next(get_db())
    try:
        txns = wallet_crud.list_transactions(db, user_id, skip=skip, limit=limit)
        return [{"id": t.id, "amount": float(t.amount), "type": t.type.value, "reference": t.reference.value if t.reference else None, "description": t.description, "created_at": str(t.created_at)} for t in txns]
    finally:
        db.close()

@mcp.tool()
def customer_get_profile(user_id: int):
    db = next(get_db())
    try:
        user = user_crud.get_user(db, user_id)
        if not user:
            return {"error": "User not found"}
        return {"id": user.id, "name": user.name, "phone": user.phone, "role": user.role.value, "is_active": user.is_active}
    finally:
        db.close()

@mcp.tool()
def customer_update_profile(user_id: int, name: str = "", phone: str = ""):
    db = next(get_db())
    try:
        kwargs = {}
        if name: kwargs["name"] = name
        if phone: kwargs["phone"] = phone
        user = user_crud.update_user(db, user_id, **kwargs)
        if not user:
            return {"error": "User not found"}
        return {"id": user.id, "name": user.name, "phone": user.phone}
    finally:
        db.close()

@mcp.tool()
def customer_list_addresses(user_id: int):
    db = next(get_db())
    try:
        addrs = address_crud.list_addresses(db, user_id)
        return [{"id": a.id, "label": a.label, "address": a.address, "lat": float(a.lat), "lng": float(a.lng)} for a in addrs]
    finally:
        db.close()

@mcp.tool()
def customer_create_address(user_id: int, address: str, lat: float, lng: float, label: str = ""):
    db = next(get_db())
    try:
        addr = address_crud.create_address(db, user_id, address=address, lat=lat, lng=lng, label=label or None)
        return {"id": addr.id, "label": addr.label, "address": addr.address}
    finally:
        db.close()

@mcp.tool()
def customer_delete_address(address_id: int, user_id: int):
    db = next(get_db())
    try:
        ok = address_crud.delete_address(db, address_id, user_id)
        return {"deleted": ok}
    finally:
        db.close()

# ──────────────────────────────────────────────
#  DRIVER (16 endpoints → 16 tools)
# ──────────────────────────────────────────────

@mcp.tool()
def driver_list_available_orders(page: int = 1, size: int = 10):
    db = next(get_db())
    try:
        skip = (page - 1) * size
        items, total = delivery_crud.list_available_deliveries(db, skip=skip, limit=size)
        return {"items": [{"id": d.id, "crn": d.crn, "pickup_address": d.pickup_address, "dropoff_address": d.dropoff_address, "total_fare": float(d.total_fare)} for d in items], "total": total, "page": page, "size": size}
    finally:
        db.close()

@mcp.tool()
def driver_accept_order(order_id: int, driver_id: int):
    db = next(get_db())
    try:
        result = delivery_crud.assign_driver(db, order_id, driver_id)
        if not result:
            return {"error": "Order not available"}
        return {"id": result.id, "status": result.status.value}
    finally:
        db.close()

@mcp.tool()
def driver_reject_order(order_id: int):
    return {"message": "Order skipped"}

@mcp.tool()
def driver_arrived_at_pickup(order_id: int):
    db = next(get_db())
    try:
        result = delivery_crud.update_status(db, order_id, "arrived_pickup")
        if not result:
            return {"error": "Cannot update"}
        return {"id": result.id, "status": result.status.value}
    finally:
        db.close()

@mcp.tool()
def driver_start_trip(order_id: int):
    db = next(get_db())
    try:
        result = delivery_crud.update_status(db, order_id, "picked_up")
        if not result:
            return {"error": "Cannot update"}
        return {"id": result.id, "status": result.status.value}
    finally:
        db.close()

@mcp.tool()
def driver_complete_delivery(order_id: int, proof_url: str = ""):
    db = next(get_db())
    try:
        result = delivery_crud.complete_with_proof(db, order_id, proof_url)
        if not result:
            return {"error": "Cannot complete"}
        return {"id": result.id, "status": result.status.value}
    finally:
        db.close()

@mcp.tool()
def driver_get_assigned_orders(driver_id: int, page: int = 1, size: int = 10):
    db = next(get_db())
    try:
        skip = (page - 1) * size
        items, total = delivery_crud.list_deliveries(db, user_id=driver_id, role="driver", skip=skip, limit=size)
        return {"items": [{"id": d.id, "crn": d.crn, "status": d.status.value, "total_fare": float(d.total_fare), "pickup_address": d.pickup_address, "dropoff_address": d.dropoff_address} for d in items], "total": total, "page": page, "size": size}
    finally:
        db.close()

@mcp.tool()
def driver_get_earnings(driver_id: int, period: str = "weekly"):
    db = next(get_db())
    try:
        items, total = delivery_crud.list_deliveries(db, user_id=driver_id, role="driver", status="delivered")
        total_earned = sum(d.net_earnings for d in items)
        commission_deducted = sum(d.total_fare - d.net_earnings for d in items)
        return {"period": period, "total_deliveries": total, "total_earned": total_earned, "commission_deducted": commission_deducted}
    finally:
        db.close()

@mcp.tool()
def driver_get_wallet(user_id: int):
    db = next(get_db())
    try:
        balance = wallet_crud.get_balance(db, user_id)
        return {"user_id": user_id, "balance": balance}
    finally:
        db.close()

@mcp.tool()
def driver_withdraw_wallet(user_id: int, amount: float):
    db = next(get_db())
    try:
        wallet = wallet_crud.withdraw(db, user_id, amount)
        return {"user_id": user_id, "balance": float(wallet.balance)}
    except Exception as e:
        return {"error": str(e)}
    finally:
        db.close()

@mcp.tool()
def driver_wallet_transactions(user_id: int, skip: int = 0, limit: int = 10):
    db = next(get_db())
    try:
        txns = wallet_crud.list_transactions(db, user_id, skip=skip, limit=limit)
        return [{"id": t.id, "amount": float(t.amount), "type": t.type.value, "reference": t.reference.value if t.reference else None, "description": t.description, "created_at": str(t.created_at)} for t in txns]
    finally:
        db.close()

@mcp.tool()
def driver_get_profile(user_id: int):
    db = next(get_db())
    try:
        user = user_crud.get_user(db, user_id)
        if not user:
            return {"error": "User not found"}
        return {"id": user.id, "name": user.name, "phone": user.phone, "role": user.role.value, "is_kyc_verified": user.is_kyc_verified, "is_online": user.is_online, "is_active": user.is_active}
    finally:
        db.close()

@mcp.tool()
def driver_update_profile(user_id: int, name: str = "", phone: str = ""):
    db = next(get_db())
    try:
        kwargs = {}
        if name: kwargs["name"] = name
        if phone: kwargs["phone"] = phone
        user = user_crud.update_user(db, user_id, **kwargs)
        if not user:
            return {"error": "User not found"}
        return {"id": user.id, "name": user.name, "phone": user.phone}
    finally:
        db.close()

@mcp.tool()
def driver_go_online(user_id: int):
    db = next(get_db())
    try:
        user = user_crud.toggle_online(db, user_id, True)
        if not user:
            return {"error": "User not found"}
        return {"id": user.id, "is_online": user.is_online}
    finally:
        db.close()

@mcp.tool()
def driver_go_offline(user_id: int):
    db = next(get_db())
    try:
        user = user_crud.toggle_online(db, user_id, False)
        if not user:
            return {"error": "User not found"}
        return {"id": user.id, "is_online": user.is_online}
    finally:
        db.close()

@mcp.tool()
def driver_get_ratings(driver_id: int):
    db = next(get_db())
    try:
        stats = rating_crud.get_driver_rating_stats(db, driver_id)
        return stats
    finally:
        db.close()

# ──────────────────────────────────────────────
#  ADMIN (20 endpoints → 20 tools)
# ──────────────────────────────────────────────

@mcp.tool()
def admin_list_drivers(page: int = 1, size: int = 10):
    db = next(get_db())
    try:
        skip = (page - 1) * size
        items, total = user_crud.list_users(db, role="driver", skip=skip, limit=size)
        return {"items": [{"id": u.id, "name": u.name, "phone": u.phone, "is_kyc_verified": u.is_kyc_verified, "is_online": u.is_online, "is_active": u.is_active} for u in items], "total": total, "page": page, "size": size}
    finally:
        db.close()

@mcp.tool()
def admin_get_driver(driver_id: int):
    db = next(get_db())
    try:
        user = user_crud.get_user(db, driver_id)
        if not user or user.role.value != "driver":
            return {"error": "Driver not found"}
        return {"id": user.id, "name": user.name, "phone": user.phone, "is_kyc_verified": user.is_kyc_verified, "is_online": user.is_online, "is_active": user.is_active}
    finally:
        db.close()

@mcp.tool()
def admin_approve_driver(driver_id: int):
    db = next(get_db())
    try:
        user = user_crud.approve_kyc(db, driver_id)
        if not user:
            return {"error": "Driver not found"}
        return {"id": user.id, "is_kyc_verified": user.is_kyc_verified}
    finally:
        db.close()

@mcp.tool()
def admin_suspend_driver(driver_id: int):
    db = next(get_db())
    try:
        user = user_crud.update_user(db, driver_id, is_active=False)
        if not user:
            return {"error": "Driver not found"}
        return {"id": user.id, "is_active": user.is_active}
    finally:
        db.close()

@mcp.tool()
def admin_list_orders(status: str = "", page: int = 1, size: int = 10):
    db = next(get_db())
    try:
        skip = (page - 1) * size
        items, total = delivery_crud.list_deliveries(db, status=status or None, skip=skip, limit=size)
        return {"items": [{"id": d.id, "crn": d.crn, "status": d.status.value, "total_fare": float(d.total_fare), "pickup_address": d.pickup_address, "dropoff_address": d.dropoff_address, "customer_id": d.customer_id, "driver_id": d.driver_id} for d in items], "total": total, "page": page, "size": size}
    finally:
        db.close()

@mcp.tool()
def admin_assign_order(order_id: int, driver_id: int):
    db = next(get_db())
    try:
        result = delivery_crud.assign_driver(db, order_id, driver_id)
        if not result:
            return {"error": "Cannot assign"}
        return {"id": result.id, "status": result.status.value}
    finally:
        db.close()

@mcp.tool()
def admin_cancel_order(order_id: int):
    db = next(get_db())
    try:
        result = delivery_crud.cancel_delivery(db, order_id)
        if not result:
            return {"error": "Cannot cancel"}
        return {"id": result.id, "status": result.status.value}
    finally:
        db.close()

@mcp.tool()
def admin_refund_order(order_id: int):
    db = next(get_db())
    try:
        payment_crud.refund_payment(db, order_id)
        return {"message": "Refund processed"}
    finally:
        db.close()

@mcp.tool()
def admin_list_vehicles():
    db = next(get_db())
    try:
        vehicles = vehicle_crud.list_vehicles(db)
        return [{"id": v.id, "name": v.name, "capacity_kg": v.capacity_kg, "base_fare": float(v.base_fare), "per_km_rate": float(v.per_km_rate), "per_min_rate": float(v.per_min_rate), "min_fare": float(v.min_fare)} for v in vehicles]
    finally:
        db.close()

@mcp.tool()
def admin_update_vehicle(vehicle_id: int, base_fare: float = 0, per_km_rate: float = 0, per_min_rate: float = 0, min_fare: float = 0):
    db = next(get_db())
    try:
        kwargs = {}
        if base_fare: kwargs["base_fare"] = base_fare
        if per_km_rate: kwargs["per_km_rate"] = per_km_rate
        if per_min_rate: kwargs["per_min_rate"] = per_min_rate
        if min_fare: kwargs["min_fare"] = min_fare
        v = vehicle_crud.update_vehicle(db, vehicle_id, **kwargs)
        if not v:
            return {"error": "Vehicle not found"}
        return {"id": v.id, "name": v.name, "base_fare": float(v.base_fare), "per_km_rate": float(v.per_km_rate)}
    finally:
        db.close()

@mcp.tool()
def admin_get_surge_config():
    from core.config import settings
    return {"night_surge_start": settings.NIGHT_SURGE_START, "night_surge_end": settings.NIGHT_SURGE_END, "night_surge_multiplier": settings.NIGHT_SURGE_MULTIPLIER, "commission_percent": settings.COMMISSION_PERCENT}

@mcp.tool()
def admin_list_payouts(page: int = 1, size: int = 10):
    db = next(get_db())
    try:
        skip = (page - 1) * size
        q = (
            db.query(WalletTransaction, Wallet, User)
            .join(Wallet, WalletTransaction.wallet_id == Wallet.id)
            .join(User, Wallet.user_id == User.id)
            .filter(WalletTransaction.reference == TxnReference.WITHDRAW)
            .order_by(desc(WalletTransaction.created_at))
        )
        total = q.count()
        items = q.offset(skip).limit(size).all()
        result = []
        for txn, wallet, driver in items:
            result.append({
                "id": txn.id,
                "driver_id": wallet.user_id,
                "driver_name": driver.name,
                "driver_phone": driver.phone,
                "amount": float(txn.amount),
                "status": txn.type.value,
                "requested_at": txn.created_at.isoformat() if txn.created_at else None,
            })
        return {"items": result, "total": total, "page": page, "size": size}
    finally:
        db.close()

@mcp.tool()
def admin_list_customers(page: int = 1, size: int = 10):
    db = next(get_db())
    try:
        skip = (page - 1) * size
        items, total = user_crud.list_users(db, role="customer", skip=skip, limit=size)
        return {"items": [{"id": u.id, "name": u.name, "phone": u.phone, "is_active": u.is_active} for u in items], "total": total, "page": page, "size": size}
    finally:
        db.close()

@mcp.tool()
def admin_block_customer(customer_id: int):
    db = next(get_db())
    try:
        user = user_crud.update_user(db, customer_id, is_active=False)
        if not user:
            return {"error": "User not found"}
        return {"id": user.id, "is_active": user.is_active}
    finally:
        db.close()

@mcp.tool()
def admin_revenue_analytics():
    db = next(get_db())
    try:
        delivered = db.query(Delivery).filter(Delivery.status == "delivered").count()
        revenue = db.query(Delivery).filter(Delivery.status == "delivered").with_entities(Delivery.total_fare).all()
        total_revenue = sum(r[0] for r in revenue) if revenue else 0
        return {"total_orders": delivered, "total_revenue": round(total_revenue, 2), "currency": "NPR"}
    finally:
        db.close()

@mcp.tool()
def admin_order_analytics():
    db = next(get_db())
    try:
        total = db.query(Delivery).count()
        active = db.query(Delivery).filter(Delivery.status.in_(["pending", "assigned", "picked_up", "in_transit"])).count()
        completed = db.query(Delivery).filter(Delivery.status == "delivered").count()
        cancelled = db.query(Delivery).filter(Delivery.status == "cancelled").count()
        return {"total": total, "active": active, "completed": completed, "cancelled": cancelled}
    finally:
        db.close()

@mcp.tool()
def admin_driver_analytics():
    db = next(get_db())
    try:
        total = db.query(User).filter(User.role == UserRole.DRIVER).count()
        online = db.query(User).filter(User.role == UserRole.DRIVER, User.is_online == True).count()
        kyc_pending = db.query(User).filter(User.role == UserRole.DRIVER, User.is_kyc_verified == False).count()
        return {"total_drivers": total, "online": online, "on_trip": 0, "offline": total - online, "kyc_pending": kyc_pending}
    finally:
        db.close()

@mcp.tool()
def admin_create_promo(code: str, discount_percent: float, max_discount: float, min_trip: float = 0, valid_from: str = "", valid_until: str = "", usage_limit: int = 100):
    db = next(get_db())
    try:
        kwargs = {"code": code, "discount_percent": discount_percent, "max_discount": max_discount, "min_trip": min_trip, "usage_limit": usage_limit}
        if valid_from: kwargs["valid_from"] = valid_from
        if valid_until: kwargs["valid_until"] = valid_until
        promo = promo_crud.create_promo(db, **kwargs)
        return {"id": promo.id, "code": promo.code, "discount_percent": promo.discount_percent}
    finally:
        db.close()

@mcp.tool()
def admin_list_promos(page: int = 1, size: int = 10):
    db = next(get_db())
    try:
        skip = (page - 1) * size
        promos = promo_crud.list_promos(db, skip=skip, limit=size)
        return {"items": [{"id": p.id, "code": p.code, "discount_percent": p.discount_percent, "max_discount": p.max_discount, "min_trip": p.min_trip, "usage_limit": p.usage_limit, "is_active": p.is_active} for p in promos], "total": len(promos), "page": page, "size": size}
    finally:
        db.close()

@mcp.tool()
def admin_send_notification(title: str, body: str):
    return {"message": f"Notification queued: {title}"}

# ──────────────────────────────────────────────
#  WEB SOCKET ACTIONS (6 actions → 6 tools)
# ──────────────────────────────────────────────

@mcp.tool()
def ws_admin_stats():
    db = next(get_db())
    try:
        total_deliveries = db.query(Delivery).count()
        active_deliveries = db.query(Delivery).filter(Delivery.status.in_(["pending", "assigned", "picked_up", "in_transit"])).count()
        online_drivers = db.query(User).filter(User.role == UserRole.DRIVER, User.is_online == True).count()
        return {"total_deliveries": total_deliveries, "active_deliveries": active_deliveries, "online_drivers": online_drivers}
    finally:
        db.close()

@mcp.tool()
def ws_driver_accept(delivery_id: int, driver_id: int):
    db = next(get_db())
    try:
        delivery = delivery_crud.assign_driver(db, delivery_id, driver_id)
        if not delivery:
            return {"error": "Unable to accept delivery"}
        return {"id": delivery.id, "status": delivery.status.value}
    finally:
        db.close()

@mcp.tool()
def ws_driver_update_status(delivery_id: int, status: str):
    db = next(get_db())
    try:
        delivery = delivery_crud.update_status(db, delivery_id, status)
        if not delivery:
            return {"error": "Unable to update status"}
        return {"id": delivery.id, "status": delivery.status.value}
    finally:
        db.close()

@mcp.tool()
def ws_driver_toggle_online(driver_id: int, online: bool = True):
    db = next(get_db())
    try:
        user = user_crud.toggle_online(db, driver_id, online)
        if not user:
            return {"error": "User not found"}
        return {"is_online": user.is_online}
    finally:
        db.close()

@mcp.tool()
def ws_customer_track_delivery(delivery_id: int):
    db = next(get_db())
    try:
        d = delivery_crud.get_delivery(db, delivery_id)
        if not d:
            return {"error": "Delivery not found"}
        return {"id": d.id, "status": d.status.value, "driver_id": d.driver_id, "pickup_lat": float(d.pickup_lat) if d.pickup_lat else None, "pickup_lng": float(d.pickup_lng) if d.pickup_lng else None, "dropoff_lat": float(d.dropoff_lat) if d.dropoff_lat else None, "dropoff_lng": float(d.dropoff_lng) if d.dropoff_lng else None}
    finally:
        db.close()

@mcp.tool()
def ws_customer_fare_estimate(vehicle_type_id: int, distance_km: float = 5, duration_min: float = 10):
    db = next(get_db())
    try:
        return calculate_fare(vehicle_id=vehicle_type_id, distance_km=distance_km, duration_min=duration_min, db=db)
    finally:
        db.close()


if __name__ == "__main__":
    import uvicorn
    app = mcp.sse_app()
    uvicorn.run(app, host="0.0.0.0", port=8003)
