from fastapi import APIRouter

from app.api.v1.endpoints import (
    health, 
    monitoring, 
    mdm, 
    billfetch, 
    billpayment, 
    billers, 
    complaints, 
    banks,
    admin,
    auth,
    bbps,
    biller_management
)

api_router = APIRouter()

api_router.include_router(health.router, tags=["Health"])
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(admin.router, prefix="/admin", tags=["Admin"])
api_router.include_router(monitoring.router, prefix="/monitoring", tags=["Monitoring"])
api_router.include_router(mdm.router, prefix="/mdm", tags=["MDM"])
api_router.include_router(billfetch.router, prefix="/billfetch", tags=["Bill Fetch"])
api_router.include_router(billpayment.router, prefix="/billpayment", tags=["Bill Payment"])
api_router.include_router(billers.router, prefix="/billers", tags=["Billers"])
api_router.include_router(complaints.router, prefix="/complaints", tags=["Complaints"])
api_router.include_router(banks.router, prefix="/banks", tags=["Banks"])
api_router.include_router(bbps.router, prefix="/bbps", tags=["BBPS Operations"])
api_router.include_router(biller_management.router, prefix="/management", tags=["Biller Management"])
