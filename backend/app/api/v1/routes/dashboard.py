"""
Dashboard Statistics Endpoints
"""

from fastapi import APIRouter
from app.models.schemas import DashboardStats
from app.storage import get_dashboard_stats

router = APIRouter()


@router.get("/dashboard/stats", response_model=DashboardStats)
async def get_stats():
    """
    Get dashboard statistics.

    Returns:
    - Total applications count
    - Count by status (approved, pending, declined, under review)
    - Approval rate percentage
    - Average risk score
    - Average processing time
    """
    stats = get_dashboard_stats()
    return DashboardStats(**stats)
