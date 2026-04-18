from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text
from sqlalchemy.sql import func
from database import Base

class Charger(Base):
    __tablename__ = "chargers"

    id                      = Column(Integer, primary_key=True, index=True)
    name                    = Column(String, nullable=False)
    operator                = Column(String, nullable=False)
    latitude                = Column(Float, nullable=False)
    longitude               = Column(Float, nullable=False)
    certificate_fingerprint = Column(String, nullable=False)
    certificate_pem         = Column(Text, nullable=False)
    baseline_latency_ms     = Column(Float, default=95.0)
    baseline_billing_rate   = Column(Float, default=0.15)
    baseline_timing_ms      = Column(Float, default=220.0)
    operator_verified       = Column(Boolean, default=True)
    trust_score             = Column(Integer, default=100)
    status                  = Column(String, default="VERIFIED")
    created_at              = Column(DateTime(timezone=True), server_default=func.now())
    updated_at              = Column(DateTime(timezone=True), onupdate=func.now())


class Alert(Base):
    __tablename__ = "alerts"

    id          = Column(Integer, primary_key=True, index=True)
    charger_id  = Column(Integer, nullable=False)
    severity    = Column(String, nullable=False)   # CRITICAL / WARNING / INFO
    attack_type = Column(String, nullable=False)   # LAYER1_CERT / LAYER2_BEHAVIOUR
    message     = Column(Text, nullable=False)
    created_at  = Column(DateTime(timezone=True), server_default=func.now())


class SessionLog(Base):
    __tablename__ = "session_logs"

    id            = Column(Integer, primary_key=True, index=True)
    charger_id    = Column(Integer, nullable=False)
    trust_score   = Column(Integer, nullable=False)
    status        = Column(String, nullable=False)
    hard_blocked  = Column(Boolean, default=False)
    deductions    = Column(Text, nullable=True)   # JSON string
    explanation   = Column(Text, nullable=True)
    created_at    = Column(DateTime(timezone=True), server_default=func.now())