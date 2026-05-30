"""Запуск: python -m src.service"""

import os

import uvicorn

from src.utils.config import load_config

if __name__ == "__main__":
    cfg = load_config()
    host = os.getenv("SERVICE_HOST", cfg["service"]["host"])
    port = int(os.getenv("SERVICE_PORT", cfg["service"]["port"]))
    uvicorn.run(
        "src.service.api:app",
        host=host,
        port=port,
        reload=False,
    )
