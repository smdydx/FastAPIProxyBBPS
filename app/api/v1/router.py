from fastapi import APIRouter

from app.api.v1.endpoints import health, monitoring, mdm, billfetch, billpayment, billers, complaints, banks

api_router = APIRouter()

api_router.include_router(health.router)
api_router.include_router(monitoring.router)
api_router.include_router(mdm.router)
api_router.include_router(billfetch.router)
api_router.include_router(billpayment.router)
api_router.include_router(billers.router)
api_router.include_router(complaints.router)
api_router.include_router(banks.router)
