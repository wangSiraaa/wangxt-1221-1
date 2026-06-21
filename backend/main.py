from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.routers import auth, monitor, anomaly, instruction, discharge, disposal, retest

app = FastAPI(title=settings.APP_NAME, version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(monitor.router)
app.include_router(anomaly.router)
app.include_router(instruction.router)
app.include_router(discharge.router)
app.include_router(disposal.router)
app.include_router(retest.router)


@app.get("/api/health")
async def health_check():
    return {"status": "ok", "app": settings.APP_NAME}


@app.get("/")
async def root():
    return {
        "app": settings.APP_NAME,
        "version": "1.0.0",
        "docs": "/docs",
        "api_health": "/api/health"
    }
