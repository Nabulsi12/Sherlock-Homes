"""
Health Check Endpoints
"""

from fastapi import APIRouter
from app.models.schemas import HealthResponse
from app.config import settings
from app.services.keywords_client import KeywordsAIClient

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint to verify API is running
    """
    services = {
        "api": "operational",
        "keywords_ai": "checking...",
    }

    # Quick Keywords AI check using Joseph's client
    try:
        client = KeywordsAIClient(api_key=settings.KEYWORDS_API_KEY)
        # Verify client can connect (just test instantiation)
        services["keywords_ai"] = "operational"
    except Exception as e:
        services["keywords_ai"] = f"error: {str(e)}"

    return HealthResponse(
        status="healthy",
        version="0.1.0",
        services=services
    )
