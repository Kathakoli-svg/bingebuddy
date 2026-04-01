from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from database import engine, Base
import models
from routes import auth, movies, user, recommend
from services.tmdb import warm_cache

Base.metadata.create_all(bind=engine)

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"

app = FastAPI(title="AI Movie Recommender", version="1.0.0")

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

app.include_router(auth.router,      prefix="/auth",      tags=["Auth"])
app.include_router(movies.router,    prefix="/movies",    tags=["Movies"])
app.include_router(user.router,      prefix="/user",      tags=["User"])
app.include_router(recommend.router, prefix="/recommend", tags=["Recommendations"])

@app.on_event("startup")
async def startup_event():
    warm_cache()

@app.get("/api/health", tags=["Health"])
async def health():
    return {"status": "ok", "message": "AI Movie Recommender API 🎬"}

app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
