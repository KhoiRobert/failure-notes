from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database.connection import engine, Base
from app.config import settings

# Import all models so SQLAlchemy can create tables
from app.models import User, RootCause, Scenario, Session, UserRootCause

# Import API routes
from app.api.routes import users, root_causes, scenarios, sessions, user_root_causes

# Create tables (only in development)
if settings.ENVIRONMENT == "development":
    Base.metadata.create_all(bind=engine)

# Create FastAPI app
app = FastAPI(
    title="Failure Notes API",
    description="API for tracking mistakes and learning from them",
    version="1.0.0",
    debug=settings.DEBUG
)

# CORS middleware (for frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(users.router)
app.include_router(root_causes.router)
app.include_router(scenarios.router)
app.include_router(sessions.router)
app.include_router(user_root_causes.router)

@app.get("/")
def root():
    """Health check"""
    return {"message": "Failure Notes API is running"}

@app.get("/health")
def health():
    """Health check endpoint"""
    return {"status": "healthy"}
