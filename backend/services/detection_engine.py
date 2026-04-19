import json
from detection.layer1_cert import run_layer1
from detection.layer2_behaviour import run_layer2
from detection.trust_score import compute_trust_score, TrustScoreResult
from sqlalchemy.orm import Session
from models import Charger, Alert, SessionLog
from utils.logger import get_logger

logger = get_logger(__name__)

# ── Consecutive failure tracker ───────────────────────────────────────
_failure_counts: dict[int, int] = {}
_ESCALATION_THRESHOLD = 3


def run_detection(
    charger_id: int,
    live_certificate_pem: str,
    live_latency_ms: float,
    live_billing_rate: float,
    live_timing_ms: float,
    db: Session,
) -> TrustScoreResult:

    charger: Charger = db.query(Charger).filter(Charger.id == charger_id).first()
    if not charger:
        raise ValueError(f"Charger {charger_id} not found in registry")

    logger.info(f"Running detection on charger {charger_id} — {charger.name}")

    # ── Layer 1 — certificate fingerprint check ───────────────────────
    layer1_result = run_layer1(
        live_certificate_pem=live_certificate_pem,
        stored_fingerprint=charger.certificate_fingerprint,
    )
    logger.info(f"Layer 1 result: passed={layer1_result.passed}")
    logger.info(f"Layer 1 detail: {layer1_result.detail}")

    # ── Layer 2 — behavioural fingerprinting ──────────────────────────
    layer2_result = run_layer2(
        live_latency_ms=live_latency_ms,
        live_billing_rate=live_billing_rate,
        live_timing_ms=live_timing_ms,
        baseline_latency_ms=charger.baseline_latency_ms,
        baseline_billing_rate=charger.baseline_billing_rate,
        baseline_timing_ms=charger.baseline_timing_ms,
    )
    logger.info(f"Layer 2 deductions: {layer2_result.deductions}")

    # ── Trust score ───────────────────────────────────────────────────
    result = compute_trust_score(
        layer2_result=layer2_result,
        operator_verified=charger.operator_verified,
        layer1_passed=layer1_result.passed,
    )
    logger.info(f"Trust score: {result.score} — {result.status}")

    # ── Persist trust score ───────────────────────────────────────────
    charger.trust_score = result.score
    charger.status = result.status

    # ── Session log — immutable audit trail ───────────────────────────
    session_log = SessionLog(
        charger_id=charger_id,
        trust_score=result.score,
        status=result.status,
        hard_blocked=result.hard_blocked,
        deductions=json.dumps(result.deductions),
        explanation=result.confidence_explanation,
    )
    db.add(session_log)

    # ── Alert on non-verified result ──────────────────────────────────
    if result.status != "VERIFIED":
        severity = "CRITICAL" if result.hard_blocked or result.score <= 19 else "WARNING"
        attack_type = "LAYER1_CERT" if result.hard_blocked else "LAYER2_BEHAVIOUR"
        alert = Alert(
            charger_id=charger_id,
            severity=severity,
            attack_type=attack_type,
            message=result.confidence_explanation,
        )
        db.add(alert)

    # ── Rate limiting — consecutive failure tracker ───────────────────
    if result.status != "VERIFIED":
        _failure_counts[charger_id] = _failure_counts.get(charger_id, 0) + 1
        count = _failure_counts[charger_id]
        logger.warning(
            f"Charger {charger_id} failure count: {count}"
        )

        if count >= _ESCALATION_THRESHOLD:
            logger.warning(
                f"ESCALATION: Charger {charger_id} — {charger.name} "
                f"has failed {count} consecutive detections. "
                f"Sustained attack suspected."
            )
            escalation_alert = Alert(
                charger_id=charger_id,
                severity="CRITICAL",
                attack_type="SUSTAINED_ATTACK",
                message=(
                    f"ESCALATION ALERT: Charger {charger_id} — {charger.name} "
                    f"has failed {count} consecutive security checks. "
                    f"Sustained attack in progress. "
                    f"Station flagged for manual inspection."
                ),
            )
            db.add(escalation_alert)
    else:
        # Reset counter on clean detection
        if charger_id in _failure_counts:
            logger.info(
                f"Charger {charger_id} passed — resetting failure count "
                f"from {_failure_counts[charger_id]} to 0"
            )
        _failure_counts[charger_id] = 0

    db.commit()
    return result