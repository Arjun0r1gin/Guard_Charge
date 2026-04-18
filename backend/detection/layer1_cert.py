from dataclasses import dataclass
from utils.crypto import fingerprint_from_cert_pem


@dataclass
class Layer1Result:
    passed: bool
    live_fingerprint: str
    stored_fingerprint: str
    detail: str


def run_layer1(live_certificate_pem: str, stored_fingerprint: str) -> Layer1Result:
    live_fingerprint = fingerprint_from_cert_pem(live_certificate_pem)
    passed = live_fingerprint == stored_fingerprint

    if passed:
        detail = "Certificate fingerprint matches registered fingerprint. Layer 1 passed."
    else:
        detail = (
            f"MISMATCH — live fingerprint: {live_fingerprint[:16]}... "
            f"stored: {stored_fingerprint[:16]}... "
            f"Certificate has been tampered or replaced."
        )

    return Layer1Result(
        passed=passed,
        live_fingerprint=live_fingerprint,
        stored_fingerprint=stored_fingerprint,
        detail=detail,
    )