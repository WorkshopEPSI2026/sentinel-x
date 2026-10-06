from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers.auth import router as auth_router


app = FastAPI(title="Sentinel-X API")

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