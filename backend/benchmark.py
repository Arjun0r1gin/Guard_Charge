"""
GuardCharge detection pipeline benchmark.
Measures response time of /detection/run across 3 scenarios.

Usage:
    cd backend
    python benchmark.py

Requirements:
    uvicorn main:app running on https://localhost:8000
"""

import sys
import time
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

ENDPOINT = "https://localhost:8000/detection/run"
REQUESTS_PER_SCENARIO = 20


def get_charger_cert(charger_id: int) -> str:
    from database import SessionLocal
    from models import Charger
    db = SessionLocal()
    charger = db.query(Charger).filter(Charger.id == charger_id).first()
    cert = charger.certificate_pem
    db.close()
    return cert


def run_scenario_benchmark(label: str, payload: dict) -> dict:
    print(f"\n{'=' * 55}")
    print(f"  Scenario: {label}")
    print(f"{'=' * 55}")

    times  = []
    scores = []
    statuses = []

    for i in range(REQUESTS_PER_SCENARIO):
        start = time.perf_counter()
        try:
            r = requests.post(ENDPOINT, json=payload, timeout=10, verify=False)
            r.raise_for_status()
            elapsed = (time.perf_counter() - start) * 1000
            data    = r.json()
            score   = data.get("score", 0)
            status  = data.get("status", "UNKNOWN")
        except Exception as e:
            print(f"  Request {i+1:2d}: ERROR — {e}")
            continue

        times.append(elapsed)
        scores.append(score)
        statuses.append(status)
        print(f"  Request {i+1:2d}: {elapsed:6.1f}ms  "
              f"score={score:3d}  {status}")

    if not times:
        print("  No successful requests.")
        return {}

    avg = sum(times) / len(times)
    p95 = sorted(times)[int(len(times) * 0.95)]

    print(f"\n  ── Results ──────────────────────────────────────")
    print(f"  Successful requests : {len(times)}/{REQUESTS_PER_SCENARIO}")
    print(f"  Average latency     : {avg:.1f}ms")
    print(f"  Min latency         : {min(times):.1f}ms")
    print(f"  Max latency         : {max(times):.1f}ms")
    print(f"  P95 latency         : {p95:.1f}ms")
    print(f"  Score range         : {min(scores)}–{max(scores)}")
    print(f"  Status              : {set(statuses)}")

    return {
        "label":   label,
        "avg":     avg,
        "min":     min(times),
        "max":     max(times),
        "p95":     p95,
        "success": len(times),
    }


def main():
    print("\n" + "=" * 55)
    print("  GuardCharge — Detection Pipeline Benchmark")
    print("=" * 55)
    print(f"  Endpoint  : {ENDPOINT}")
    print(f"  Requests  : {REQUESTS_PER_SCENARIO} per scenario")
    print(f"  Scenarios : 3 (VERIFIED / SUSPICIOUS / CONFIRMED_ROGUE)")

    # Check backend
    try:
        requests.get(
            "https://localhost:8000/chargers/",
            timeout=5,
            verify=False
        )
        print("\n  Backend connected. Starting benchmark...\n")
    except requests.exceptions.ConnectionError:
        print("\n  ERROR: Backend not running.")
        print("  Run: uvicorn main:app --ssl-keyfile key.pem "
              "--ssl-certfile cert.pem --reload")
        sys.exit(1)

    results = []

    # ── Scenario 1 — Clean charger (VERIFIED) ────────────────────────
    cert1 = get_charger_cert(1)
    r1 = run_scenario_benchmark(
        label="Clean charger — Layer 1 + Layer 2 pass (VERIFIED)",
        payload={
            "charger_id": 1,
            "live_certificate_pem": cert1,
            "live_latency_ms": 92.0,
            "live_billing_rate": 0.15,
            "live_timing_ms": 218.0,
        }
    )
    results.append(r1)

    # ── Scenario 2 — Partial anomaly (SUSPICIOUS) ────────────────────
    cert2 = get_charger_cert(2)
    r2 = run_scenario_benchmark(
        label="Partial anomaly — latency spike (SUSPICIOUS)",
        payload={
            "charger_id": 2,
            "live_certificate_pem": cert2,
            "live_latency_ms": 158.0,
            "live_billing_rate": 0.16,
            "live_timing_ms": 245.0,
        }
    )
    results.append(r2)

    # ── Scenario 3 — Rogue charger (CONFIRMED_ROGUE) ─────────────────
    from utils.crypto import generate_rsa_keypair, generate_self_signed_cert
    private_key = generate_rsa_keypair()
    fake_cert   = generate_self_signed_cert(private_key, "ROGUE_STATION")

    r3 = run_scenario_benchmark(
        label="Rogue charger — cert mismatch hard block (CONFIRMED_ROGUE)",
        payload={
            "charger_id": 3,
            "live_certificate_pem": fake_cert,
            "live_latency_ms": 340.0,
            "live_billing_rate": 0.45,
            "live_timing_ms": 310.0,
        }
    )
    results.append(r3)

    # ── Summary ───────────────────────────────────────────────────────
    print(f"\n{'=' * 55}")
    print("  BENCHMARK SUMMARY")
    print(f"{'=' * 55}")
    print(f"  {'Scenario':<45} {'Avg':>6}  {'P95':>6}")
    print(f"  {'-'*45} {'------':>6}  {'------':>6}")
    for r in results:
        if r:
            label_short = r['label'][:44]
            print(f"  {label_short:<45} {r['avg']:>5.1f}ms  {r['p95']:>5.1f}ms")

    all_avgs = [r['avg'] for r in results if r]
    if all_avgs:
        overall = sum(all_avgs) / len(all_avgs)
        print(f"\n  Overall average latency : {overall:.1f}ms")
        print(f"  All scenarios           : sub-{max(r['max'] for r in results if r):.0f}ms")
        print()
        print("  JUDGE TALKING POINT:")
        print(f"  GuardCharge completes full 2-layer detection in")
        print(f"  {overall:.0f}ms average — well under 1 second,")
        print(f"  including database read, RSA fingerprint comparison,")
        print(f"  behavioural analysis, trust score computation,")
        print(f"  and database write.")

    print(f"\n{'=' * 55}")
    print("  Benchmark complete.")
    print(f"{'=' * 55}\n")


if __name__ == "__main__":
    main()