"""
Report Generation Endpoints
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from typing import Optional
from datetime import datetime
from app.storage import get_application, get_dashboard_stats

router = APIRouter()


@router.get("/reports/{application_id}")
async def get_report(
    application_id: str,
    format: Optional[str] = "json"
):
    """
    Generate and download report for a loan application

    Supported formats:
    - json: JSON response with full report
    - pdf: PDF document (future feature)
    - html: HTML report (future feature)
    """
    if format not in ["json", "pdf", "html"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid format. Supported: json, pdf, html"
        )

    # Get application data
    app = get_application(application_id)
    if not app:
        raise HTTPException(
            status_code=404,
            detail=f"Application {application_id} not found"
        )

    # Build report
    report = {
        "report_id": f"RPT-{application_id}",
        "generated_at": datetime.utcnow().isoformat(),
        "format": format,
        "application": {
            "id": app["application_id"],
            "status": app["status"],
            "borrower": app["borrower_name"],
            "loan_type": app["loan_type"],
            "loan_amount": app["loan_amount"],
            "property_value": app["property_value"],
        },
        "risk_assessment": {
            "risk_score": app.get("risk_score"),
            "risk_level": "low" if app.get("risk_score", 100) <= 35 else "medium" if app.get("risk_score", 100) <= 60 else "high",
            "ltv_ratio": app.get("ltv_ratio"),
            "dti_ratio": app.get("dti_ratio"),
            "credit_score": app.get("credit_score"),
        },
        "recommendation": _get_recommendation(app),
        "timeline": {
            "submitted": app.get("submitted_at"),
            "processed": app.get("processed_at"),
        }
    }

    # Include full response if available
    if "full_response" in app:
        report["detailed_analysis"] = app["full_response"]

    if format == "pdf":
        # For hackathon - return JSON with note about PDF
        report["note"] = "PDF generation available in production version"

    if format == "html":
        # For hackathon - return JSON with note about HTML
        report["note"] = "HTML report available in production version"

    return JSONResponse(report)


def _get_recommendation(app: dict) -> dict:
    """Generate recommendation based on application data"""
    risk_score = app.get("risk_score", 50)
    status = app.get("status", "pending")

    if status == "approved" or risk_score <= 35:
        return {
            "decision": "APPROVE",
            "confidence": "high",
            "notes": "Application meets all underwriting criteria"
        }
    elif status == "review" or risk_score <= 60:
        return {
            "decision": "REVIEW",
            "confidence": "medium",
            "notes": "Application requires additional review or documentation"
        }
    else:
        return {
            "decision": "DECLINE",
            "confidence": "high",
            "notes": "Application does not meet minimum underwriting standards"
        }


@router.get("/reports/{application_id}/export")
async def export_report(application_id: str):
    """
    Export report as downloadable file
    """
    # Get application data
    app = get_application(application_id)
    if not app:
        raise HTTPException(
            status_code=404,
            detail=f"Application {application_id} not found"
        )

    # For hackathon - return JSON export
    return JSONResponse({
        "message": "Report export",
        "application_id": application_id,
        "export_format": "json",
        "data": app
    })


@router.get("/reports/summary/all")
async def get_summary_report():
    """
    Get summary report of all applications
    """
    stats = get_dashboard_stats()

    return {
        "report_type": "summary",
        "generated_at": datetime.utcnow().isoformat(),
        "statistics": stats,
        "insights": {
            "approval_trend": "stable",
            "average_loan_amount": 386250,  # Demo value
            "top_loan_types": [
                "30-Year Fixed Conventional",
                "15-Year Fixed Conventional",
                "30-Year Fixed FHA"
            ],
            "risk_distribution": {
                "low": stats.get("approved", 0),
                "medium": stats.get("under_review", 0),
                "high": stats.get("declined", 0)
            }
        }
    }
