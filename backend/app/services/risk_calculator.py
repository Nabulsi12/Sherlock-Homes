"""
Risk Calculator Service - Calculates risk scores and assessments
"""

from app.models.schemas import (
    LoanApplicationRequest,
    RiskAssessment,
    RiskLevel,
    RiskFactors,
    GatheredData
)
from app.utils.logger import logger
import math


class RiskCalculatorService:
    """
    Calculate risk scores based on standard underwriting metrics
    """

    def __init__(self):
        pass

    async def calculate_risk(
        self,
        application: LoanApplicationRequest,
        gathered_data: GatheredData
    ) -> RiskAssessment:
        """
        Calculate comprehensive risk assessment

        Risk factors considered:
        - Credit score
        - DTI (Debt-to-Income) ratio
        - LTV (Loan-to-Value) ratio
        - Employment stability
        - Income verification
        - Property type and occupancy
        """
        logger.info(f"Calculating risk for {application.applicant.full_name}")

        # Calculate key ratios
        ltv_ratio = self._calculate_ltv(
            application.loan_details.loan_amount,
            application.property_info.estimated_value
        )

        # Estimate DTI (in production, calculate from actual debt data)
        dti_ratio = self._estimate_dti(
            application.loan_details.loan_amount,
            application.applicant.annual_income
        )

        # Calculate individual risk scores
        credit_risk = self._assess_credit_risk(application.applicant.credit_score)
        dti_risk = self._assess_dti_risk(dti_ratio)
        ltv_risk = self._assess_ltv_risk(ltv_ratio)
        employment_risk = self._assess_employment_risk(application.applicant.years_employed)
        income_risk = self._assess_income_risk(application.applicant.annual_income)
        property_risk = self._assess_property_risk(
            application.property_info.property_type.value,
            application.property_info.occupancy.value
        )

        # Calculate overall risk score (0-100)
        risk_score = self._calculate_overall_risk_score(
            credit_risk, dti_risk, ltv_risk,
            employment_risk, income_risk, property_risk
        )

        # Determine risk level
        risk_level = self._determine_risk_level(risk_score)

        # Generate recommendation
        recommendation = self._generate_recommendation(
            risk_score, risk_level, ltv_ratio, dti_ratio,
            application.applicant.credit_score
        )

        # Estimate interest rate and monthly payment
        estimated_rate = self._estimate_interest_rate(risk_score, application.loan_details.loan_type.value)
        estimated_payment = self._calculate_monthly_payment(
            application.loan_details.loan_amount,
            estimated_rate,
            application.loan_details.loan_type.value
        )

        # Create risk factors breakdown
        risk_factors = RiskFactors(
            credit_score_risk=credit_risk["level"],
            dti_ratio_risk=dti_risk["level"],
            ltv_ratio_risk=ltv_risk["level"],
            employment_stability_risk=employment_risk["level"],
            income_verification_risk=income_risk["level"],
            property_risk=property_risk["level"]
        )

        return RiskAssessment(
            risk_score=risk_score,
            risk_level=risk_level,
            dti_ratio=round(dti_ratio, 2),
            ltv_ratio=round(ltv_ratio, 2),
            risk_factors=risk_factors,
            recommendation=recommendation,
            estimated_interest_rate=round(estimated_rate, 3),
            estimated_monthly_payment=round(estimated_payment, 2)
        )

    def _calculate_ltv(self, loan_amount: float, property_value: float) -> float:
        """Calculate Loan-to-Value ratio"""
        return (loan_amount / property_value) * 100

    def _estimate_dti(self, loan_amount: float, annual_income: float) -> float:
        """Estimate Debt-to-Income ratio (simplified for hackathon)"""
        # Rough estimate: assume 30-year loan at 7% interest
        monthly_payment = (loan_amount * 0.00665) / (1 - (1 + 0.00665) ** -360)
        monthly_income = annual_income / 12
        return (monthly_payment / monthly_income) * 100

    def _assess_credit_risk(self, credit_score: int) -> dict:
        """Assess risk based on credit score (0-35 points)"""
        if credit_score >= 760:
            return {"score": 0, "level": "Excellent"}
        elif credit_score >= 720:
            return {"score": 10, "level": "Very Good"}
        elif credit_score >= 680:
            return {"score": 20, "level": "Good"}
        elif credit_score >= 640:
            return {"score": 28, "level": "Fair"}
        else:
            return {"score": 35, "level": "Poor"}

    def _assess_dti_risk(self, dti_ratio: float) -> dict:
        """Assess risk based on DTI ratio (0-35 points)"""
        if dti_ratio <= 28:
            return {"score": 0, "level": "Excellent"}
        elif dti_ratio <= 36:
            return {"score": 10, "level": "Good"}
        elif dti_ratio <= 43:
            return {"score": 20, "level": "Acceptable"}
        elif dti_ratio <= 50:
            return {"score": 28, "level": "High"}
        else:
            return {"score": 35, "level": "Excessive"}

    def _assess_ltv_risk(self, ltv_ratio: float) -> dict:
        """Assess risk based on LTV ratio (0-30 points)"""
        if ltv_ratio <= 80:
            return {"score": 0, "level": "Low"}
        elif ltv_ratio <= 90:
            return {"score": 10, "level": "Moderate"}
        elif ltv_ratio <= 95:
            return {"score": 20, "level": "Elevated"}
        else:
            return {"score": 30, "level": "High"}

    def _assess_employment_risk(self, years_employed: float) -> dict:
        """Assess employment stability risk (0-10 points)"""
        if not years_employed:
            return {"score": 10, "level": "Unknown"}
        if years_employed >= 5:
            return {"score": 0, "level": "Stable"}
        elif years_employed >= 2:
            return {"score": 3, "level": "Adequate"}
        elif years_employed >= 1:
            return {"score": 7, "level": "Marginal"}
        else:
            return {"score": 10, "level": "Insufficient"}

    def _assess_income_risk(self, annual_income: float) -> dict:
        """Assess income level risk (0-10 points)"""
        if annual_income >= 100000:
            return {"score": 0, "level": "Strong"}
        elif annual_income >= 75000:
            return {"score": 3, "level": "Good"}
        elif annual_income >= 50000:
            return {"score": 7, "level": "Adequate"}
        else:
            return {"score": 10, "level": "Limited"}

    def _assess_property_risk(self, property_type: str, occupancy: str) -> dict:
        """Assess property and occupancy risk"""
        risk_score = 5
        if "Investment" in occupancy:
            risk_score += 10
        if "Condo" in property_type or "PUD" in property_type:
            risk_score += 5

        if risk_score <= 10:
            level = "Low"
        elif risk_score <= 15:
            level = "Moderate"
        else:
            level = "Elevated"

        return {"score": risk_score, "level": level}

    def _calculate_overall_risk_score(
        self, credit_risk, dti_risk, ltv_risk,
        employment_risk, income_risk, property_risk
    ) -> int:
        """Calculate overall risk score using simple addition

        Components contribute:
        - Credit: 0-35 points
        - DTI: 0-35 points
        - LTV: 0-30 points
        - Employment: 0-10 points
        - Income: 0-10 points
        - Property: minimal impact (not used in sum)

        Total: 0-120 points (clamped to 0-100)
        """
        total_score = (
            credit_risk["score"] +      # 0-35 range
            dti_risk["score"] +          # 0-35 range
            ltv_risk["score"] +          # 0-30 range
            employment_risk["score"] +   # 0-10 range
            income_risk["score"]         # 0-10 range
            # property_risk removed from sum (was only 5% anyway)
        )

        return min(100, max(0, int(total_score)))

    def _determine_risk_level(self, risk_score: int) -> RiskLevel:
        """Determine risk level from score"""
        if risk_score <= 30:
            return RiskLevel.LOW
        elif risk_score <= 60:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.HIGH

    def _generate_recommendation(
        self, risk_score: int, risk_level: RiskLevel,
        ltv_ratio: float, dti_ratio: float, credit_score: int
    ) -> str:
        """Generate underwriting recommendation"""
        if risk_level == RiskLevel.LOW:
            return "APPROVED - Low risk applicant. Recommend approval with standard terms."
        elif risk_level == RiskLevel.MEDIUM:
            conditions = []
            if ltv_ratio > 80:
                conditions.append("PMI required")
            if dti_ratio > 36:
                conditions.append("additional income verification")
            if credit_score < 700:
                conditions.append("higher interest rate")

            cond_str = ", ".join(conditions) if conditions else "standard conditions"
            return f"CONDITIONAL APPROVAL - Moderate risk. Recommend approval with {cond_str}."
        else:
            return "DECLINE - High risk applicant. Recommend decline or significant conditions."

    def _estimate_interest_rate(self, risk_score: int, loan_type: str) -> float:
        """Estimate interest rate based on risk"""
        base_rate = 6.5  # Base rate for 30-year fixed

        # Adjust for loan type
        if "15-Year" in loan_type:
            base_rate -= 0.5
        elif "ARM" in loan_type:
            base_rate -= 0.75

        # Add risk premium
        risk_premium = (risk_score / 100) * 2.5  # Up to 2.5% premium for high risk

        return base_rate + risk_premium

    def _calculate_monthly_payment(
        self, loan_amount: float, annual_rate: float, loan_type: str
    ) -> float:
        """Calculate estimated monthly payment"""
        # Determine loan term in months
        if "15-Year" in loan_type:
            months = 180
        else:
            months = 360  # Default to 30 years

        # Monthly interest rate
        monthly_rate = annual_rate / 100 / 12

        # Calculate payment using mortgage formula
        if monthly_rate == 0:
            return loan_amount / months

        payment = loan_amount * (
            monthly_rate * (1 + monthly_rate) ** months
        ) / ((1 + monthly_rate) ** months - 1)

        return payment
