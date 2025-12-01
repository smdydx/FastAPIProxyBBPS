from fastapi import APIRouter
from src.routes.base_router import create_category_router

router = create_category_router("cable_tv", "Cable TV Bill Payment")
