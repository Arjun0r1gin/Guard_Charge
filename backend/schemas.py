from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class ChargerBase(BaseModel):
    name: str
    operator: str
    latitude: float
    longitude: float

class ChargerOut(ChargerBase):
    id: int
    trust_score: int
    status: str
    operator_verified: bool
    created_at: datetime

    class Config:
        from_attributes = True

class AlertOut(BaseModel):
    id: int
    charger_id: int
    severity: str
    attack_type: str
    message: str
    created_at: datetime

    class Config:
        from_attributes = True

class SessionLogOut(BaseModel):
    id: int
    charger_id: int
    trust_score: int
    status: str
    hard_blocked: bool
    explanation: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

class DetectionRequest(BaseModel):
    charger_id: int
    live_certificate_pem: str
    live_latency_ms: float
    live_billing_rate: float
    live_timing_ms: float

class DetectionResponse(BaseModel):
    charger_id: int
    score: int
    status: str
    action: str
    hard_blocked: bool
    confidence_explanation: str