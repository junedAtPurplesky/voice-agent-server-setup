"""Main STT Service Application"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from .config import config_manager
from .http_endpoints import router as http_router
from .websocket_endpoints import router as websocket_router

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger.info("🚀 Starting STT Service...")
    config = config_manager.get_config()
    logger.info(f"Configuration loaded: {config.model.name} on {config.model.device}")
    logger.info("✅ STT Service started successfully")
    
    yield
    
    logger.info("🛑 Shutting down STT Service...")
    logger.info("✅ STT Service shutdown complete")


app = FastAPI(
    title="STT Service - Production Ready",
    description="Production-ready Speech-to-Text service with dynamic configuration",
    version="2.0.0",
    root_path="/stt",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(http_router, tags=["HTTP Endpoints"])
app.include_router(websocket_router, tags=["WebSocket Endpoints"])


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        workers=1,
        log_level="info"
    )

