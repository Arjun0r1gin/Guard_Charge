"""
OCPP 2.0 message parser — production integration stub.

In the demo, detection_engine.py receives data from ev_simulator.py
via POST /detection/run.

In production, this module receives real OCPP 2.0 messages from a
CCS2 connector and extracts the same data fields that the simulator
currently provides manually.

The detection functions in layer1_cert.py and layer2_behaviour.py
are completely unchanged — only the data source changes.
This is a one-file swap from demo to production.

Production integration map:
────────────────────────────────────────────────────────────
DEMO (current)                PRODUCTION (this module)
──────────────────────────    ──────────────────────────────
ev_simulator sends            OCPP client receives message
  live_certificate_pem    →   parse_boot_notification() +
                              ISO 15118 TLS cert extraction
  live_latency_ms         →   extract_response_latency()
  live_billing_rate       →   parse_meter_values()
  live_timing_ms          →   extract_message_timing()

detection_engine.run_detection() is IDENTICAL in both cases.
Zero detection logic changes required.
────────────────────────────────────────────────────────────
"""

import hashlib
from datetime import datetime, timezone


def parse_boot_notification(message: dict) -> dict:
    """
    Extracts charger identity from OCPP 2.0 BootNotification message.

    In production:
    - certificate_pem comes from the ISO 15118 TLS handshake
      embedded in the OCPP connection setup
    - charger_id maps to the serialNumber field

    OCPP 2.0 BootNotification structure:
    {
        "chargingStation": {
            "serialNumber": "GC-BLR-001",
            "model": "FastCharge-50",
            "vendorName": "Tata Power",
            "firmwareVersion": "2.1.0",
            "modem": { "iccid": "...", "imsi": "..." }
        },
        "reason": "PowerUp"
    }
    """
    station = message.get("chargingStation", {})
    return {
        "serial_number": station.get("serialNumber", "UNKNOWN"),
        "vendor":        station.get("vendorName", "UNKNOWN"),
        "model":         station.get("model", "UNKNOWN"),
        "firmware":      station.get("firmwareVersion", "UNKNOWN"),
        "reason":        message.get("reason", "UNKNOWN"),
    }


def parse_meter_values(message: dict) -> dict:
    """
    Extracts billing rate from OCPP 2.0 MeterValues message.

    In production:
    - billing_rate is derived from Energy.Active.Import.Register
    - timestamp gives us the message timing gap

    OCPP 2.0 MeterValues structure:
    {
        "connectorId": 1,
        "transactionId": "tx-001",
        "meterValue": [{
            "timestamp": "2026-04-17T12:00:00Z",
            "sampledValue": [{
                "value": "0.150",
                "measurand": "Energy.Active.Import.Register",
                "unit": "kWh",
                "context": "Sample.Periodic"
            }]
        }]
    }
    """
    meter_values = message.get("meterValue", [{}])
    sampled = meter_values[0].get("sampledValue", [{}]) if meter_values else [{}]

    energy_reading = next(
        (v for v in sampled
         if v.get("measurand") == "Energy.Active.Import.Register"),
        {}
    )

    return {
        "billing_rate":   float(energy_reading.get("value", 0.0)),
        "unit":           energy_reading.get("unit", "kWh"),
        "timestamp":      meter_values[0].get(
                            "timestamp",
                            datetime.now(timezone.utc).isoformat()
                          ),
        "connector_id":   message.get("connectorId", 1),
        "transaction_id": message.get("transactionId", "UNKNOWN"),
    }


def parse_authorize_request(message: dict) -> dict:
    """
    Extracts identity token from OCPP 2.0 Authorize request.

    Identity privacy enforcement:
    GuardCharge never logs the raw idToken.
    Only a SHA256 hash is stored — the original cannot be recovered.

    OCPP 2.0 Authorize structure:
    {
        "idToken": {
            "idToken": "ABC12345",
            "type": "ISO14443"
        }
    }
    """
    id_token = message.get("idToken", {})
    raw = id_token.get("idToken", "")

    # Never store raw identity — hash only
    hashed = hashlib.sha256(raw.encode()).hexdigest() if raw else "UNKNOWN"

    return {
        "id_token_type": id_token.get("type", "UNKNOWN"),
        "id_token_hash": hashed,
        # raw token deliberately not returned
    }


def extract_response_latency(
    request_time: float,
    response_time: float
) -> float:
    """
    Computes response latency in milliseconds.

    In production: wraps the actual OCPP message round-trip timing.
    In demo: ev_simulator.py provides this value directly.

    Args:
        request_time:  time.perf_counter() at request send
        response_time: time.perf_counter() at response receive

    Returns:
        Latency in milliseconds, rounded to 2 decimal places.
    """
    return round((response_time - request_time) * 1000, 2)


def extract_message_timing(
    first_message_time: float,
    second_message_time: float
) -> float:
    """
    Computes gap between sequential protocol messages in milliseconds.

    In production: measures the gap between BootNotification and
    the first MeterValues message during session setup.
    In demo: ev_simulator.py provides this value directly.

    Args:
        first_message_time:  time.perf_counter() of first message
        second_message_time: time.perf_counter() of second message

    Returns:
        Timing gap in milliseconds, rounded to 2 decimal places.
    """
    return round((second_message_time - first_message_time) * 1000, 2)


def extract_tls_certificate(tls_connection) -> str:
    """
    Extracts PEM certificate from an active TLS connection.

    In production: called during ISO 15118 TLS handshake setup.
    In demo: ev_simulator.py provides certificate_pem directly.

    Args:
        tls_connection: ssl.SSLSocket or equivalent TLS connection object

    Returns:
        Certificate in PEM format as a string.
    """
    import ssl
    der_cert = tls_connection.getpeercert(binary_form=True)
    pem_cert = ssl.DER_cert_to_PEM_cert(der_cert)
    return pem_cert