import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from database.connection import Base, engine
from routers import rhymes, complete, corpus, spark, style, scraped, genius, study, freestyle


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(engine)
    yield


app = FastAPI(title="KSL API", description="Bulgarian Chalga/Trap Lyrics Writing Tool", lifespan=lifespan)

# CORS - allow frontend dev server and production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all routers
app.include_router(rhymes.router)
app.include_router(complete.router)
app.include_router(corpus.router)
app.include_router(spark.router)
app.include_router(style.router)
app.include_router(scraped.router)
app.include_router(genius.router)
app.include_router(study.router)
app.include_router(freestyle.router)


# Serve frontend static files in production
STATIC_DIR = Path(__file__).parent / "ksl-web" / "dist"

if STATIC_DIR.exists():
    # Serve static assets (JS, CSS, etc.)
    app.mount("/assets", StaticFiles(directory=STATIC_DIR / "assets"), name="assets")

    @app.get("/")
    async def serve_spa():
        return FileResponse(STATIC_DIR / "index.html")

    # Catch-all route for SPA - must be last
    @app.get("/{path:path}")
    async def serve_spa_routes(path: str):
        # Don't intercept API routes
        if path.startswith("api/"):
            return {"error": "Not found"}
        # Serve index.html for all other routes (SPA routing)
        file_path = STATIC_DIR / path
        if file_path.exists() and file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(STATIC_DIR / "index.html")
else:
    @app.get("/")
    def root():
        return {"status": "ok", "app": "KSL API", "version": "1.0.0"}
