"""
Test Risk Calculator Service
"""

import pytest
from app.services.risk_calculator import RiskCalculatorService
from app.models.schemas import (
    LoanApplicationRequest,
    ApplicantInfo,
    PropertyInfo,
    LoanDetails,
    GatheredData,
    PropertyType,
    Occupancy,
    LoanType,
    LoanPurpose
)


@pytest.mark.asyncio
async def test_risk_calculation():
    """Test basic risk calculation"""
    service = RiskCalculatorService()

    # Create test application
    application = LoanApplicationRequest(
        applicant=ApplicantInfo(
            full_name="Test User",
            email="test@example.com",
            phone="555-1234",
            credit_score=720,
            annual_income=85000,
            years_employed=5
        ),
        property_info=PropertyInfo(
            address="123 Test St",
            estimated_value=425000,
            property_type=PropertyType.SINGLE_FAMILY,
            occupancy=Occupancy.PRIMARY
        ),
        loan_details=LoanDetails(
            loan_amount=350000,
            loan_type=LoanType.CONVENTIONAL_30,
            loan_purpose=LoanPurpose.PURCHASE
        )
    )

    gathered_data = GatheredData(sources=[])

    # Calculate risk
    risk = await service.calculate_risk(application, gathered_data)

    # Assertions
    assert risk.risk_score >= 0
    assert risk.risk_score <= 100
    assert risk.ltv_ratio is not None
    assert risk.dti_ratio is not None
    assert risk.estimated_interest_rate is not None
    assert risk.estimated_monthly_payment is not None


# Add more tests as needed
