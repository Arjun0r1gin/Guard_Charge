from dataclasses import dataclass

# Thresholds from the report
LATENCY_THRESHOLD_MS = 50       # deviation from baseline → -35 pts
BILLING_RATE_THRESHOLD = 0.20   # >20% above stored profile → -35 pts
TIMING_THRESHOLD_MS = 30        # message timing shift → -20 pts


@dataclass
class BehaviouralResult:
    latency_anomaly: bool
    billing_anomaly: bool
    timing_anomaly: bool
    latency_ms: float
    billing_rate: float
    message_timing_ms: float
    deductions: int
    details: dict


def check_latency(live_ms: float, baseline_ms: float) -> tuple[bool, str]:
    deviation = abs(live_ms - baseline_ms)
    anomaly = deviation > LATENCY_THRESHOLD_MS
    return anomaly, f"live={live_ms}ms baseline={baseline_ms}ms deviation={deviation}ms"


def check_billing_rate(live_rate: float, stored_rate: float) -> tuple[bool, str]:
    if stored_rate == 0:
        return True, "stored billing rate is zero — cannot verify"
    pct_above = (live_rate - stored_rate) / stored_rate
    anomaly = pct_above > BILLING_RATE_THRESHOLD
    return anomaly, f"live=₹{live_rate}/min stored=₹{stored_rate}/min overage={pct_above:.1%}"


def check_message_timing(live_ms: float, baseline_ms: float) -> tuple[bool, str]:
    deviation = abs(live_ms - baseline_ms)
    anomaly = deviation > TIMING_THRESHOLD_MS
    return anomaly, f"live={live_ms}ms baseline={baseline_ms}ms deviation={deviation}ms"


def run_layer2(
    live_latency_ms: float,
    live_billing_rate: float,
    live_timing_ms: float,
    baseline_latency_ms: float,
    baseline_billing_rate: float,
    baseline_timing_ms: float,
) -> BehaviouralResult:
    latency_anomaly, latency_detail = check_latency(live_latency_ms, baseline_latency_ms)
    billing_anomaly, billing_detail = check_billing_rate(live_billing_rate, baseline_billing_rate)
    timing_anomaly, timing_detail = check_message_timing(live_timing_ms, baseline_timing_ms)

    deductions = 0
    if latency_anomaly:
        deductions += 35
    if billing_anomaly:
        deductions += 35
    if timing_anomaly:
        deductions += 20

    return BehaviouralResult(
        latency_anomaly=latency_anomaly,
        billing_anomaly=billing_anomaly,
        timing_anomaly=timing_anomaly,
        latency_ms=live_latency_ms,
        billing_rate=live_billing_rate,
        message_timing_ms=live_timing_ms,
        deductions=deductions,
        details={
            "latency": latency_detail,
            "billing": billing_detail,
            "timing": timing_detail,
        },
    )