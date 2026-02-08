from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database.connection import Base, engine
from routers import rhymes, complete, corpus, spark, style


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(engine)
    yield


app = FastAPI(title="KSL API", description="Bulgarian Chalga/Trap Lyrics Writing Tool", lifespan=lifespan)

# CORS - allow frontend dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "*"],
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


@app.get("/")
def root():
    return {"status": "ok", "app": "KSL API", "version": "1.0.0"}
