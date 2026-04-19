# GuardCharge

GuardCharge is a security system for EV charging stations. When an EV is plugged in, it runs a multi-layer detection pipeline to verify the charger before any charging begins. The goal is to catch rogue or tampered stations that could steal billing data or perform man-in-the-middle attacks.

This repo contains the full stack: a FastAPI backend, a Windows USB-triggered simulator, and two frontend interfaces for monitoring.

---

## How It Works

Every plug-in event triggers a 6-step pipeline:

1. A TLS handshake is initiated with the charging station
2. The station's certificate is retrieved and its fingerprint is checked against the registered one in the database
3. Live behavioural data is collected: response latency, billing rate, and protocol timing
4. All values are compared against the stored baseline profile for that charger
5. A trust score is calculated from 0 to 100 based on how many checks pass
6. A final verdict is issued: Verified, Suspicious, Blocked, or Hard Block

If the certificate fingerprint does not match, the charger is immediately hard-blocked regardless of the other checks.

---

## Project Structure

```
Guard_Charge/
|
|-- backend/                  # FastAPI backend
|   |-- main.py               # App entry point, router registration
|   |-- models.py             # SQLAlchemy models (Charger, Session, Alert)
|   |-- schemas.py            # Pydantic request/response schemas
|   |-- database.py           # SQLite DB connection
|   |-- seed_chargers.py      # Seeds charger data and generates RSA certs
|   |-- detection/            # Detection pipeline logic and trust scoring
|   |-- routers/              # API routes: /chargers, /alerts, /detection, /stream
|   |-- services/             # Business logic layer
|   |-- utils/                # Crypto utilities (RSA keygen, cert signing, fingerprinting)
|   |-- certs/                # Stored certificates
|
|-- ev_simulator/             # Windows USB-triggered EV simulator
|   |-- ev_simulator.py       # Main simulator, listens for USB insertion events
|   |-- attack_modes.py       # Profiles: safe, partial anomaly, rogue
|   |-- session_manager.py    # Tracks simulation sessions
|   |-- dashboard.html        # Live security monitoring dashboard (SSE)
|
|-- frontend/                 # Charger map interface
|   |-- index.html            # Interactive Leaflet.js map with charger directory
|   |-- src/                  # React components (ChargerMap, DetectionPanel, etc.)
|
|-- docker-compose.yml
```

---

## Stack

**Backend**
- Python, FastAPI, SQLAlchemy, SQLite
- RSA certificate generation with `cryptography`
- Server-Sent Events (SSE) for real-time log streaming

**EV Simulator**
- Python with `pywin32` for Windows USB device detection
- Simulates 3 scenarios: Safe, Partial Anomaly, Rogue

**Frontend**
- Charger Map: Vanilla HTML/CSS/JS, Leaflet.js, CartoDB dark tiles
- Live Dashboard: Vanilla HTML/CSS/JS, SSE via `EventSource`

---

## Getting Started

### 1. Backend

```bash
cd backend
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
python seed_chargers.py
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`.

### 2. EV Simulator

```bash
cd ev_simulator
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
python ev_simulator.py
```

Once running, physically insert a USB drive to trigger a plug-in simulation. Each insertion cycles through the three attack scenarios in order:

- Insertion 1: Safe charger (Trust Score: 100, Verified)
- Insertion 2: Partial anomaly (Trust Score: 65, Warning)
- Insertion 3: Rogue charger with certificate mismatch (Trust Score: 20, Hard Block)

### 3. Frontend

Open `frontend/index.html` in a browser to see the charger map. Click any charger and use "Connect to Charger" to open the live dashboard at `ev_simulator/dashboard.html`.

The dashboard streams events from the backend in real time and displays the trust score, detection breakdown, and session stats.

---

## Detection Scenarios

| Scenario | Certificate | Latency | Billing | Timing | Result |
|---|---|---|---|---|---|
| Safe | Match | Normal (~92ms) | Normal | Normal | VERIFIED |
| Partial Anomaly | Match | High (~158ms) | Slightly high | Normal | SUSPICIOUS |
| Rogue | Mismatch | Very high (~340ms) | 3x normal | Shifted | HARD BLOCK |

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/chargers/` | List all registered chargers |
| POST | `/detection/run` | Run the detection pipeline |
| GET | `/stream/events` | SSE stream for live dashboard |
| POST | `/stream/log` | Push a log line to the SSE stream |
| GET | `/alerts/` | List generated alerts |

---

## Notes

- The simulator only runs on Windows because USB device change events use the Win32 API (`WM_DEVICECHANGE`).
- The database is auto-seeded on simulator startup if no chargers exist.
- Certificates are RSA-2048, self-signed, and generated fresh during seeding.
