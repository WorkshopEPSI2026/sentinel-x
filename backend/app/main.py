from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import asyncio

from app.services import websocket as websocket_service

from app.routers.auth import router as auth_router
from app.routers.telemetry import router as telemetry_router
from app.routers.websocket import router as websocket_router
from app.mqtt_client import start_mqtt

app = FastAPI(title="Sentinel-X API")

# Start MQTT client
mqtt_client = start_mqtt()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(telemetry_router)
app.include_router(websocket_router)

@app.on_event("startup")
async def startup():
    websocket_service.event_loop = asyncio.get_running_loop()

@app.get("/")
def root():
    return {
        "message": "Welcome to Sentinel-X API",
        "service": "sentinel-backend",
    }

@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "sentinel-backend",
    }