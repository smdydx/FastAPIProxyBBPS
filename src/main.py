from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from datetime import datetime
import time

from src.config.settings import settings
from src.utils.logger import logger

from src.routes.health import router as health_router
from src.routes.monitoring import router as monitoring_router
from src.routes.mdm import router as mdm_router
from src.routes.billfetch import router as billfetch_router
from src.routes.billpayment import router as billpayment_router
from src.routes.billers import router as billers_router
from src.routes.complaints import router as complaints_router
from src.routes.banks import router as banks_router
from src.routes.admin_router import router as admin_router
from src.routes.auth_router import router as auth_router
from src.routes.biller_management import router as biller_management_router

app = FastAPI(
    title=settings.APP_NAME,
    description="""
    ## BBPS Proxy System
    
    A production-ready FastAPI proxy system for Bharat Bill Payment System (BBPS) operations.
    This proxy forwards requests to the actual BBPS backend while hiding real URLs from clients.
    
    ### API Categories:
    
    #### Core BBPS Operations
    - **Billers**: List, search, and get biller details
    - **Bill Fetch**: Fetch bill details for consumers
    - **Bill Payment**: Process bill payments
    - **Complaints**: Register and track complaints
    
    #### Master Data Management
    - **MDM**: Fetch and sync biller MDM data from BBPS
    
    #### Infrastructure
    - **Monitoring**: Health checks, metrics, and system stats
    - **Banks**: Bank and IFSC code lookup
    
    ### Features:
    - Config-based URL mapping for easy backend URL updates
    - Comprehensive logging and error handling
    - Request/Response validation with Pydantic
    - Retry mechanism with exponential backoff
    - Normalized response format
    """,
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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


app.include_router(health_router, prefix="/api/v1")
app.include_router(monitoring_router, prefix="/api/v1")
app.include_router(mdm_router, prefix="/api/v1")
app.include_router(billfetch_router, prefix="/api/v1")
app.include_router(billpayment_router, prefix="/api/v1")
app.include_router(billers_router, prefix="/api/v1")
app.include_router(complaints_router, prefix="/api/v1")
app.include_router(banks_router, prefix="/api/v1")
app.include_router(admin_router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1")
app.include_router(biller_management_router, prefix="/api/v1")


@app.get("/")
async def root():
    return JSONResponse(content={
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "documentation": "/docs",
        "health_check": "/api/v1/health",
        "endpoints": {
            "monitoring": "/api/v1/monitoring",
            "mdm": "/api/v1/mdm",
            "billers": "/api/v1/billers",
            "billfetch": "/api/v1/billfetch",
            "billpayment": "/api/v1/billpayment",
            "complaints": "/api/v1/complaints",
            "banks": "/api/v1/banks",
            "admin": "/api/v1/admin",
            "auth": "/api/v1/auth",
            "biller_management": "/api/v1/biller-management"
        },
        "timestamp": datetime.utcnow().isoformat()
    })


if __name__ == "__main__":
    import uvicorn
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
