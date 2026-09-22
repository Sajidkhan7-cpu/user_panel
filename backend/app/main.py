"""
main.py
FastAPI application entry point. Wires up CORS, routers, and (optionally)
serves the static frontend directly so the whole project can run with
a single `uvicorn app.main:app` command.
"""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.routers import chatbot, auth, student, faq, course, admin

app = FastAPI(title=settings.APP_NAME, debug=settings.DEBUG)

# ---------------------------------------------------------------------------
# CORS - allow the frontend (served separately or via Live Server) to call
# the API. Tighten allow_origins in production.
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
app.include_router(auth.router)
app.include_router(chatbot.router)
app.include_router(student.router)
app.include_router(faq.router)
app.include_router(course.router)
app.include_router(admin.router)


@app.get("/api/health", tags=["Health"])
def health_check():
    return {"status": "ok", "app": settings.APP_NAME}


# ---------------------------------------------------------------------------
# Optionally serve the frontend as static files so the project can run
# without a separate web server (visit http://localhost:8000/ )
# ---------------------------------------------------------------------------
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "frontend")
if os.path.isdir(FRONTEND_DIR):
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
