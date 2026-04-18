import os
from utils.crypto import (
    generate_rsa_keypair,
    generate_self_signed_cert,
    fingerprint_from_cert_pem,
    get_private_key_pem,
)
from config import settings


def generate_charger_certificate(charger_name: str) -> dict:
    private_key = generate_rsa_keypair()
    cert_pem = generate_self_signed_cert(private_key, common_name=charger_name)
    fingerprint = fingerprint_from_cert_pem(cert_pem)
    private_key_pem = get_private_key_pem(private_key)

    # Save private key to certs/ directory
    os.makedirs(settings.CERTS_DIR, exist_ok=True)
    safe_name = charger_name.replace(" ", "_").lower()
    key_path = os.path.join(settings.CERTS_DIR, f"{safe_name}.key.pem")
    with open(key_path, "w") as f:
        f.write(private_key_pem)

    return {
        "certificate_pem": cert_pem,
        "fingerprint": fingerprint,
        "private_key_path": key_path,
    }