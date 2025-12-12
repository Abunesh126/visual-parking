from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.database import Base, engine
from app.routers import entry, exit, health, occupancy, slots

app = FastAPI(
    title="Parking Management System",
    description="A comprehensive parking management system with real-time occupancy tracking",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    """Create database tables on startup."""
    Base.metadata.create_all(bind=engine)

# Include routers
app.include_router(health.router)
app.include_router(entry.router)
app.include_router(exit.router)
app.include_router(slots.router)
app.include_router(occupancy.router)

@app.get("/")
def root():
    """Root endpoint with API information."""
    return {
        "message": "Parking Management System API",
        "version": "1.0.0",
        "documentation": "/docs",
        "health_check": "/health"
    }
