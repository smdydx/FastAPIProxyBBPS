"""API v1 Endpoints"""
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

__all__ = [
    "health",
    "monitoring",
    "mdm",
    "billfetch",
    "billpayment",
    "billers",
    "complaints",
    "banks",
    "admin",
    "auth",
    "bbps",
    "biller_management"
]
