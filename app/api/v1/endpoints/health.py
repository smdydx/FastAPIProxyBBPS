from fastapi import APIRouter
from fastapi.responses import JSONResponse
from datetime import datetime

from app.core.config import settings

router = APIRouter(tags=["Health & Configuration"])


@router.get("/health")
async def health_check():
    return JSONResponse(content={
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "timestamp": datetime.utcnow().isoformat()
    })


@router.get("/categories")
async def list_categories():
    config = settings.get_bbps_config()
    categories = list(config.get("bbps_backend_urls", {}).keys())
    
    category_info = []
    for cat in categories:
        urls = settings.get_category_urls(cat)
        endpoints = [k for k in urls.keys() if k != "base_url"]
        category_info.append({
            "category": cat,
            "display_name": cat.replace("_", " ").title(),
            "endpoints": endpoints,
            "configured": bool(urls.get("base_url"))
        })
    
    return JSONResponse(content={
        "success": True,
        "message": "Available BBPS categories",
        "data": {
            "total_categories": len(categories),
            "categories": category_info
        },
        "timestamp": datetime.utcnow().isoformat()
    })


@router.post("/config/reload")
async def reload_config():
    try:
        settings.reload_config()
        return JSONResponse(content={
            "success": True,
            "message": "Configuration reloaded successfully",
            "timestamp": datetime.utcnow().isoformat()
        })
    except Exception as e:
        return JSONResponse(
            content={
                "success": False,
                "message": "Failed to reload configuration",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            },
            status_code=500
        )
