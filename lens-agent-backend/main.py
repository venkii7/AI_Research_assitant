"""FastAPI application factory with lifespan hook."""
from fastapi import FastAPI
from contextlib import asynccontextmanager
from api.middleware import add_middleware
from api.routes import (
    health,
    papers,
    stream,
    query,
    exports,
    concepts,
    memory,
)
from services.redis_client import get_redis
from core.config import get_settings
import logging
import json

settings = get_settings()

# Configure structured JSON logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(message)s",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown context for the application."""
    # Startup: verify connections
    try:
        r = await get_redis()
        await r.ping()
        logging.getLogger("lens").info(
            json.dumps({"event": "startup", "status": "ok"})
        )
    except Exception as e:
        logging.getLogger("lens").error(
            json.dumps({"event": "startup", "status": "failed", "error": str(e)})
        )
        raise

    yield

    # Shutdown: clean up
    logging.getLogger("lens").info(json.dumps({"event": "shutdown"}))


app = FastAPI(
    title="Lens API",
    description="AI Research Intelligence Backend",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.environment == "development" else None,
    redoc_url=None,
)

# Register middleware
add_middleware(app)

# Register routers
app.include_router(health.router)
app.include_router(papers.router)
app.include_router(stream.router)
app.include_router(query.router)
app.include_router(exports.router)
app.include_router(concepts.router)
app.include_router(memory.router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host=settings.app_host,
        port=settings.app_port,
        log_level=settings.log_level.lower(),
    )
