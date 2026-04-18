from detection.layer1_cert import run_layer1
from detection.layer2_behaviour import run_layer2
from detection.trust_score import compute_trust_score, TrustScoreResult
from sqlalchemy.orm import Session
from models import Charger


def run_detection(
    charger_id: int,
    live_certificate_pem: str,
    live_latency_ms: float,
    live_billing_rate: float,
    live_timing_ms: float,
    db: Session,
) -> TrustScoreResult:

    # Fetch stored profile from DB
    charger: Charger = db.query(Charger).filter(Charger.id == charger_id).first()
    if not charger:
        raise ValueError(f"Charger {charger_id} not found in registry")

    # Layer 1 — certificate fingerprint check
    layer1_result = run_layer1(
        live_certificate_pem=live_certificate_pem,
        stored_fingerprint=charger.certificate_fingerprint,
    )

    # Layer 2 — behavioural fingerprinting
    layer2_result = run_layer2(
        live_latency_ms=live_latency_ms,
        live_billing_rate=live_billing_rate,
        live_timing_ms=live_timing_ms,
        baseline_latency_ms=charger.baseline_latency_ms,
        baseline_billing_rate=charger.baseline_billing_rate,
        baseline_timing_ms=charger.baseline_timing_ms,
    )

    # Trust score — combines both layers
    result = compute_trust_score(
        layer2_result=layer2_result,
        operator_verified=charger.operator_verified,
        layer1_passed=layer1_result.passed,
    )

    # Persist updated trust score back to DB
    charger.trust_score = result.score
    db.commit()

    return result