from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from datetime import datetime
import time

from app.core.config import settings
from app.core.logging import logger
from app.core.database import init_db, close_db, get_engine
from app.core.cache import close_redis
from app.api.v1.router import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    
    if settings.DATABASE_URL:
        try:
            await init_db()
            logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
    else:
        logger.warning("DATABASE_URL not set - database features disabled")
    
    yield
    
    logger.info("Shutting down application...")
    await close_db()
    await close_redis()
    logger.info("Application shutdown complete")


app = FastAPI(
    title=settings.APP_NAME,
    description="""
    ## BBPS Proxy System
    
    A production-ready FastAPI proxy system for Bharat Bill Payment System (BBPS) operations.
    This system provides comprehensive BBPS integration with authentication, database operations,
    caching, and full API proxy capabilities.
    
    ### API Categories:
    
    #### Authentication & Admin
    - **Auth**: OAuth2 token-based authentication
    - **Admin**: Client management, dashboard, audit logs
    
    #### Core BBPS Operations
    - **Billers**: List, search, and get biller details
    - **Bill Fetch**: Fetch bill details for consumers
    - **Bill Payment**: Process bill payments
    - **Complaints**: Register and track complaints
    - **BBPS**: Advanced BBPS operations (transactions, recharge, plans)
    
    #### Master Data Management
    - **MDM**: Fetch and sync biller MDM data from BBPS
    - **Biller Management**: CRUD operations, CSV upload
    
    #### Infrastructure
    - **Monitoring**: Health checks, metrics, and system stats
    - **Banks**: Bank and IFSC code lookup
    
    ### Features:
    - OAuth2/JWT authentication with API key support
    - Async PostgreSQL database with SQLAlchemy
    - Redis caching layer
    - Config-based URL mapping for easy backend URL updates
    - Comprehensive logging and error handling
    - Request/Response validation with Pydantic
    - Retry mechanism with exponential backoff
    - Rate limiting
    - Normalized response format
    """,
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    
    response = await call_next(request)
    
    duration = (time.time() - start_time) * 1000
    logger.info(
        f"Request: {request.method} {request.url.path} - "
        f"Status: {response.status_code} - "
        f"Duration: {duration:.2f}ms"
    )
    
    return response


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "Internal server error",
            "error": str(exc) if settings.DEBUG else "An unexpected error occurred",
            "timestamp": datetime.utcnow().isoformat()
        }
    )


app.include_router(api_router, prefix="/api/v1")


@app.get("/")
async def root():
    db_status = "connected" if get_engine() else "not configured"
    
    return JSONResponse(content={
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "database": db_status,
        "documentation": "/docs",
        "health_check": "/api/v1/health",
        "endpoints": {
            "auth": "/api/v1/auth",
            "admin": "/api/v1/admin",
            "monitoring": "/api/v1/monitoring",
            "mdm": "/api/v1/mdm",
            "billers": "/api/v1/billers",
            "billfetch": "/api/v1/billfetch",
            "billpayment": "/api/v1/billpayment",
            "complaints": "/api/v1/complaints",
            "banks": "/api/v1/banks",
            "bbps": "/api/v1/bbps",
            "management": "/api/v1/management"
        },
        "timestamp": datetime.utcnow().isoformat()
    })


if __name__ == "__main__":
    import uvicorn
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
