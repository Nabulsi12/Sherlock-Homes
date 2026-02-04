"""
Sherlock Homes Risk Scorer

Calculates composite risk scores (0-100) for loan applications.
Uses traditional underwriting factors as the base, with social/lifestyle
features from feature_extractor.py as small modifiers.

Risk Score = Approximate probability of default (0 = lowest risk, 100 = highest risk)
"""

import json
from typing import Dict, Any, Optional
from dataclasses import dataclass
from keywords_client import KeywordsAIClient
from feature_extractor import (
    FeatureExtractor,
    CombinedFeatures,
    TraditionalFeatures,
    ProfessionalFeatures,
    LifestyleFeatures,
    SocialConnectednessFeatures
)


# =============================================================================
# TEST CASES - Current applications from the dashboard
# =============================================================================

TEST_CASES = [
    {
        "id": "LN-2024-08472",
        "borrower": "James Morrison",
        "loan_type": "30-Year Fixed Conventional",
        "loan_amount": 1420000,
        "property_value": 1775000,
        "ltv": 80.0,
        "property_address": "1847 Oak Valley Dr, Austin, TX",
        "status": "Approved",
        "current_risk_score": 18,
        "credit_score": 780,
        "annual_income": 425000,
        "monthly_debts": 2500,
        "dti": 28,
        "employment_years": 8,
        "reserves_months": 12
    },
    {
        "id": "LN-2024-08471",
        "borrower": "Sarah Chen",
        "loan_type": "15-Year Fixed Conventional",
        "loan_amount": 960000,
        "property_value": 1280000,
        "ltv": 75.0,
        "property_address": "2234 Maple Creek Ln, Denver, CO",
        "status": "Pending Docs",
        "current_risk_score": 32,
        "credit_score": 720,
        "annual_income": 285000,
        "monthly_debts": 1800,
        "dti": 35,
        "employment_years": 4,
        "reserves_months": 6
    },
    {
        "id": "LN-2024-08470",
        "borrower": "Michael Torres",
        "loan_type": "30-Year Fixed FHA",
        "loan_amount": 825000,
        "property_value": 865000,
        "ltv": 95.4,
        "property_address": "789 Sunset Blvd, Phoenix, AZ",
        "status": "Under Review",
        "current_risk_score": 58,
        "credit_score": 640,
        "annual_income": 145000,
        "monthly_debts": 1200,
        "dti": 42,
        "employment_years": 2,
        "reserves_months": 3
    },
    {
        "id": "LN-2024-08469",
        "borrower": "Robert Blake",
        "loan_type": "30-Year Fixed Conventional",
        "loan_amount": 2150000,
        "property_value": 2250000,
        "ltv": 95.6,
        "property_address": "456 Pine Ridge Way, Seattle, WA",
        "status": "Declined",
        "current_risk_score": 84,
        "credit_score": 580,
        "annual_income": 320000,
        "monthly_debts": 4500,
        "dti": 48,
        "employment_years": 1,
        "reserves_months": 1
    }
]


# =============================================================================
# RISK CALCULATION WEIGHTS
# =============================================================================

# Base weights for traditional factors (should sum to ~100% of base score)
TRADITIONAL_WEIGHTS = {
    "credit_score": 0.35,      # 35% - Most important factor
    "dti": 0.25,               # 25% - Debt-to-income ratio
    "ltv": 0.20,               # 20% - Loan-to-value ratio
    "employment": 0.10,        # 10% - Employment stability
    "reserves": 0.10           # 10% - Cash reserves
}

# Modifier weights for social/lifestyle features (small adjustments, +/- 5 points max each)
MODIFIER_WEIGHTS = {
    "professional_credibility": 2.0,    # +/- 2 points
    "job_stability": 2.0,               # +/- 2 points
    "lifestyle_stability": 1.5,         # +/- 1.5 points
    "income_lifestyle_alignment": 1.5,  # +/- 1.5 points
    "social_support": 1.0,              # +/- 1 point
    "community_rootedness": 1.0,        # +/- 1 point
    "relationship_stability": 1.0       # +/- 1 point
}

# Maximum total modifier adjustment
MAX_MODIFIER_ADJUSTMENT = 10  # +/- 10 points max from all modifiers combined


# =============================================================================
# RISK REPORT DATA CLASS
# =============================================================================

@dataclass
class RiskReport:
    """Complete risk assessment report."""
    application_id: str
    borrower_name: str

    # Final scores
    risk_score: int  # 0-100, probability of default
    risk_category: str  # Low, Medium, High, Very High
    recommendation: str  # Approve, Review, Decline

    # Component scores
    base_score: float
    credit_component: float
    dti_component: float
    ltv_component: float
    employment_component: float
    reserves_component: float

    # Modifier adjustments
    total_modifier_adjustment: float
    modifier_breakdown: Dict[str, float]

    # Traditional metrics
    credit_score: int
    dti_ratio: float
    ltv_ratio: float

    # Analysis
    risk_factors: list
    positive_factors: list
    ai_analysis: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "application_id": self.application_id,
            "borrower_name": self.borrower_name,
            "risk_score": self.risk_score,
            "risk_category": self.risk_category,
            "recommendation": self.recommendation,
            # Flat access for frontend convenience
            "credit_score": self.credit_score,
            "dti": self.dti_ratio,
            "ltv": self.ltv_ratio,
            # Score breakdown for the frontend display
            "score_breakdown": {
                "credit_risk": round(self.credit_component * TRADITIONAL_WEIGHTS["credit_score"], 2),
                "dti_risk": round(self.dti_component * TRADITIONAL_WEIGHTS["dti"], 2),
                "ltv_risk": round(self.ltv_component * TRADITIONAL_WEIGHTS["ltv"], 2),
                "employment_risk": round(self.employment_component * TRADITIONAL_WEIGHTS["employment"], 2),
                "reserves_risk": round(self.reserves_component * TRADITIONAL_WEIGHTS["reserves"], 2),
                "feature_modifiers": round(self.total_modifier_adjustment, 2)
            },
            "scores": {
                "base_score": round(self.base_score, 2),
                "credit_component": round(self.credit_component, 2),
                "dti_component": round(self.dti_component, 2),
                "ltv_component": round(self.ltv_component, 2),
                "employment_component": round(self.employment_component, 2),
                "reserves_component": round(self.reserves_component, 2),
                "modifier_adjustment": round(self.total_modifier_adjustment, 2)
            },
            "modifier_breakdown": {k: round(v, 2) for k, v in self.modifier_breakdown.items()},
            "metrics": {
                "credit_score": self.credit_score,
                "dti_ratio": self.dti_ratio,
                "ltv_ratio": self.ltv_ratio
            },
            "risk_factors": self.risk_factors,
            "positive_factors": self.positive_factors,
            "ai_analysis": self.ai_analysis
        }


# =============================================================================
# RISK SCORER CLASS
# =============================================================================

class RiskScorer:
    """
    Calculates comprehensive risk scores for loan applications.

    The scoring system:
    1. Calculates base score from traditional factors (credit, DTI, LTV, employment, reserves)
    2. Applies small modifiers from social/lifestyle analysis
    3. Generates AI-powered analysis and recommendations
    """

    def __init__(self, model: str = "gpt-4o"):
        """Initialize the risk scorer."""
        try:
            self.client = KeywordsAIClient(default_model=model)
        except ValueError:
            self.client = None
            print("Warning: Keywords AI client not configured. AI analysis disabled.")

        self.feature_extractor = FeatureExtractor()
        self.model = model

    # =========================================================================
    # BASE SCORE CALCULATIONS
    # =========================================================================

    def _calculate_credit_risk(self, credit_score: int) -> float:
        """
        Calculate risk component from credit score.
        Higher credit score = lower risk.

        Credit Score Ranges:
        - 800-850: Exceptional (5-10 risk)
        - 740-799: Very Good (10-20 risk)
        - 670-739: Good (20-35 risk)
        - 580-669: Fair (35-55 risk)
        - 300-579: Poor (55-80 risk)
        """
        if credit_score >= 800:
            return 5 + (850 - credit_score) * 0.1
        elif credit_score >= 740:
            return 10 + (799 - credit_score) * 0.17
        elif credit_score >= 670:
            return 20 + (739 - credit_score) * 0.22
        elif credit_score >= 580:
            return 35 + (669 - credit_score) * 0.22
        else:
            return 55 + (579 - credit_score) * 0.09

    def _calculate_dti_risk(self, dti: float) -> float:
        """
        Calculate risk component from DTI ratio.
        Higher DTI = higher risk.

        DTI Ranges:
        - 0-20%: Very Low Risk (5-15)
        - 20-36%: Acceptable (15-30)
        - 36-43%: Elevated (30-50)
        - 43-50%: High (50-70)
        - 50%+: Very High (70-90)
        """
        if dti <= 20:
            return 5 + dti * 0.5
        elif dti <= 36:
            return 15 + (dti - 20) * 0.94
        elif dti <= 43:
            return 30 + (dti - 36) * 2.86
        elif dti <= 50:
            return 50 + (dti - 43) * 2.86
        else:
            return min(70 + (dti - 50) * 2, 90)

    def _calculate_ltv_risk(self, ltv: float) -> float:
        """
        Calculate risk component from LTV ratio.
        Higher LTV = higher risk.

        LTV Ranges:
        - 0-60%: Very Low Risk (5-15)
        - 60-80%: Low Risk (15-25)
        - 80-90%: Moderate (25-45)
        - 90-95%: Elevated (45-65)
        - 95%+: High (65-85)
        """
        if ltv <= 60:
            return 5 + ltv * 0.17
        elif ltv <= 80:
            return 15 + (ltv - 60) * 0.5
        elif ltv <= 90:
            return 25 + (ltv - 80) * 2
        elif ltv <= 95:
            return 45 + (ltv - 90) * 4
        else:
            return min(65 + (ltv - 95) * 4, 85)

    def _calculate_employment_risk(self, years: float) -> float:
        """
        Calculate risk component from employment stability.
        Longer employment = lower risk.

        Years at Job:
        - 5+ years: Low Risk (10-20)
        - 2-5 years: Moderate (20-40)
        - 1-2 years: Elevated (40-55)
        - <1 year: High (55-70)
        """
        if years >= 5:
            return 10 + max(0, (10 - years)) * 1
        elif years >= 2:
            return 20 + (5 - years) * 6.67
        elif years >= 1:
            return 40 + (2 - years) * 15
        else:
            return 55 + (1 - years) * 15

    def _calculate_reserves_risk(self, months: int) -> float:
        """
        Calculate risk component from cash reserves.
        More reserves = lower risk.

        Months of Reserves:
        - 12+ months: Very Low (5-15)
        - 6-12 months: Low (15-30)
        - 3-6 months: Moderate (30-45)
        - 1-3 months: Elevated (45-60)
        - <1 month: High (60-75)
        """
        if months >= 12:
            return 5 + max(0, (24 - months)) * 0.83
        elif months >= 6:
            return 15 + (12 - months) * 2.5
        elif months >= 3:
            return 30 + (6 - months) * 5
        elif months >= 1:
            return 45 + (3 - months) * 7.5
        else:
            return 60 + (1 - months) * 15

    # =========================================================================
    # MODIFIER CALCULATIONS FROM FEATURE EXTRACTOR
    # =========================================================================

    def _calculate_modifiers(self, features: CombinedFeatures) -> Dict[str, float]:
        """
        Calculate risk modifiers from social/lifestyle features.
        Each modifier ranges from -weight to +weight.
        Positive values increase risk, negative values decrease risk.
        """
        modifiers = {}

        # Professional credibility (higher = lower risk)
        # Score is 0-1, convert to modifier: 0.5 baseline, so (0.5 - score) * weight
        prof_score = features.professional.professional_credibility_score
        modifiers["professional_credibility"] = (0.5 - prof_score) * MODIFIER_WEIGHTS["professional_credibility"] * 2

        # Job stability (higher = lower risk)
        job_score = features.professional.job_stability_score
        modifiers["job_stability"] = (0.5 - job_score) * MODIFIER_WEIGHTS["job_stability"] * 2

        # Lifestyle stability (higher = lower risk)
        lifestyle_score = features.lifestyle.lifestyle_stability_score
        modifiers["lifestyle_stability"] = (0.5 - lifestyle_score) * MODIFIER_WEIGHTS["lifestyle_stability"] * 2

        # Income-lifestyle alignment (higher = lower risk)
        alignment_score = features.lifestyle.income_lifestyle_alignment
        modifiers["income_lifestyle_alignment"] = (0.5 - alignment_score) * MODIFIER_WEIGHTS["income_lifestyle_alignment"] * 2

        # Social support (higher = lower risk)
        social_score = features.social.social_support_score
        modifiers["social_support"] = (0.5 - social_score) * MODIFIER_WEIGHTS["social_support"] * 2

        # Community rootedness (higher = lower risk)
        community_score = features.social.community_rootedness_score
        modifiers["community_rootedness"] = (0.5 - community_score) * MODIFIER_WEIGHTS["community_rootedness"] * 2

        # Relationship stability (higher = lower risk)
        relationship_score = features.social.relationship_stability_score
        modifiers["relationship_stability"] = (0.5 - relationship_score) * MODIFIER_WEIGHTS["relationship_stability"] * 2

        # Red flag adjustments
        if features.lifestyle.gambling_indicators:
            modifiers["gambling_flag"] = 3.0  # +3 points risk
        if features.lifestyle.substance_use_indicators:
            modifiers["substance_flag"] = 2.0  # +2 points risk
        if features.professional.frequent_job_changes:
            modifiers["job_hopping_flag"] = 1.5  # +1.5 points risk
        if features.social.social_isolation_indicators:
            modifiers["isolation_flag"] = 1.0  # +1 point risk

        return modifiers

    # =========================================================================
    # MAIN SCORING METHOD
    # =========================================================================

    def score_application(
        self,
        application: Dict[str, Any],
        professional_features: ProfessionalFeatures = None,
        lifestyle_features: LifestyleFeatures = None,
        social_features: SocialConnectednessFeatures = None
    ) -> RiskReport:
        """
        Calculate comprehensive risk score for a loan application.

        Args:
            application: Dict with loan application data
            professional_features: Optional professional profile features
            lifestyle_features: Optional lifestyle features
            social_features: Optional social connectedness features

        Returns:
            RiskReport with complete analysis
        """
        # Extract basic data
        app_id = application.get("id", "NEW")
        borrower = application.get("borrower", "Unknown")
        credit_score = application.get("credit_score", 680)
        dti = application.get("dti", 36)
        ltv = application.get("ltv", 80)
        employment_years = application.get("employment_years", 2)
        reserves_months = application.get("reserves_months", 3)

        # Calculate component scores
        credit_risk = self._calculate_credit_risk(credit_score)
        dti_risk = self._calculate_dti_risk(dti)
        ltv_risk = self._calculate_ltv_risk(ltv)
        employment_risk = self._calculate_employment_risk(employment_years)
        reserves_risk = self._calculate_reserves_risk(reserves_months)

        # Calculate weighted base score
        base_score = (
            credit_risk * TRADITIONAL_WEIGHTS["credit_score"] +
            dti_risk * TRADITIONAL_WEIGHTS["dti"] +
            ltv_risk * TRADITIONAL_WEIGHTS["ltv"] +
            employment_risk * TRADITIONAL_WEIGHTS["employment"] +
            reserves_risk * TRADITIONAL_WEIGHTS["reserves"]
        )

        # Calculate modifiers from social/lifestyle features
        modifier_breakdown = {}
        total_modifier = 0.0

        if professional_features or lifestyle_features or social_features:
            # Create combined features
            traditional = self.feature_extractor.extract_traditional_features(application)
            combined = CombinedFeatures(
                traditional=traditional,
                professional=professional_features or ProfessionalFeatures(),
                lifestyle=lifestyle_features or LifestyleFeatures(),
                social=social_features or SocialConnectednessFeatures()
            )

            modifier_breakdown = self._calculate_modifiers(combined)
            total_modifier = sum(modifier_breakdown.values())

            # Cap total modifier adjustment
            total_modifier = max(-MAX_MODIFIER_ADJUSTMENT, min(MAX_MODIFIER_ADJUSTMENT, total_modifier))

        # Calculate final score
        final_score = base_score + total_modifier
        final_score = max(0, min(100, final_score))  # Clamp to 0-100
        risk_score = round(final_score)

        # Determine risk category and recommendation
        if risk_score <= 25:
            risk_category = "Low"
            recommendation = "Approve"
        elif risk_score <= 45:
            risk_category = "Moderate"
            recommendation = "Approve with Conditions"
        elif risk_score <= 65:
            risk_category = "Elevated"
            recommendation = "Manual Review Required"
        elif risk_score <= 80:
            risk_category = "High"
            recommendation = "Decline Recommended"
        else:
            risk_category = "Very High"
            recommendation = "Decline"

        # Identify risk factors and positive factors
        risk_factors = []
        positive_factors = []

        if credit_score < 620:
            risk_factors.append(f"Poor credit score ({credit_score})")
        elif credit_score >= 740:
            positive_factors.append(f"Excellent credit score ({credit_score})")

        if dti > 43:
            risk_factors.append(f"High DTI ratio ({dti}%)")
        elif dti <= 28:
            positive_factors.append(f"Low DTI ratio ({dti}%)")

        if ltv > 90:
            risk_factors.append(f"High LTV ratio ({ltv}%) - minimal equity")
        elif ltv <= 80:
            positive_factors.append(f"Conservative LTV ({ltv}%) - good equity position")

        if employment_years < 2:
            risk_factors.append(f"Short employment history ({employment_years} years)")
        elif employment_years >= 5:
            positive_factors.append(f"Stable employment ({employment_years}+ years)")

        if reserves_months < 3:
            risk_factors.append(f"Limited reserves ({reserves_months} months)")
        elif reserves_months >= 6:
            positive_factors.append(f"Strong reserves ({reserves_months} months)")

        # Add modifier-based factors
        for key, value in modifier_breakdown.items():
            if value > 1:
                risk_factors.append(f"Social indicator: {key.replace('_', ' ')}")
            elif value < -1:
                positive_factors.append(f"Social indicator: {key.replace('_', ' ')}")

        # Generate AI analysis
        ai_analysis = self._generate_ai_analysis(
            application, risk_score, risk_category,
            risk_factors, positive_factors
        )

        return RiskReport(
            application_id=app_id,
            borrower_name=borrower,
            risk_score=risk_score,
            risk_category=risk_category,
            recommendation=recommendation,
            base_score=base_score,
            credit_component=credit_risk,
            dti_component=dti_risk,
            ltv_component=ltv_risk,
            employment_component=employment_risk,
            reserves_component=reserves_risk,
            total_modifier_adjustment=total_modifier,
            modifier_breakdown=modifier_breakdown,
            credit_score=credit_score,
            dti_ratio=dti,
            ltv_ratio=ltv,
            risk_factors=risk_factors,
            positive_factors=positive_factors,
            ai_analysis=ai_analysis
        )

    def _generate_ai_analysis(
        self,
        application: Dict[str, Any],
        risk_score: int,
        risk_category: str,
        risk_factors: list,
        positive_factors: list
    ) -> str:
        """Generate AI-powered analysis narrative."""
        if not self.client:
            return "AI analysis unavailable - Keywords AI client not configured."

        prompt = f"""You are an expert mortgage underwriter for Sherlock Homes, an AI-powered underwriting platform.

Analyze this loan application and provide a professional underwriting assessment.

APPLICATION DATA:
- Borrower: {application.get('borrower', 'Unknown')}
- Loan Amount: ${application.get('loan_amount', 0):,}
- Property Value: ${application.get('property_value', 0):,}
- Loan Type: {application.get('loan_type', 'Conventional')}
- Property Address: {application.get('property_address', 'N/A')}

KEY METRICS:
- Credit Score: {application.get('credit_score', 'N/A')}
- DTI Ratio: {application.get('dti', 'N/A')}%
- LTV Ratio: {application.get('ltv', 'N/A')}%
- Employment: {application.get('employment_years', 'N/A')} years
- Reserves: {application.get('reserves_months', 'N/A')} months

CALCULATED RISK:
- Risk Score: {risk_score}/100
- Risk Category: {risk_category}

IDENTIFIED RISK FACTORS:
{chr(10).join('- ' + f for f in risk_factors) if risk_factors else '- None identified'}

POSITIVE FACTORS:
{chr(10).join('- ' + f for f in positive_factors) if positive_factors else '- None identified'}

Provide a 2-3 paragraph professional assessment that:
1. Summarizes the overall risk profile
2. Explains the key factors driving the risk score
3. Provides a clear recommendation with any conditions

Keep the tone professional and suitable for an underwriting report."""

        try:
            response = self.client.complete(
                prompt=prompt,
                system_prompt="You are an expert mortgage underwriter providing professional loan assessments.",
                temperature=0.3,
                max_tokens=500,
                metadata={
                    "task": "risk_analysis",
                    "application_id": application.get("id"),
                    "risk_score": risk_score
                }
            )
            return response
        except Exception as e:
            return f"AI analysis error: {str(e)}"

    # =========================================================================
    # CONVENIENCE METHODS
    # =========================================================================

    def score_from_form(
        self,
        borrower_name: str,
        loan_amount: float,
        property_value: float,
        loan_type: str,
        property_address: str,
        credit_score: int,
        annual_income: float,
        monthly_debts: float,
        employment_years: float,
        reserves_months: int = 3,
        # Optional social profile data
        linkedin_url: str = None,
        instagram_url: str = None,
        **additional_fields
    ) -> RiskReport:
        """
        Score an application from form input.

        This is the main method called by the frontend.
        """
        # Calculate DTI
        monthly_income = annual_income / 12

        # Estimate monthly payment (rough calculation for DTI)
        # Using 6.5% rate, 30-year term
        rate = 0.065 / 12
        term = 360
        monthly_payment = loan_amount * (rate * (1 + rate)**term) / ((1 + rate)**term - 1)

        total_monthly_debt = monthly_debts + monthly_payment
        dti = (total_monthly_debt / monthly_income) * 100 if monthly_income > 0 else 50

        # Calculate LTV
        ltv = (loan_amount / property_value) * 100 if property_value > 0 else 100

        application = {
            "id": f"NEW-{borrower_name[:3].upper()}",
            "borrower": borrower_name,
            "loan_amount": loan_amount,
            "property_value": property_value,
            "loan_type": loan_type,
            "property_address": property_address,
            "credit_score": credit_score,
            "annual_income": annual_income,
            "dti": round(dti, 1),
            "ltv": round(ltv, 1),
            "employment_years": employment_years,
            "reserves_months": reserves_months,
            **additional_fields
        }

        # TODO: If social URLs provided, analyze profiles and extract features
        # professional_features = None
        # lifestyle_features = None
        # social_features = None
        #
        # if linkedin_url:
        #     # Analyze LinkedIn profile
        #     pass
        # if instagram_url:
        #     # Analyze Instagram profile
        #     pass

        return self.score_application(application)

    def score_all_test_cases(self) -> list:
        """Score all test cases from the dashboard."""
        results = []
        for case in TEST_CASES:
            print(f"Scoring {case['id']}...")
            report = self.score_application(case)
            results.append(report.to_dict())
        return results


# =============================================================================
# API ENDPOINT HELPER
# =============================================================================

def process_form_submission(form_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process a form submission from the frontend.

    Expected form_data fields:
    - borrower_name: str
    - loan_amount: float
    - property_value: float
    - loan_type: str
    - property_address: str
    - credit_score: int
    - annual_income: float
    - monthly_debts: float
    - employment_years: float
    - reserves_months: int (optional)
    - linkedin_url: str (optional)
    - instagram_url: str (optional)
    """
    scorer = RiskScorer()

    try:
        report = scorer.score_from_form(
            borrower_name=form_data.get("borrower_name", ""),
            loan_amount=float(form_data.get("loan_amount", 0)),
            property_value=float(form_data.get("property_value", 0)),
            loan_type=form_data.get("loan_type", "30-Year Fixed Conventional"),
            property_address=form_data.get("property_address", ""),
            credit_score=int(form_data.get("credit_score", 680)),
            annual_income=float(form_data.get("annual_income", 0)),
            monthly_debts=float(form_data.get("monthly_debts", 0)),
            employment_years=float(form_data.get("employment_years", 2)),
            reserves_months=int(form_data.get("reserves_months", 3)),
            linkedin_url=form_data.get("linkedin_url"),
            instagram_url=form_data.get("instagram_url")
        )

        return {
            "status": "success",
            "report": report.to_dict()
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("Sherlock Homes Risk Scorer")
    print("=" * 60)
    print()

    scorer = RiskScorer()

    print("Scoring Test Cases:")
    print("-" * 60)

    for case in TEST_CASES:
        report = scorer.score_application(case)
        print(f"\n{report.application_id}: {report.borrower_name}")
        print(f"  Credit: {report.credit_score} | DTI: {report.dti_ratio}% | LTV: {report.ltv_ratio}%")
        print(f"  Base Score: {report.base_score:.1f}")
        print(f"  Final Risk Score: {report.risk_score}/100 ({report.risk_category})")
        print(f"  Recommendation: {report.recommendation}")
        print(f"  Risk Factors: {', '.join(report.risk_factors[:2]) if report.risk_factors else 'None'}")
        print(f"  Positive Factors: {', '.join(report.positive_factors[:2]) if report.positive_factors else 'None'}")

    print()
    print("-" * 60)
    print()

    # Example form submission
    print("Example: Scoring a new form submission...")
    result = process_form_submission({
        "borrower_name": "Jane Smith",
        "loan_amount": 450000,
        "property_value": 550000,
        "loan_type": "30-Year Fixed Conventional",
        "property_address": "123 Main St, Austin, TX",
        "credit_score": 740,
        "annual_income": 120000,
        "monthly_debts": 800,
        "employment_years": 5,
        "reserves_months": 6
    })

    if result["status"] == "success":
        r = result["report"]
        print(f"\nNew Application Result:")
        print(f"  Risk Score: {r['risk_score']}/100 ({r['risk_category']})")
        print(f"  Recommendation: {r['recommendation']}")
    else:
        print(f"Error: {result['message']}")
