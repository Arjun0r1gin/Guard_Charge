from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import Charger
from schemas import ChargerOut
from typing import List

router = APIRouter(prefix="/chargers", tags=["chargers"])


@router.get("/", response_model=List[ChargerOut])
def get_all_chargers(db: Session = Depends(get_db)):
    return db.query(Charger).all()


@router.get("/{charger_id}", response_model=ChargerOut)
def get_charger(charger_id: int, db: Session = Depends(get_db)):
    charger = db.query(Charger).filter(Charger.id == charger_id).first()
    if not charger:
        raise HTTPException(status_code=404, detail="Charger not found")
    return chargery
    