from database import SessionLocal, engine, Base
from models import Charger
from services.cert_service import generate_charger_certificate

Base.metadata.create_all(bind=engine)

CHARGERS = [
    {"name": "Tata Power — Koramangala",  "operator": "Tata Power",   "lat": 12.9279, "lng": 77.6271},
    {"name": "Tata Power — Indiranagar",  "operator": "Tata Power",   "lat": 12.9784, "lng": 77.6408},
    {"name": "Ather Grid — HSR Layout",   "operator": "Ather Grid",   "lat": 12.9116, "lng": 77.6389},
    {"name": "Ather Grid — Whitefield",   "operator": "Ather Grid",   "lat": 12.9698, "lng": 77.7499},
    {"name": "ChargeZone — MG Road",      "operator": "ChargeZone",   "lat": 12.9757, "lng": 77.6011},
    {"name": "ChargeZone — Marathahalli", "operator": "ChargeZone",   "lat": 12.9591, "lng": 77.6972},
    {"name": "BPCL Pulse — Hebbal",       "operator": "BPCL Pulse",   "lat": 13.0353, "lng": 77.5950},
    {"name": "BPCL Pulse — Electronic City", "operator": "BPCL Pulse","lat": 12.8458, "lng": 77.6613},
    {"name": "Tata Power — Jayanagar",    "operator": "Tata Power",   "lat": 12.9250, "lng": 77.5938},
    {"name": "Ather Grid — Malleshwaram", "operator": "Ather Grid",   "lat": 13.0035, "lng": 77.5673},
]

def seed():
    db = SessionLocal()
    existing = db.query(Charger).count()
    if existing > 0:
        print(f"Database already has {existing} chargers. Skipping seed.")
        db.close()
        return

    for data in CHARGERS:
        cert_data = generate_charger_certificate(data["name"])
        charger = Charger(
            name=data["name"],
            operator=data["operator"],
            latitude=data["lat"],
            longitude=data["lng"],
            certificate_pem=cert_data["certificate_pem"],
            certificate_fingerprint=cert_data["fingerprint"],
            baseline_latency_ms=95.0,
            baseline_billing_rate=0.15,
            baseline_timing_ms=220.0,
            operator_verified=True,
            trust_score=100,
            status="VERIFIED",
        )
        db.add(charger)
        print(f"Seeded: {data['name']}")

    db.commit()
    db.close()
    print("Seeding complete.")

if __name__ == "__main__":
    seed()