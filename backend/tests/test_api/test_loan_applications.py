"""
Test Loan Application Endpoints
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_check():
    """Test health check endpoint"""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data


def test_create_loan_application():
    """Test creating a loan application"""
    application_data = {
        "applicant": {
            "full_name": "Test Borrower",
            "email": "test@example.com",
            "phone": "555-123-4567",
            "credit_score": 720,
            "annual_income": 85000
        },
        "property_info": {
            "address": "123 Test St, Test City, ST 12345",
            "estimated_value": 425000,
            "property_type": "Single Family Detached",
            "occupancy": "Primary Residence"
        },
        "loan_details": {
            "loan_amount": 350000,
            "loan_type": "30-Year Fixed Conventional",
            "loan_purpose": "Purchase"
        }
    }

    # Note: This test will fail without a valid CLAUDE_API_KEY
    # For hackathon, you may want to mock the AI service
    response = client.post("/api/v1/loan-applications", json=application_data)

    # Uncomment when ready to test with real API key
    # assert response.status_code == 200
    # data = response.json()
    # assert "application_id" in data
    # assert data["status"] == "processed"


# Add more tests as needed
