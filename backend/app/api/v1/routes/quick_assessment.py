"""
Quick Pre-Qualification Assessment Endpoint
"""

from fastapi import APIRouter
from app.models.schemas import (
    QuickAssessmentRequest,
    QuickAssessmentResponse,
    RiskLevel
)

router = APIRouter()


def calculate_risk_score(
    credit_score: int,
    dti_ratio: float,
    ltv_ratio: float
) -> tuple[int, RiskLevel]:
    """
    Calculate risk score based on key factors.

    Risk score: 0-100 (lower is better)
    """
    score = 0

    # Credit score component (0-35 points)
    if credit_score >= 760:
        score += 0
    elif credit_score >= 720:
        score += 10
    elif credit_score >= 680:
        score += 20
    elif credit_score >= 640:
        score += 28
    else:
        score += 35

    # DTI ratio component (0-35 points)
    if dti_ratio <= 28:
        score += 0
    elif dti_ratio <= 36:
        score += 10
    elif dti_ratio <= 43:
        score += 20
    elif dti_ratio <= 50:
        score += 28
    else:
        score += 35

    # LTV ratio component (0-30 points)
    if ltv_ratio <= 80:
        score += 0
    elif ltv_ratio <= 90:
        score += 10
    elif ltv_ratio <= 95:
        score += 20
    else:
        score += 30

    # Determine risk level
    if score <= 30:
        level = RiskLevel.LOW
    elif score <= 60:
        level = RiskLevel.MEDIUM
    else:
        level = RiskLevel.HIGH

    return score, level


def estimate_interest_rate(credit_score: int, ltv_ratio: float) -> float:
    """Estimate interest rate based on credit score and LTV"""
    # Base rate
    base_rate = 6.5

    # Credit score adjustments
    if credit_score >= 760:
        base_rate -= 0.5
    elif credit_score >= 720:
        base_rate -= 0.25
    elif credit_score >= 680:
        pass  # No adjustment
    elif credit_score >= 640:
        base_rate += 0.5
    else:
        base_rate += 1.0

    # LTV adjustments
    if ltv_ratio > 95:
        base_rate += 0.5
    elif ltv_ratio > 90:
        base_rate += 0.25

    return round(base_rate, 3)


def calculate_monthly_payment(
    loan_amount: float,
    annual_rate: float,
    years: int = 30
) -> float:
    """Calculate monthly mortgage payment"""
    monthly_rate = annual_rate / 100 / 12
    num_payments = years * 12

    if monthly_rate == 0:
        return loan_amount / num_payments

    payment = loan_amount * (
        monthly_rate * (1 + monthly_rate) ** num_payments
    ) / (
        (1 + monthly_rate) ** num_payments - 1
    )

    return round(payment, 2)


@router.post("/quick-assessment", response_model=QuickAssessmentResponse)
async def run_quick_assessment(request: QuickAssessmentRequest):
    """
    Run a quick pre-qualification assessment.

    This provides an instant preliminary assessment based on:
    - Credit score
    - Debt-to-income ratio (DTI)
    - Loan-to-value ratio (LTV)

    Returns a risk score, recommendation, and estimated rates.
    """
    # Calculate ratios
    monthly_income = request.annual_income / 12
    monthly_debts = request.monthly_debts or 0

    # Estimate mortgage payment for DTI calculation
    estimated_rate = estimate_interest_rate(
        request.credit_score,
        (request.loan_amount / request.property_value) * 100
    )
    estimated_payment = calculate_monthly_payment(
        request.loan_amount,
        estimated_rate
    )

    # Add property taxes and insurance estimate (~1.5% of property value annually)
    monthly_taxes_insurance = (request.property_value * 0.015) / 12

    total_housing_payment = estimated_payment + monthly_taxes_insurance
    total_monthly_debts = monthly_debts + total_housing_payment

    dti_ratio = (total_monthly_debts / monthly_income) * 100
    ltv_ratio = (request.loan_amount / request.property_value) * 100

    # Calculate risk score
    risk_score, risk_level = calculate_risk_score(
        request.credit_score,
        dti_ratio,
        ltv_ratio
    )

    # Determine recommendation
    likely_to_qualify = risk_score <= 50 and dti_ratio <= 50 and request.credit_score >= 620

    if risk_score <= 30:
        recommendation = "LIKELY TO QUALIFY - Strong application profile"
    elif risk_score <= 50:
        recommendation = "LIKELY TO QUALIFY - Good application with minor considerations"
    elif risk_score <= 70:
        recommendation = "CONDITIONAL - May require additional documentation or conditions"
    else:
        recommendation = "UNLIKELY TO QUALIFY - Consider improving credit or reducing loan amount"

    # Build factors explanation
    factors = {}

    # Credit score factor
    if request.credit_score >= 740:
        factors["credit_score"] = "Excellent"
    elif request.credit_score >= 700:
        factors["credit_score"] = "Good"
    elif request.credit_score >= 660:
        factors["credit_score"] = "Fair"
    else:
        factors["credit_score"] = "Needs Improvement"

    # DTI factor
    if dti_ratio <= 36:
        factors["dti_ratio"] = "Excellent"
    elif dti_ratio <= 43:
        factors["dti_ratio"] = "Acceptable"
    elif dti_ratio <= 50:
        factors["dti_ratio"] = "High"
    else:
        factors["dti_ratio"] = "Too High"

    # LTV factor
    if ltv_ratio <= 80:
        factors["ltv_ratio"] = "Good (No PMI required)"
    elif ltv_ratio <= 95:
        factors["ltv_ratio"] = "Acceptable (PMI required)"
    else:
        factors["ltv_ratio"] = "High LTV"

    return QuickAssessmentResponse(
        risk_score=risk_score,
        risk_level=risk_level,
        dti_ratio=round(dti_ratio, 1),
        ltv_ratio=round(ltv_ratio, 1),
        recommendation=recommendation,
        likely_to_qualify=likely_to_qualify,
        estimated_interest_rate=estimated_rate,
        estimated_monthly_payment=round(total_housing_payment, 2),
        factors=factors
    )
