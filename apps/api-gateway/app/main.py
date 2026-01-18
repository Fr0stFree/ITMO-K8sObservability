from contextlib import asynccontextmanager
from prometheus_client import make_asgi_app
from fastapi import FastAPI
import uvicorn

from config import logger, LOGGING_CONFIG
from metrics import REQUESTS_TOTAL, REQUEST_LATENCY, IN_PROGRESS_REQUESTS


@asynccontextmanager
async def lifespan(app: FastAPI):
    metrics_app = make_asgi_app()
    app.mount("/metrics", metrics_app)
    logger.info("Mounting /metrics endpoint...")
    yield
    logger.info("Application shutdown...")


app = FastAPI(lifespan=lifespan)


@app.get("/")
async def root():
    operation = "root"
    REQUESTS_TOTAL.labels(operation=operation).inc()
    with REQUEST_LATENCY.labels(operation=operation).time():
        IN_PROGRESS_REQUESTS.labels(operation=operation).inc()
        try:
            return {"message": "Hello, World!"}
        finally:
            IN_PROGRESS_REQUESTS.labels(operation=operation).dec()


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, log_config=LOGGING_CONFIG, log_level="info")
