"""
Compliance Checker Service - Validates against Fannie Mae/Freddie Mac guidelines
Integrated with Joseph's keywords_client
"""

from app.config import settings
from app.models.schemas import (
    LoanApplicationRequest,
    RiskAssessment,
    ComplianceCheck
)
from app.services.keywords_client import KeywordsAIClient
from app.utils.logger import logger
import json


class ComplianceCheckerService:
    """
    Check loan application compliance with regulatory guidelines
    Uses Keywords AI (Joseph's client) to analyze Fannie Mae Selling Guide
    """

    def __init__(self):
        # Use Joseph's Keywords AI client
        self.client = KeywordsAIClient(api_key=settings.KEYWORDS_API_KEY)
        self.guide_path = settings.FANNIE_MAE_GUIDE_PATH

    async def check_compliance(
        self,
        application: LoanApplicationRequest,
        risk_assessment: RiskAssessment
    ) -> tuple[ComplianceCheck, dict]:
        """
        Check compliance with Fannie Mae and Freddie Mac guidelines
        Returns: (ComplianceCheck, AI summary with score)
        """
        logger.info(f"Checking compliance for {application.applicant.full_name}")

        try:
            # Use Claude to analyze compliance AND generate summary with risk score
            compliance_result, ai_summary = await self._analyze_with_claude(
                application, risk_assessment
            )

            return compliance_result, ai_summary

        except Exception as e:
            logger.error(f"Error checking compliance: {str(e)}")
            # Return basic compliance check as fallback with no AI score
            return self._basic_compliance_check(application, risk_assessment), {}

    async def _analyze_with_claude(
        self,
        application: LoanApplicationRequest,
        risk_assessment: RiskAssessment
    ) -> tuple[ComplianceCheck, dict]:
        """
        Use Claude to analyze compliance against Fannie Mae guidelines
        AND generate a comprehensive summary with AI-determined risk score
        Returns: (ComplianceCheck, AI summary dict with 'ai_risk_score' and 'summary')
        """

        # Read the PDF guide (for hackathon, we'll use summarized rules)
        # In production, you would use Claude's PDF reading capability or extract text

        prompt = f"""You are a mortgage underwriting expert. Review this loan application comprehensively.

APPLICATION DETAILS:
- Applicant: {application.applicant.full_name}
- Credit Score: {application.applicant.credit_score}
- DTI Ratio: {risk_assessment.dti_ratio}%
- LTV Ratio: {risk_assessment.ltv_ratio}%
- Loan Amount: ${application.loan_details.loan_amount:,.2f}
- Property Value: ${application.property_info.estimated_value:,.2f}
- Annual Income: ${application.applicant.annual_income:,.2f}
- Employment: {application.applicant.years_employed} years
- Loan Type: {application.loan_details.loan_type.value}
- Property Type: {application.property_info.property_type.value}
- Occupancy: {application.property_info.occupancy.value}
- Loan Purpose: {application.loan_details.loan_purpose.value}

CALCULATED RISK BREAKDOWN:
- Credit Risk: {risk_assessment.risk_factors.credit_score_risk if risk_assessment.risk_factors else 'N/A'}
- DTI Risk: {risk_assessment.risk_factors.dti_ratio_risk if risk_assessment.risk_factors else 'N/A'}
- LTV Risk: {risk_assessment.risk_factors.ltv_ratio_risk if risk_assessment.risk_factors else 'N/A'}
- Calculated Risk Score: {risk_assessment.risk_score}/100

TASK:
1. Analyze this application holistically as an experienced underwriter
2. Assess the overall risk considering ALL factors (not just the calculation)
3. Check compliance with Fannie Mae/Freddie Mac guidelines
4. Provide your own professional risk score (0-100, where 0=no risk, 100=maximum risk)

Return a JSON response with TWO sections:
{{
    "compliance": {{
        "compliant": true/false,
        "fannie_mae_compliant": true/false,
        "freddie_mac_compliant": true/false,
        "guidelines_checked": ["guideline1", "guideline2", ...],
        "violations": ["violation1", ...] or [],
        "warnings": ["warning1", ...] or [],
        "details": "Brief explanation of compliance status"
    }},
    "ai_assessment": {{
        "ai_risk_score": <your professional risk score 0-100>,
        "summary": "2-3 sentence professional summary explaining your risk assessment and key factors that influenced your score"
    }}
}}
"""

        try:
            # Use Keywords AI client
            response_text = self.client.complete(
                prompt=prompt,
                model=settings.CLAUDE_MODEL,
                max_tokens=3072,
                temperature=0.3,  # Lower temperature for compliance checking
                metadata={
                    "task": "compliance_and_assessment",
                    "applicant": application.applicant.full_name
                }
            )

            # Parse JSON response
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            if start_idx != -1 and end_idx > start_idx:
                json_str = response_text[start_idx:end_idx]
                full_response = json.loads(json_str)

                # Extract compliance data
                compliance_data = full_response.get("compliance", {})
                compliance_check = ComplianceCheck(**compliance_data)

                # Extract AI assessment
                ai_assessment = full_response.get("ai_assessment", {})

                return compliance_check, ai_assessment
            else:
                raise ValueError("No JSON found in response")

        except Exception as e:
            logger.error(f"Error in AI compliance analysis: {str(e)}")
            return self._basic_compliance_check(application, risk_assessment), {}

    def _basic_compliance_check(
        self,
        application: LoanApplicationRequest,
        risk_assessment: RiskAssessment
    ) -> ComplianceCheck:
        """
        Fallback: Basic rule-based compliance check
        """
        violations = []
        warnings = []
        guidelines_checked = []

        # Check credit score
        guidelines_checked.append("Minimum Credit Score")
        if application.applicant.credit_score < 620:
            violations.append("Credit score below minimum requirement (620)")

        # Check DTI ratio
        guidelines_checked.append("Maximum DTI Ratio")
        if risk_assessment.dti_ratio and risk_assessment.dti_ratio > 50:
            violations.append(f"DTI ratio ({risk_assessment.dti_ratio}%) exceeds maximum (50%)")
        elif risk_assessment.dti_ratio and risk_assessment.dti_ratio > 43:
            warnings.append(f"DTI ratio ({risk_assessment.dti_ratio}%) above preferred threshold (43%)")

        # Check LTV ratio
        guidelines_checked.append("Maximum LTV Ratio")
        max_ltv = 97 if "FHA" in application.loan_details.loan_type.value else 95
        if risk_assessment.ltv_ratio and risk_assessment.ltv_ratio > max_ltv:
            violations.append(f"LTV ratio ({risk_assessment.ltv_ratio}%) exceeds maximum ({max_ltv}%)")

        # Check property occupancy for investment properties
        guidelines_checked.append("Occupancy Requirements")
        if application.property_info.occupancy.value == "Investment Property":
            if risk_assessment.ltv_ratio and risk_assessment.ltv_ratio > 85:
                violations.append("LTV too high for investment property (max 85%)")
            warnings.append("Investment properties have stricter requirements")

        # Determine overall compliance
        fannie_mae_compliant = len(violations) == 0
        freddie_mac_compliant = len(violations) == 0
        compliant = fannie_mae_compliant and freddie_mac_compliant

        details = "Application reviewed against standard Fannie Mae and Freddie Mac guidelines. "
        if compliant:
            details += "All basic requirements met."
        else:
            details += f"Found {len(violations)} violation(s) and {len(warnings)} warning(s)."

        return ComplianceCheck(
            compliant=compliant,
            fannie_mae_compliant=fannie_mae_compliant,
            freddie_mac_compliant=freddie_mac_compliant,
            guidelines_checked=guidelines_checked,
            violations=violations,
            warnings=warnings,
            details=details
        )
