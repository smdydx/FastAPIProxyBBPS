from fastapi import APIRouter
from src.routes.base_router import create_recharge_router

router = create_recharge_router("dth", "DTH Recharge & Bill Payment")
