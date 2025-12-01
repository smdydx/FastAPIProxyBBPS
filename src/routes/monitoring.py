from fastapi import APIRouter
from typing import Optional

from src.services.proxy_forwarder import forward_to_bbps
from src.routes.base_router import normalize_response
from src.models.responses import BBPSResponse

router = APIRouter(prefix="/monitoring", tags=["Monitoring"])


@router.get("/health", response_model=BBPSResponse)
async def health_check() -> BBPSResponse:
    """Basic health check endpoint."""
    response_data, status_code = await forward_to_bbps(
        category="monitoring",
        endpoint_key="health",
        method="GET"
    )
    return normalize_response(response_data, status_code)


@router.get("/health/detailed", response_model=BBPSResponse)
async def detailed_health_check() -> BBPSResponse:
    """Detailed health check with dependency status (DB, Cache)."""
    response_data, status_code = await forward_to_bbps(
        category="monitoring",
        endpoint_key="health_detailed",
        method="GET"
    )
    return normalize_response(response_data, status_code)


@router.get("/health/ready", response_model=BBPSResponse)
async def readiness_check() -> BBPSResponse:
    """Kubernetes readiness probe."""
    response_data, status_code = await forward_to_bbps(
        category="monitoring",
        endpoint_key="health_ready",
        method="GET"
    )
    return normalize_response(response_data, status_code)


@router.get("/health/live", response_model=BBPSResponse)
async def liveness_check() -> BBPSResponse:
    """Kubernetes liveness probe."""
    response_data, status_code = await forward_to_bbps(
        category="monitoring",
        endpoint_key="health_live",
        method="GET"
    )
    return normalize_response(response_data, status_code)


@router.get("/metrics", response_model=BBPSResponse)
async def prometheus_metrics() -> BBPSResponse:
    """Prometheus metrics endpoint."""
    response_data, status_code = await forward_to_bbps(
        category="monitoring",
        endpoint_key="metrics",
        method="GET"
    )
    return normalize_response(response_data, status_code)


@router.get("/stats/system", response_model=BBPSResponse)
async def system_stats() -> BBPSResponse:
    """System resource usage statistics (CPU, Memory, Disk)."""
    response_data, status_code = await forward_to_bbps(
        category="monitoring",
        endpoint_key="stats_system",
        method="GET"
    )
    return normalize_response(response_data, status_code)


@router.get("/stats/application", response_model=BBPSResponse)
async def application_stats() -> BBPSResponse:
    """Application-specific statistics (DB counts)."""
    response_data, status_code = await forward_to_bbps(
        category="monitoring",
        endpoint_key="stats_application",
        method="GET"
    )
    return normalize_response(response_data, status_code)


@router.get("/stats/cache", response_model=BBPSResponse)
async def cache_stats() -> BBPSResponse:
    """Redis cache statistics."""
    response_data, status_code = await forward_to_bbps(
        category="monitoring",
        endpoint_key="stats_cache",
        method="GET"
    )
    return normalize_response(response_data, status_code)
