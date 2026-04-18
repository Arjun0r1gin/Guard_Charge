import sys
import os
import time
import random

BACKEND_DIR = os.path.join(os.path.dirname(__file__), '..', 'backend')
sys.path.insert(0, BACKEND_DIR)
os.environ["DATABASE_URL"] = f"sqlite:///{os.path.join(BACKEND_DIR, 'guardcharge.db')}"

from utils.crypto import (
    generate_rsa_keypair,
    generate_self_signed_cert,
    fingerprint_from_cert_pem,
)
from database import SessionLocal
from models import Charger


def fetch_charger(charger_id: int) -> Charger:
    db = SessionLocal()
    charger = db.query(Charger).filter(Charger.id == charger_id).first()
    db.close()
    return charger


def measure_latency(label: str, target_ms: float, noise: float = 3.0) -> float:
    """Simulate measuring response latency with small random noise."""
    print(f"    [MEASURE] Sending session initiation request to {label}...")
    time.sleep(0.4)
    actual = round(target_ms + random.uniform(-noise, noise), 2)
    print(f"    [MEASURE] Response received. Latency = {actual}ms")
    return actual


def measure_billing(label: str, target_rate: float, noise: float = 0.002) -> float:
    """Simulate reading billing rate from charger MeterValues."""
    print(f"    [MEASURE] Reading billing rate from {label} MeterValues...")
    time.sleep(0.3)
    actual = round(target_rate + random.uniform(-noise, noise), 4)
    print(f"    [MEASURE] Billing rate = Rs.{actual}/min")
    return actual


def measure_timing(label: str, target_ms: float, noise: float = 2.0) -> float:
    """Simulate measuring message timing gap."""
    print(f"    [MEASURE] Measuring protocol message timing gap...")
    time.sleep(0.3)
    actual = round(target_ms + random.uniform(-noise, noise), 2)
    print(f"    [MEASURE] Message timing gap = {actual}ms")
    return actual


def get_safe_profile(charger_id: int = 1) -> dict:
    charger = fetch_charger(charger_id)
    print(f"\n  [CERT] Fetching registered certificate for {charger.name}...")
    time.sleep(0.4)
    fingerprint = fingerprint_from_cert_pem(charger.certificate_pem)
    print(f"  [CERT] Certificate found.")
    print(f"  [CERT] Fingerprint : {fingerprint[:32]}...")
    print(f"  [CERT] Expires     : 2027-04-12")
    print(f"  [CERT] Operator    : {charger.operator}")
    print()

    latency = measure_latency(charger.name, target_ms=92.0)
    billing = measure_billing(charger.name, target_rate=0.15)
    timing  = measure_timing(charger.name, target_ms=220.0)

    print(f"\n  [BASELINE] Stored profile for {charger.name}:")
    print(f"    Baseline latency  : {charger.baseline_latency_ms}ms")
    print(f"    Baseline billing  : Rs.{charger.baseline_billing_rate}/min")
    print(f"    Baseline timing   : {charger.baseline_timing_ms}ms")

    return {
        "charger_id": charger_id,
        "live_certificate_pem": charger.certificate_pem,
        "live_latency_ms": latency,
        "live_billing_rate": billing,
        "live_timing_ms": timing,
    }


def get_partial_profile(charger_id: int = 2) -> dict:
    charger = fetch_charger(charger_id)
    print(f"\n  [CERT] Fetching registered certificate for {charger.name}...")
    time.sleep(0.4)
    fingerprint = fingerprint_from_cert_pem(charger.certificate_pem)
    print(f"  [CERT] Certificate found.")
    print(f"  [CERT] Fingerprint : {fingerprint[:32]}...")
    print(f"  [CERT] Expires     : 2027-04-12")
    print(f"  [CERT] Operator    : {charger.operator}")
    print()
    print("  [WARN] Behavioural anomalies detected during handshake...")
    print()

    latency = measure_latency(charger.name, target_ms=158.0)  # 63ms over baseline
    billing = measure_billing(charger.name, target_rate=0.16)  # within 20%
    timing  = measure_timing(charger.name, target_ms=245.0)   # within threshold

    print(f"\n  [BASELINE] Stored profile for {charger.name}:")
    print(f"    Baseline latency  : {charger.baseline_latency_ms}ms  →  live: {latency}ms")
    print(f"    Baseline billing  : Rs.{charger.baseline_billing_rate}/min  →  live: Rs.{billing}/min")
    print(f"    Baseline timing   : {charger.baseline_timing_ms}ms  →  live: {timing}ms")

    return {
        "charger_id": charger_id,
        "live_certificate_pem": charger.certificate_pem,
        "live_latency_ms": latency,
        "live_billing_rate": billing,
        "live_timing_ms": timing,
    }


def get_rogue_profile(charger_id: int = 3) -> dict:
    charger = fetch_charger(charger_id)

    print(f"\n  [CERT] Fetching registered certificate for {charger.name}...")
    time.sleep(0.4)
    stored_fingerprint = fingerprint_from_cert_pem(charger.certificate_pem)
    print(f"  [CERT] Stored fingerprint  : {stored_fingerprint[:32]}...")
    print()

    print("  [CERT] Generating live certificate presented by station...")
    time.sleep(0.6)
    private_key   = generate_rsa_keypair()
    fake_cert_pem = generate_self_signed_cert(private_key, "ROGUE_STATION")
    live_fingerprint = fingerprint_from_cert_pem(fake_cert_pem)
    print(f"  [CERT] Live fingerprint    : {live_fingerprint[:32]}...")
    print()

    # Show the mismatch explicitly
    match = stored_fingerprint == live_fingerprint
    print(f"  [CERT] Fingerprint match   : {'YES' if match else 'NO — MISMATCH DETECTED'}")
    print(f"  [CERT] Stored  : {stored_fingerprint}")
    print(f"  [CERT] Live    : {live_fingerprint}")
    print()

    print("  [WARN] Certificate mismatch — Layer 1 will hard block.")
    print("  [WARN] Continuing to measure behaviour for full audit log...")
    print()

    latency = measure_latency("ROGUE STATION", target_ms=340.0)  # 245ms over baseline
    billing = measure_billing("ROGUE STATION", target_rate=0.45)  # 3x normal
    timing  = measure_timing("ROGUE STATION", target_ms=310.0)   # 90ms shift

    print(f"\n  [BASELINE] Stored profile for {charger.name}:")
    print(f"    Baseline latency  : {charger.baseline_latency_ms}ms  →  live: {latency}ms  ⚠")
    print(f"    Baseline billing  : Rs.{charger.baseline_billing_rate}/min  →  live: Rs.{billing}/min  ⚠")
    print(f"    Baseline timing   : {charger.baseline_timing_ms}ms  →  live: {timing}ms  ⚠")

    return {
        "charger_id": charger_id,
        "live_certificate_pem": fake_cert_pem,
        "live_latency_ms": latency,
        "live_billing_rate": billing,
        "live_timing_ms": timing,
    }