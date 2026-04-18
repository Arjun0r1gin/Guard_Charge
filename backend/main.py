from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base
from routers import chargers, alerts, detection, stream

Base.metadata.create_all(bind=engine)

app = FastAPI(title="GuardCharge API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chargers.router)
app.include_router(alerts.router)
app.include_router(detection.router)
app.include_router(stream.router)


@app.get("/")
def root():
    return {"message": "GuardCharge API running"}