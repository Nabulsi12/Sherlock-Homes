"""
In-Memory Storage for Loan Applications

For hackathon purposes - in production, replace with a database.
"""

from typing import Dict, List, Optional
from datetime import datetime
from app.models.schemas import LoanApplicationResponse

# In-memory storage
_applications: Dict[str, dict] = {}

# Sample data for demo
SAMPLE_APPLICATIONS = [
    {
        "application_id": "LN-2024-08472",
        "status": "approved",
        "borrower_name": "James Morrison",
        "loan_type": "30-Year Fixed Rate Conventional",
        "loan_amount": 425000,
        "property_value": 530000,
        "ltv_ratio": 80.2,
        "risk_score": 18,
        "credit_score": 780,
        "annual_income": 145000,
        "dti_ratio": 28.5,
        "submitted_at": "2024-01-30T10:30:00Z",
        "processed_at": "2024-01-30T10:30:09Z",
    },
    {
        "application_id": "LN-2024-08471",
        "status": "pending",
        "borrower_name": "Sarah Chen",
        "loan_type": "15-Year Fixed Rate Conventional",
        "loan_amount": 315000,
        "property_value": 420000,
        "ltv_ratio": 75.0,
        "risk_score": 32,
        "credit_score": 745,
        "annual_income": 118000,
        "dti_ratio": 31.2,
        "submitted_at": "2024-01-30T09:15:00Z",
        "processed_at": None,
    },
    {
        "application_id": "LN-2024-08470",
        "status": "review",
        "borrower_name": "Michael Torres",
        "loan_type": "30-Year Fixed Rate FHA",
        "loan_amount": 285000,
        "property_value": 299000,
        "ltv_ratio": 95.3,
        "risk_score": 58,
        "credit_score": 680,
        "annual_income": 72000,
        "dti_ratio": 42.1,
        "submitted_at": "2024-01-29T16:45:00Z",
        "processed_at": "2024-01-29T16:45:12Z",
    },
    {
        "application_id": "LN-2024-08469",
        "status": "declined",
        "borrower_name": "Robert Blake",
        "loan_type": "30-Year Fixed Rate Conventional",
        "loan_amount": 520000,
        "property_value": 545000,
        "ltv_ratio": 95.4,
        "risk_score": 84,
        "credit_score": 620,
        "annual_income": 85000,
        "dti_ratio": 52.3,
        "submitted_at": "2024-01-29T14:20:00Z",
        "processed_at": "2024-01-29T14:20:15Z",
    },
]

# Initialize with sample data
for app in SAMPLE_APPLICATIONS:
    _applications[app["application_id"]] = app


def save_application(application_id: str, data: dict) -> None:
    """Save an application to storage"""
    _applications[application_id] = data


def get_application(application_id: str) -> Optional[dict]:
    """Retrieve an application by ID"""
    return _applications.get(application_id)


def list_applications(
    skip: int = 0,
    limit: int = 10,
    status: Optional[str] = None
) -> tuple[List[dict], int]:
    """List applications with optional filtering"""
    apps = list(_applications.values())

    # Filter by status if provided
    if status:
        apps = [a for a in apps if a.get("status") == status]

    total = len(apps)

    # Sort by submitted_at descending (newest first)
    apps.sort(key=lambda x: x.get("submitted_at", ""), reverse=True)

    # Paginate
    apps = apps[skip:skip + limit]

    return apps, total


def update_application_status(application_id: str, new_status: str) -> Optional[dict]:
    """Update an application's status"""
    if application_id in _applications:
        _applications[application_id]["status"] = new_status
        _applications[application_id]["updated_at"] = datetime.utcnow().isoformat()
        return _applications[application_id]
    return None


def get_dashboard_stats() -> dict:
    """Calculate dashboard statistics"""
    apps = list(_applications.values())
    total = len(apps)

    if total == 0:
        return {
            "total_applications": 0,
            "approved": 0,
            "pending": 0,
            "declined": 0,
            "under_review": 0,
            "approval_rate": 0.0,
            "average_risk_score": 0.0,
            "average_processing_time": 0.0,
        }

    approved = sum(1 for a in apps if a.get("status") == "approved")
    pending = sum(1 for a in apps if a.get("status") == "pending")
    declined = sum(1 for a in apps if a.get("status") == "declined")
    review = sum(1 for a in apps if a.get("status") == "review")

    # Calculate averages
    risk_scores = [a.get("risk_score", 0) for a in apps if a.get("risk_score")]
    avg_risk = sum(risk_scores) / len(risk_scores) if risk_scores else 0

    # Approval rate (approved / (approved + declined))
    decided = approved + declined
    approval_rate = (approved / decided * 100) if decided > 0 else 0

    return {
        "total_applications": total,
        "approved": approved,
        "pending": pending,
        "declined": declined,
        "under_review": review,
        "approval_rate": round(approval_rate, 1),
        "average_risk_score": round(avg_risk, 1),
        "average_processing_time": 9.5,  # Simulated for demo
    }
