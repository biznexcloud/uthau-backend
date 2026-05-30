from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from core.config import settings
from core.database import Base, engine, SessionLocal
from core.rate_limit import RateLimitMiddleware, AuthRateLimitMiddleware
from routers import auth, ws
from routers.customer import delivery as customer_delivery, wallet as customer_wallet, profile as customer_profile
from routers.driver import delivery as driver_delivery, earnings as driver_earnings, wallet as driver_wallet, profile as driver_profile
from routers.admin import fleet as admin_fleet, orders as admin_orders, pricing as admin_pricing, payouts as admin_payouts, customers as admin_customers, analytics as admin_analytics, promos as admin_promos, support as admin_support

import os

app = FastAPI(title="Uthau Nepal", version="1.0.0", docs_url="/docs")

if os.environ.get("TESTING") != "1":
    app.add_middleware(AuthRateLimitMiddleware, max_requests=5, window_seconds=300)
    app.add_middleware(RateLimitMiddleware, max_requests=100, window_seconds=60)

origins = settings.CORS_ORIGINS
if settings.is_production and "*" in origins:
    import logging
    logging.warning("CORS_ORIGINS contains '*' in production! This is a security risk.")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials="*" not in origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

if settings.ENVIRONMENT == "development":
    Base.metadata.create_all(bind=engine)


@app.get("/health")
def health_check():
    try:
        from sqlalchemy import text
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    return JSONResponse(content={
        "status": "ok",
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT,
        "database": db_status,
    })


app.include_router(auth.router)

app.include_router(customer_delivery.router)
app.include_router(customer_wallet.router)
app.include_router(customer_profile.router)

app.include_router(driver_delivery.router)
app.include_router(driver_earnings.router)
app.include_router(driver_wallet.router)
app.include_router(driver_profile.router)

app.include_router(admin_fleet.router)
app.include_router(admin_orders.router)
app.include_router(admin_pricing.router)
app.include_router(admin_payouts.router)
app.include_router(admin_customers.router)
app.include_router(admin_analytics.router)
app.include_router(admin_promos.router)
app.include_router(admin_support.router)

app.include_router(ws.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
