from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.database import engine
from app.models import models
from app.routers import auth, contacts, brands, pipeline, orders, emails, users, dashboard

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Konomocha CRM", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(contacts.router)
app.include_router(brands.router)
app.include_router(pipeline.router)
app.include_router(orders.router)
app.include_router(emails.router)
app.include_router(users.router)
app.include_router(dashboard.router)

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", include_in_schema=False)
def serve_frontend():
    return FileResponse("static/index.html")

@app.get("/health")
def health():
    return {"status": "ok"}
