"""
AI Agent Service - Orchestrates the entire underwriting analysis
Integrated with Joseph's framework (keywords_client, feature_extractor, profile_analyzer)
"""

from app.config import settings
from app.models.schemas import (
    LoanApplicationRequest,
    RiskAssessment,
    ComplianceCheck,
    GatheredData,
)
from app.services.risk_calculator import RiskCalculatorService
from app.services.compliance_checker import ComplianceCheckerService
from app.services.keywords_client import KeywordsAIClient
from app.services.feature_extractor import FeatureExtractor
from app.services.profile_analyzer import analyze_multiple_profiles
from app.utils.logger import logger
from typing import Dict, Any, List
import json


class AIAgentService:
    """
    Main AI Agent that coordinates all analysis tasks
    Integrated with Joseph's ML-based feature extraction framework
    """

    def __init__(self):
        # Use Joseph's Keywords AI client
        self.client = KeywordsAIClient(api_key=settings.KEYWORDS_API_KEY)
        self.feature_extractor = FeatureExtractor(keywords_client=self.client)
        self.risk_calculator = RiskCalculatorService()
        self.compliance_checker = ComplianceCheckerService()

    async def analyze_loan_application(
        self,
        application_id: str,
        application: LoanApplicationRequest
    ) -> Dict[str, Any]:
        """
        Perform comprehensive analysis of loan application

        Analyzes traditional Big 3 factors + Fourth Factor (social media insights):
        1. Income (from application)
        2. Collateral/Property Value (from application)
        3. Credit Score (from application)
        4. Social Media Insights (from profile_analyzer - the fourth factor)

        Steps:
        1. Gather profile data using Joseph's profile_analyzer (Fourth Factor)
        2. Extract ML features using Joseph's feature_extractor
        3. Calculate risk assessment based on Big 3 + Fourth Factor
        4. Check compliance with regulations
        """
        logger.info(f"Starting analysis for application {application_id}")

        # Step 1: Gather profile data using Joseph's profile_analyzer (Fourth Factor)
        gathered_data, ml_features = await self._gather_profile_data(application)

        # Step 2: Calculate risk assessment (enhanced with ML features from Fourth Factor)
        risk_assessment = await self.risk_calculator.calculate_risk(
            application=application,
            gathered_data=gathered_data
        )

        # Step 3: Check compliance and get AI summary with risk score
        compliance_check, ai_summary = await self.compliance_checker.check_compliance(
            application=application,
            risk_assessment=risk_assessment
        )

        # Return Big 3 + Fourth Factor analysis + AI Assessment
        return {
            "risk_assessment": risk_assessment,
            "compliance_check": compliance_check,
            "ai_summary": ai_summary,  # AI-generated summary with risk score
            "fourth_factor": gathered_data,  # Social media insights as the fourth factor
            "ml_features": ml_features  # 60+ ML features for future model training
        }

    async def _gather_profile_data(
        self,
        application: LoanApplicationRequest
    ) -> tuple[GatheredData, Dict[str, float]]:
        """
        Gather profile data using Joseph's profile_analyzer
        Returns: (GatheredData, ML features dict)
        """
        # Collect all provided profile URLs
        profile_urls = []
        if application.applicant.linkedin_url:
            profile_urls.append(str(application.applicant.linkedin_url))
        if hasattr(application.applicant, 'instagram_url') and application.applicant.instagram_url:
            profile_urls.append(str(application.applicant.instagram_url))
        if hasattr(application.applicant, 'facebook_url') and application.applicant.facebook_url:
            profile_urls.append(str(application.applicant.facebook_url))
        if hasattr(application.applicant, 'twitter_handle') and application.applicant.twitter_handle:
            twitter_url = f"https://twitter.com/{application.applicant.twitter_handle.lstrip('@')}"
            profile_urls.append(twitter_url)

        # Prepare traditional features dict
        traditional_data = self._application_to_dict(application)

        if profile_urls and settings.PERPLEXITY_API_KEY:
            try:
                logger.info(f"Analyzing {len(profile_urls)} social media profiles")
                # Use Joseph's profile analyzer
                multi_analysis = analyze_multiple_profiles(profile_urls)

                # Extract ML features using Joseph's feature_extractor
                features = self.feature_extractor.extract_all_features(
                    traditional_data=traditional_data,
                    professional_analysis=multi_analysis.profiles[0].raw_analysis if len(multi_analysis.profiles) > 0 else None,
                    lifestyle_analysis=multi_analysis.profiles[1].raw_analysis if len(multi_analysis.profiles) > 1 else None,
                    social_analysis=multi_analysis.profiles[2].raw_analysis if len(multi_analysis.profiles) > 2 else None
                )

                # Convert to GatheredData for compatibility
                gathered_data = GatheredData(
                    sources=[p.url for p in multi_analysis.profiles],
                    professional_summary=multi_analysis.summary if multi_analysis.summary else None,
                    red_flags=multi_analysis.combined_red_flags if multi_analysis.combined_red_flags else [],
                    positive_indicators=multi_analysis.combined_positive_indicators if multi_analysis.combined_positive_indicators else [],
                    additional_findings=f"Analyzed {len(multi_analysis.profiles)} social media profiles. Professional score: {multi_analysis.overall_professional_score:.0%}, Lifestyle score: {multi_analysis.overall_lifestyle_score:.0%}, Social score: {multi_analysis.overall_social_score:.0%}"
                )

                ml_features = features.to_model_input()
                logger.info(f"Extracted {len(ml_features)} ML features from profiles")

            except Exception as e:
                logger.warning(f"Profile analysis failed: {str(e)}. Using web search fallback.")
                gathered_data, ml_features = self._fallback_with_search(application, traditional_data)
        else:
            # No profiles provided or Perplexity key missing - try web search
            if not profile_urls:
                logger.info("No social media profiles provided - attempting web search")
            if not settings.PERPLEXITY_API_KEY:
                logger.warning("PERPLEXITY_API_KEY not set - skipping profile analysis")

            gathered_data, ml_features = self._fallback_with_search(application, traditional_data)

        return gathered_data, ml_features

    def _fallback_with_search(
        self,
        application: LoanApplicationRequest,
        traditional_data: Dict[str, Any]
    ) -> tuple[GatheredData, Dict[str, float]]:
        """
        Fallback: Search for person by name and job when social media is unavailable.
        Uses Perplexity Sonar to search public web sources.
        """
        # Extract location from property address (address field contains full address)
        location = None
        if application.property_info and application.property_info.address:
            # Try to extract city/state from full address
            location = application.property_info.address

        # Try to search for the person by name and job
        features = self.feature_extractor.extract_all_features(
            traditional_data=traditional_data,
            applicant_name=application.applicant.full_name,
            applicant_employer=application.applicant.employer_name,
            applicant_location=location
        )

        # Check if search was successful
        if hasattr(features.professional, 'search_based') and features.professional.search_based:
            logger.info(f"Web search successful for {application.applicant.full_name}")

            # Build professional insights summary
            prof = features.professional
            professional_insights = {
                "search_method": "Web search via Perplexity Sonar API",
                "applicant_searched": application.applicant.full_name,
                "employer_searched": application.applicant.employer_name,
                "scores": {
                    "job_stability_score": round(prof.job_stability_score * 100),
                    "professional_credibility_score": round(prof.professional_credibility_score * 100),
                    "career_trajectory": ["Declining", "Unstable", "Stable", "Growing", "Rapidly Growing"][prof.career_trajectory - 1] if 1 <= prof.career_trajectory <= 5 else "Unknown",
                    "education_level": ["Unknown", "High School", "Associate", "Bachelors", "Masters", "PhD"][prof.education_level] if 0 <= prof.education_level <= 5 else "Unknown",
                    "industry": prof.industry or "Not identified",
                    "industry_stability": round(prof.industry_stability * 100),
                    "total_experience_years": prof.total_experience_years,
                },
                "flags": {
                    "employment_gaps_detected": prof.employment_gaps,
                    "frequent_job_changes": prof.frequent_job_changes,
                    "profile_inconsistencies": prof.profile_inconsistencies
                }
            }

            # Build positive indicators from search
            positive_indicators = []
            if prof.job_stability_score >= 0.7:
                positive_indicators.append(f"Strong job stability score ({round(prof.job_stability_score * 100)}%)")
            if prof.professional_credibility_score >= 0.7:
                positive_indicators.append(f"High professional credibility ({round(prof.professional_credibility_score * 100)}%)")
            if prof.career_trajectory >= 4:
                positive_indicators.append("Growing career trajectory")
            if prof.education_level >= 3:
                edu_levels = ["Unknown", "High School", "Associate", "Bachelors", "Masters", "PhD"]
                positive_indicators.append(f"Education: {edu_levels[prof.education_level]}")
            if prof.total_experience_years >= 10:
                positive_indicators.append(f"{prof.total_experience_years}+ years of experience")

            # Build red flags from search
            red_flags = []
            if prof.employment_gaps > 0:
                red_flags.append(f"Employment gaps detected ({prof.employment_gaps})")
            if prof.frequent_job_changes:
                red_flags.append("Frequent job changes in recent history")
            if prof.job_stability_score < 0.4:
                red_flags.append(f"Low job stability score ({round(prof.job_stability_score * 100)}%)")

            gathered_data = GatheredData(
                sources=["Web search (Perplexity Sonar)"],
                professional_summary=features.professional.search_raw_analysis if features.professional.search_raw_analysis else None,
                red_flags=red_flags,
                positive_indicators=positive_indicators,
                social_media_insights=professional_insights,
                additional_findings=f"Searched public web sources for {application.applicant.full_name}. Found professional information via web search."
            )
        else:
            logger.info(f"No web search results for {application.applicant.full_name} - using traditional data only")
            gathered_data = GatheredData(
                sources=["Traditional underwriting data only"],
                additional_findings="No social media profiles provided and web search did not return results. Risk assessment based on traditional factors only."
            )

        return gathered_data, features.to_model_input()

    def _application_to_dict(self, application: LoanApplicationRequest) -> Dict[str, Any]:
        """Convert application to dict for feature extraction"""
        return {
            # Credit
            "credit_score": application.applicant.credit_score,
            "credit_history_years": 0,  # Not in schema, could be added

            # Income & Employment
            "annual_income": application.applicant.annual_income,
            "employment_length_months": int(application.applicant.years_employed * 12) if application.applicant.years_employed else 0,
            "is_self_employed": False,  # Not in schema
            "income_verified": True,  # Assume verified

            # Loan Details
            "loan_amount": application.loan_details.loan_amount,
            "property_value": application.property_info.estimated_value,
            "loan_purpose": application.loan_details.loan_purpose.value.lower().replace(" ", "_"),

            # Property
            "property_type": application.property_info.property_type.value.lower().replace(" ", "_"),
            "is_primary_residence": application.property_info.occupancy.value == "Primary Residence",

            # Assets (not in schema, defaults)
            "total_assets": 0,
            "liquid_assets": 0,
            "reserves_months": 0,
        }

