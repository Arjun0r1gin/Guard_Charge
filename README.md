# GuardCharge — feature/demo-automation

This branch is the hardened version of GuardCharge built for live demonstration and production readiness evaluation. Compared to `main`, it replaces HTTP with TLS-encrypted HTTPS, adds a fail-safe default-block policy, introduces sustained attack detection via a consecutive failure tracker, and ships with a full production integration stub for OCPP 2.0.

---

## What Changed From Main

### 1. All Traffic Is Now Encrypted (TLS)

In `main`, the simulator talks to the backend over plain `http://localhost:8000`. In this branch, every request goes over `https://localhost:8000` using a self-signed TLS certificate.

The backend is started with:

```bash
uvicorn main:app --ssl-keyfile key.pem --ssl-certfile cert.pem --reload
```

The simulator uses `requests` with `verify=False` since the cert is self-signed. In a real deployment you would swap in a CA-signed certificate and remove that flag. The important thing is that the transport layer is encrypted and cannot be sniffed in transit.

This matters because the detection pipeline transmits RSA certificate fingerprints and billing data. On `main`, that goes over plaintext. On this branch it does not.

---

### 2. Fail-Safe: The System Defaults to Block When It Cannot Reach the Backend

This is the biggest behavioural change in the branch. On `main`, if the backend goes down, the simulator throws an error and exits. On this branch, the system catches every possible failure and responds the same way: block charging, do not fail open.

Three cases are handled explicitly:

**Backend unreachable:**
```
[FAIL-SAFE] Backend unreachable
GuardCharge defaults to BLOCK
Charging is NOT permitted
We never fail open — safety first
```

**Backend timeout (10 seconds):**
```
[FAIL-SAFE] Backend timeout (10s)
GuardCharge defaults to BLOCK
Charging is NOT permitted
```

**Any unexpected exception:**
```
[FAIL-SAFE] Unexpected error: <detail>
[FAIL-SAFE] Defaulting to BLOCK — charging not permitted.
```

The design principle is that GuardCharge is not a system that can accidentally grant access. If the backend is offline, under attack, or responding too slowly, the answer is always no. The charger stays blocked until the system can verify it.

---

### 3. Sustained Attack Detection

The detection engine in this branch tracks how many times each charger fails in a row. The threshold is 3 consecutive failures.

If a charger fails 3 or more checks in sequence without a single verified session in between, a separate escalation alert is generated with `attack_type = "SUSTAINED_ATTACK"`. The alert is written to the database and flags the station for manual inspection.

When a clean session comes through, the counter resets to zero.

This catches a scenario that single-session detection cannot: an attacker repeatedly probing a station to find an exploit window. Each individual attempt might only score as SUSPICIOUS, but the pattern over time tells a different story.

The counter lives in memory (`_failure_counts` dict in `detection_engine.py`), so it resets on backend restart. A production version would persist this to the database.

---

### 4. Identity Privacy in OCPP Messages

The OCPP 2.0 parser in this branch includes an `Authorize` message handler that enforces identity privacy. When a charge session is authorized, the raw RFID or card token is never stored. Instead, a SHA-256 hash is computed and only the hash is kept.

```python
# Never store raw identity — hash only
hashed = hashlib.sha256(raw.encode()).hexdigest() if raw else "UNKNOWN"
```

The original token cannot be recovered from the stored value. This is not in `main`.

---

### 5. OCPP 2.0 Production Integration Stub

This branch ships a full production integration roadmap in `backend/utils/ocpp_parser.py`. It documents exactly how to replace the simulator with a real CCS2 connector without touching any detection logic.

The mapping is:

| Demo (current) | Production (ocpp_parser.py) |
|---|---|
| `ev_simulator` sends `live_certificate_pem` | `extract_tls_certificate()` from the ISO 15118 handshake |
| `ev_simulator` sends `live_latency_ms` | `extract_response_latency()` from OCPP round-trip timing |
| `ev_simulator` sends `live_billing_rate` | `parse_meter_values()` from OCPP MeterValues message |
| `ev_simulator` sends `live_timing_ms` | `extract_message_timing()` from message gap measurement |

The detection engine itself does not change at all. `run_detection()` takes the same four values regardless of whether they came from a USB simulator or a real charger. The only change in production is the data source.

---

### 6. Benchmark Tool

This branch includes `backend/benchmark.py`, which runs 20 back-to-back detection requests for each of the three scenarios and reports timing metrics.

```bash
cd backend
python benchmark.py
```

Output includes average latency, min, max, and P95 per scenario, plus an overall summary. The intent is to show that GuardCharge completes the full 2-layer detection pipeline (database read, RSA fingerprint comparison, behavioural analysis, trust score, database write) in well under 1 second per plug-in event.

---

## Running This Branch

### 1. Backend with TLS

```bash
cd backend
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
python seed_chargers.py
uvicorn main:app --ssl-keyfile key.pem --ssl-certfile cert.pem --reload
```

The `cert.pem` and `key.pem` files are included in this branch. They are self-signed and for local use only.

### 2. EV Simulator

```bash
cd ev_simulator
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
python ev_simulator.py
```

On startup, the simulator confirms the backend is reachable over HTTPS and prints the fail-safe and TLS status:

```
[FAIL-SAFE] Enabled — backend unreachable = charging blocked.
[TLS] All communications encrypted (HTTPS + WSS).
Listening for USB insertions...
```

---

## Security Summary

| Feature | main | feature/demo-automation |
|---|---|---|
| Transport encryption | None (HTTP) | TLS / HTTPS |
| Backend failure behavior | Crash / error | Default block (fail-safe) |
| Timeout behavior | Not handled | Default block after 10s |
| Consecutive failure tracking | No | Yes, escalation at 3 failures |
| Identity token storage | N/A | SHA-256 hash only, raw never stored |
| OCPP 2.0 production path | Not documented | Full stub with integration map |
| Benchmark tooling | No | Yes, 3-scenario latency benchmark |
