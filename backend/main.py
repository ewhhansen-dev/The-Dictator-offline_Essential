import logging
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.api.routes import router
from backend.config import load_settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

settings = load_settings()

app = FastAPI(
    title="The Dictator",
    description="Local-first voice dictation API",
    version="0.0.1"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost",
        "http://localhost:8000",
        "http://localhost:8765",
        "http://127.0.0.1",
        "http://127.0.0.1:8000",
        "http://127.0.0.1:8765",
        "null",  # Allow file:// protocol for opening frontend/index.html directly
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")

@app.get("/")
async def root():
    return {"message": "The Dictator is running. Docs at /docs"}

def cli():
    import uvicorn
    dev_mode = os.getenv("DEV_MODE", "false").lower() == "true"
    uvicorn.run(
        "backend.main:app",
        host=settings.server.host,
        port=settings.server.port,
        reload=dev_mode
    )

if __name__ == "__main__":
    cli()
