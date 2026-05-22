import time
import traceback
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from app.database import engine
from app.models import models
from app.routers import auth, contacts, brands, pipeline, orders, emails, users, dashboard, reports, tasks, trash
from app.routers.audit import router as audit_router
from app.logger import app_logger

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Konomocha CRM", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request timing middleware ──────────────────────────────────────────────────
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration = time.time() - start
    # Log slow requests (>2s) and all errors
    if duration > 2.0 or response.status_code >= 500:
        app_logger.warning(
            f"{request.method} {request.url.path} "
            f"status={response.status_code} duration={duration:.2f}s"
        )
    return response


# ── Global unhandled exception handler ────────────────────────────────────────
@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    app_logger.error(
        f"Unhandled exception: {request.method} {request.url.path}\n"
        f"{traceback.format_exc()}"
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal error occurred. It has been logged."},
    )


# ── Client-side error reporting ────────────────────────────────────────────────
class ClientError(BaseModel):
    message: str
    source: str = ""
    lineno: int = 0
    colno: int = 0
    stack: str = ""
    url: str = ""


@app.post("/api/log-client-error", include_in_schema=False)
async def log_client_error(request: Request, error: ClientError):
    app_logger.error(
        f"[FRONTEND] {error.message} | "
        f"url={error.url} source={error.source}:{error.lineno}:{error.colno}\n"
        f"{error.stack}"
    )
    return {"ok": True}


from app.routers.admin_stages import router as admin_stages_router

app.include_router(auth.router)
app.include_router(contacts.router)
app.include_router(brands.router)
app.include_router(pipeline.router)
app.include_router(orders.router)
app.include_router(emails.router)
app.include_router(users.router)
app.include_router(dashboard.router)
app.include_router(reports.router)
app.include_router(tasks.router)
app.include_router(admin_stages_router, prefix="/api")
app.include_router(trash.router)
app.include_router(audit_router)
from app.routers.timeline import router as timeline_router
from app.routers.search   import router as search_router
app.include_router(timeline_router)
app.include_router(search_router)

app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/", include_in_schema=False)
def serve_frontend():
    return FileResponse("static/index.html")


@app.get("/health")
def health():
    return {"status": "ok"}
