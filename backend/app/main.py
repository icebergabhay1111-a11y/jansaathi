from __future__ import annotations

import logging
import time
import uuid

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse

from .config import get_settings
from .routers import account, admin, public

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
log = logging.getLogger("jansaathi")

settings = get_settings()
app = FastAPI(title="JanSaathi API", version="0.1.0",
              description="Independent citizen-information API. Not affiliated with the Government of India.",
              docs_url="/api/docs", openapi_url="/api/openapi.json")
app.add_middleware(GZipMiddleware, minimum_size=800)
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins, allow_credentials=True,
                   allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"], allow_headers=["content-type", "x-requested-with"])


@app.middleware("http")
async def security_headers_and_logging(request: Request, call_next):
    rid = uuid.uuid4().hex[:12]
    start = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception:  # never leak internals to users
        log.exception("unhandled error rid=%s path=%s", rid, request.url.path)
        # hook point for error monitoring (e.g. Sentry) — see docs/DEPLOYMENT.md
        response = JSONResponse({"detail": "Something went wrong on our side. Please try again.", "request_id": rid}, status_code=500)
    response.headers["X-Request-ID"] = rid
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["X-Frame-Options"] = "DENY"
    log.info("%s %s %s %.0fms rid=%s", request.method, request.url.path, response.status_code, (time.perf_counter() - start) * 1000, rid)
    return response


@app.exception_handler(RequestValidationError)
async def validation_handler(request: Request, exc: RequestValidationError):
    errors = [{"field": ".".join(str(p) for p in e["loc"][1:]), "message": e["msg"].removeprefix("Value error, ")} for e in exc.errors()]
    return JSONResponse({"detail": "Please check the highlighted fields.", "errors": errors}, status_code=422)


app.include_router(public.router)
app.include_router(account.router)
app.include_router(admin.router)
