from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from models import Alert
from schemas import AlertOut
from typing import List

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("/", response_model=List[AlertOut])
def get_all_alerts(db: Session = Depends(get_db)):
    return db.query(Alert).order_by(Alert.created_at.desc()).all()


@router.get("/{charger_id}", response_model=List[AlertOut])
def get_alerts_for_charger(charger_id: int, db: Session = Depends(get_db)):
    return (
        db.query(Alert)
        .filter(Alert.charger_id == charger_id)
        .order_by(Alert.created_at.desc())
        .all()
    )