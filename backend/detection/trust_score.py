from dataclasses import dataclass
from detection.layer2_behaviour import BehaviouralResult

# Deduction weights (from report Section 4)
DEDUCTION_LATENCY = 35
DEDUCTION_BILLING = 35
DEDUCTION_TIMING = 20
DEDUCTION_OPERATOR = 10


@dataclass
class TrustScoreResult:
    score: int                  # 0–100
    status: str                 # VERIFIED / SUSPICIOUS / LIKELY_ROGUE / CONFIRMED_ROGUE
    action: str                 # what the app should do
    hard_blocked: bool          # True if Layer 1 killed it
    deductions: dict            # breakdown of what was deducted and why
    confidence_explanation: str # human-readable string for the confidence explainer popup


_STATUS_MAP = [
    (80, "VERIFIED",       "permit_charging"),
    (50, "SUSPICIOUS",     "alert_and_warn"),
    (20, "LIKELY_ROGUE",   "block_charging"),
    (0,  "CONFIRMED_ROGUE","hard_block"),
]


def _status_from_score(score: int) -> tuple[str, str]:
    for threshold, status, action in _STATUS_MAP:
        if score >= threshold:
            return status, action
    return "CONFIRMED_ROGUE", "hard_block"


def compute_trust_score(
    layer2_result: BehaviouralResult,
    operator_verified: bool,
    layer1_passed: bool,
) -> TrustScoreResult:

    # Layer 1 hard block — score goes to 0 immediately, no further checks
    if not layer1_passed:
        return TrustScoreResult(
            score=0,
            status="CONFIRMED_ROGUE",
            action="hard_block",
            hard_blocked=True,
            deductions={"layer1_cert_mismatch": 100},
            confidence_explanation=(
                "Layer 1 FAILED: certificate fingerprint does not match the registered "
                "fingerprint. This station's certificate has been tampered or replaced. "
                "Charging is hard-blocked."
            ),
        )

    # Start at 100, apply Layer 2 deductions
    score = 100
    deductions = {}

    if layer2_result.latency_anomaly:
        score -= DEDUCTION_LATENCY
        deductions["latency_anomaly"] = {
            "points": DEDUCTION_LATENCY,
            "detail": layer2_result.details["latency"],
        }

    if layer2_result.billing_anomaly:
        score -= DEDUCTION_BILLING
        deductions["billing_anomaly"] = {
            "points": DEDUCTION_BILLING,
            "detail": layer2_result.details["billing"],
        }

    if layer2_result.timing_anomaly:
        score -= DEDUCTION_TIMING
        deductions["timing_anomaly"] = {
            "points": DEDUCTION_TIMING,
            "detail": layer2_result.details["timing"],
        }

    if not operator_verified:
        score -= DEDUCTION_OPERATOR
        deductions["operator_verification_failure"] = {
            "points": DEDUCTION_OPERATOR,
            "detail": "Operator identity could not be confirmed",
        }

    score = max(0, score)
    status, action = _status_from_score(score)

    # Build the confidence explainer text
    if not deductions:
        explanation = "All Layer 2 checks passed. Certificate valid, behaviour matches baseline."
    else:
        lines = [f"Trust score: {score}/100. Anomalies detected:"]
        for key, val in deductions.items():
            lines.append(f"  • {key}: −{val['points']} pts — {val['detail']}")
        explanation = "\n".join(lines)

    return TrustScoreResult(
        score=score,
        status=status,
        action=action,
        hard_blocked=False,
        deductions=deductions,
        confidence_explanation=explanation,
    )