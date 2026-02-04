"""
API Router Aggregator
"""

from fastapi import APIRouter
from app.api.v1.routes import (
    health,
    loan_applications,
    reports,
    quick_assessment,
    dashboard,
    documents,
    # auth,  # Not implemented yet
    # settings  # Not implemented yet
)

api_router = APIRouter()

# Include all route modules

# Authentication (no prefix, uses /auth/...)
# api_router.include_router(
#     auth.router,
#     tags=["authentication"]
# )

# Health check
api_router.include_router(
    health.router,
    tags=["health"]
)

# Loan applications
api_router.include_router(
    loan_applications.router,
    tags=["loan-applications"]
)

# Quick assessment
api_router.include_router(
    quick_assessment.router,
    tags=["quick-assessment"]
)

# Dashboard
api_router.include_router(
    dashboard.router,
    tags=["dashboard"]
)

# Documents
api_router.include_router(
    documents.router,
    tags=["documents"]
)

# Reports
api_router.include_router(
    reports.router,
    tags=["reports"]
)

# Settings
# api_router.include_router(
#     settings.router,
#     tags=["settings"]
# )
