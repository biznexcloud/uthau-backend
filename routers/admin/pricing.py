from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from core.database import get_db
from core.deps import require_role
from core.config import settings
from models.user import User as UserModel
from schemas.vehicle import VehicleTypeResponse, VehicleTypeUpdate
from schemas.common import MessageResponse
from crud import vehicle as vehicle_crud

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/pricing/vehicles", response_model=list[VehicleTypeResponse])
def list_vehicles(db: Session = Depends(get_db), current_user: UserModel = Depends(require_role("admin"))):
    return vehicle_crud.list_vehicles(db)


@router.put("/pricing/vehicles/{vehicle_id}", response_model=VehicleTypeResponse)
def update_vehicle(vehicle_id: int, body: VehicleTypeUpdate, db: Session = Depends(get_db), current_user: UserModel = Depends(require_role("admin"))):
    result = vehicle_crud.update_vehicle(db, vehicle_id, **body.model_dump(exclude_none=True))
    if not result:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    return result


@router.get("/pricing/surge")
def get_surge_config(current_user: UserModel = Depends(require_role("admin"))):
    return {
        "night_surge_start": settings.NIGHT_SURGE_START,
        "night_surge_end": settings.NIGHT_SURGE_END,
        "night_surge_multiplier": settings.NIGHT_SURGE_MULTIPLIER,
        "commission_percent": settings.COMMISSION_PERCENT,
    }
