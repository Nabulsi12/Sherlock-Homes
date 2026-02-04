"""
Feature Extractor for AI Underwriter

Extracts and normalizes features from:
1. LinkedIn/social media profile analysis (professional)
2. Instagram/Facebook/TikTok analysis (lifestyle & social)
3. Standard underwriting data (credit, income, employment, etc.)

These features feed into the ML risk scoring model.
"""

import re
import json
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict, field
from enum import Enum

from keywords_client import KeywordsAIClient


class EducationLevel(Enum):
    """Education level enumeration for scoring."""
    UNKNOWN = 0
    HIGH_SCHOOL = 1
    ASSOCIATE = 2
    BACHELOR = 3
    MASTER = 4
    PHD = 5


class CareerTrajectory(Enum):
    """Career trajectory classification."""
    DECLINING = 1
    UNSTABLE = 2
    STABLE = 3
    GROWING = 4
    RAPIDLY_GROWING = 5


class LifestyleLevel(Enum):
    """Apparent lifestyle/spending level."""
    FRUGAL = 1
    MODEST = 2
    COMFORTABLE = 3
    AFFLUENT = 4
    LAVISH = 5


class RelationshipStatus(Enum):
    """Relationship/family status."""
    UNKNOWN = 0
    SINGLE = 1
    IN_RELATIONSHIP = 2
    MARRIED = 3
    MARRIED_WITH_CHILDREN = 4


@dataclass
class TraditionalFeatures:
    """Standard underwriting features."""
    # Credit
    credit_score: float = 0.0  # 300-850
    credit_history_years: float = 0.0

    # Income & Employment
    annual_income: float = 0.0
    employment_length_months: int = 0
    is_self_employed: bool = False
    income_verified: bool = False

    # Debt
    debt_to_income_ratio: float = 0.0  # DTI as decimal (0.35 = 35%)
    monthly_debt_payments: float = 0.0

    # Loan Details
    loan_amount: float = 0.0
    property_value: float = 0.0
    loan_to_value_ratio: float = 0.0  # LTV as decimal
    loan_purpose: str = "purchase"  # purchase, refinance, cash-out

    # Property
    property_type: str = "single_family"  # single_family, condo, multi_family
    is_primary_residence: bool = True

    # Assets
    total_assets: float = 0.0
    liquid_assets: float = 0.0
    reserves_months: int = 0  # Months of payments in reserves


@dataclass
class ProfessionalFeatures:
    """Features extracted from LinkedIn/professional profiles."""
    # Employment Stability
    current_job_months: int = 0
    total_experience_years: float = 0.0
    jobs_last_5_years: int = 0
    career_trajectory: int = 3  # CareerTrajectory enum value

    # Professional Profile
    education_level: int = 0  # EducationLevel enum value
    has_advanced_degree: bool = False
    industry_stability: float = 0.5  # 0-1, how stable is their industry
    industry: str = ""

    # Network & Credibility
    profile_completeness: float = 0.5  # 0-1
    has_recommendations: bool = False
    connection_count_tier: int = 2  # 1=low (<500), 2=med (500-1000), 3=high (1000+)

    # Red Flags
    employment_gaps: int = 0
    frequent_job_changes: bool = False
    profile_inconsistencies: int = 0

    # Derived Scores
    job_stability_score: float = 0.5  # 0-1
    professional_credibility_score: float = 0.5  # 0-1


@dataclass
class LifestyleFeatures:
    """Features extracted from Instagram/Facebook/TikTok - lifestyle indicators."""
    # Spending Indicators
    lifestyle_level: int = 3  # LifestyleLevel enum value (1-5)
    apparent_spending_vs_income: float = 0.5  # 0=frugal, 0.5=balanced, 1=overspending
    luxury_items_visible: bool = False
    frequent_expensive_travel: bool = False
    vehicle_tier: int = 2  # 1=economy, 2=standard, 3=luxury

    # Housing Indicators
    housing_quality_apparent: int = 2  # 1=modest, 2=average, 3=upscale
    appears_homeowner: bool = False
    location_cost_of_living: float = 0.5  # 0-1 relative scale

    # Activities & Interests
    travel_frequency: int = 2  # 1=rarely, 2=occasionally, 3=frequently
    expensive_hobbies: bool = False
    gambling_indicators: bool = False
    substance_use_indicators: bool = False

    # Financial Behavior Indicators
    financial_responsibility_signals: int = 0  # Count of positive signals
    financial_irresponsibility_signals: int = 0  # Count of negative signals

    # Derived Scores
    lifestyle_stability_score: float = 0.5  # 0-1 (higher = more stable/responsible)
    income_lifestyle_alignment: float = 0.5  # 0-1 (higher = lifestyle matches income)


@dataclass
class SocialConnectednessFeatures:
    """Features measuring social network and support system."""
    # Network Size & Quality
    total_followers_tier: int = 2  # 1=low, 2=medium, 3=high
    engagement_rate: float = 0.5  # 0-1
    authentic_connections: float = 0.5  # 0-1 (vs fake/bought followers)

    # Family & Relationships
    relationship_status: int = 0  # RelationshipStatus enum value
    family_presence_in_content: float = 0.5  # 0-1
    appears_stable_relationship: bool = False
    has_children: bool = False

    # Community & Support
    community_involvement: float = 0.5  # 0-1
    group_memberships: int = 0
    volunteer_charity_involvement: bool = False
    religious_community_ties: bool = False

    # Social Stability Indicators
    long_term_friendships_visible: bool = False
    local_community_ties: float = 0.5  # 0-1
    geographic_stability: float = 0.5  # 0-1 (vs frequent moves)

    # Red Flags
    social_isolation_indicators: bool = False
    conflict_drama_indicators: int = 0
    relationship_instability_signals: int = 0

    # Derived Scores
    social_support_score: float = 0.5  # 0-1 (strength of support network)
    community_rootedness_score: float = 0.5  # 0-1 (ties to local community)
    relationship_stability_score: float = 0.5  # 0-1


@dataclass
class CombinedFeatures:
    """All features combined for ML model input."""
    traditional: TraditionalFeatures
    professional: ProfessionalFeatures
    lifestyle: LifestyleFeatures
    social: SocialConnectednessFeatures

    def to_model_input(self) -> Dict[str, float]:
        """Convert to flat dict of normalized features for ML model."""
        features = {}

        # ============ TRADITIONAL FEATURES ============
        features["credit_score_normalized"] = max(0, (self.traditional.credit_score - 300) / 550)
        features["credit_history_years"] = min(self.traditional.credit_history_years / 30, 1.0)
        features["annual_income_log"] = min(self.traditional.annual_income / 500000, 1.0)
        features["employment_length_normalized"] = min(self.traditional.employment_length_months / 120, 1.0)
        features["is_self_employed"] = 1.0 if self.traditional.is_self_employed else 0.0
        features["income_verified"] = 1.0 if self.traditional.income_verified else 0.0
        features["dti_ratio"] = min(self.traditional.debt_to_income_ratio, 1.0)
        features["ltv_ratio"] = min(self.traditional.loan_to_value_ratio, 1.0)
        features["is_primary_residence"] = 1.0 if self.traditional.is_primary_residence else 0.0
        features["reserves_months_normalized"] = min(self.traditional.reserves_months / 12, 1.0)

        # ============ PROFESSIONAL FEATURES ============
        features["current_job_months_normalized"] = min(self.professional.current_job_months / 120, 1.0)
        features["total_experience_years_normalized"] = min(self.professional.total_experience_years / 30, 1.0)
        features["jobs_last_5_years_normalized"] = min(self.professional.jobs_last_5_years / 5, 1.0)
        features["career_trajectory_normalized"] = self.professional.career_trajectory / 5
        features["education_level_normalized"] = self.professional.education_level / 5
        features["has_advanced_degree"] = 1.0 if self.professional.has_advanced_degree else 0.0
        features["industry_stability"] = self.professional.industry_stability
        features["profile_completeness"] = self.professional.profile_completeness
        features["has_recommendations"] = 1.0 if self.professional.has_recommendations else 0.0
        features["connection_count_normalized"] = self.professional.connection_count_tier / 3
        features["employment_gaps_normalized"] = min(self.professional.employment_gaps / 3, 1.0)
        features["frequent_job_changes"] = 1.0 if self.professional.frequent_job_changes else 0.0
        features["profile_inconsistencies_normalized"] = min(self.professional.profile_inconsistencies / 3, 1.0)
        features["job_stability_score"] = self.professional.job_stability_score
        features["professional_credibility_score"] = self.professional.professional_credibility_score

        # ============ LIFESTYLE FEATURES ============
        features["lifestyle_level_normalized"] = self.lifestyle.lifestyle_level / 5
        features["spending_vs_income"] = self.lifestyle.apparent_spending_vs_income
        features["luxury_items_visible"] = 1.0 if self.lifestyle.luxury_items_visible else 0.0
        features["frequent_expensive_travel"] = 1.0 if self.lifestyle.frequent_expensive_travel else 0.0
        features["vehicle_tier_normalized"] = self.lifestyle.vehicle_tier / 3
        features["housing_quality_normalized"] = self.lifestyle.housing_quality_apparent / 3
        features["appears_homeowner"] = 1.0 if self.lifestyle.appears_homeowner else 0.0
        features["location_cost_of_living"] = self.lifestyle.location_cost_of_living
        features["travel_frequency_normalized"] = self.lifestyle.travel_frequency / 3
        features["expensive_hobbies"] = 1.0 if self.lifestyle.expensive_hobbies else 0.0
        features["gambling_indicators"] = 1.0 if self.lifestyle.gambling_indicators else 0.0
        features["substance_use_indicators"] = 1.0 if self.lifestyle.substance_use_indicators else 0.0
        features["financial_responsibility_signals"] = min(self.lifestyle.financial_responsibility_signals / 5, 1.0)
        features["financial_irresponsibility_signals"] = min(self.lifestyle.financial_irresponsibility_signals / 5, 1.0)
        features["lifestyle_stability_score"] = self.lifestyle.lifestyle_stability_score
        features["income_lifestyle_alignment"] = self.lifestyle.income_lifestyle_alignment

        # ============ SOCIAL CONNECTEDNESS FEATURES ============
        features["followers_tier_normalized"] = self.social.total_followers_tier / 3
        features["engagement_rate"] = self.social.engagement_rate
        features["authentic_connections"] = self.social.authentic_connections
        features["relationship_status_normalized"] = self.social.relationship_status / 4
        features["family_presence"] = self.social.family_presence_in_content
        features["stable_relationship"] = 1.0 if self.social.appears_stable_relationship else 0.0
        features["has_children"] = 1.0 if self.social.has_children else 0.0
        features["community_involvement"] = self.social.community_involvement
        features["group_memberships_normalized"] = min(self.social.group_memberships / 10, 1.0)
        features["volunteer_charity"] = 1.0 if self.social.volunteer_charity_involvement else 0.0
        features["religious_community"] = 1.0 if self.social.religious_community_ties else 0.0
        features["long_term_friendships"] = 1.0 if self.social.long_term_friendships_visible else 0.0
        features["local_community_ties"] = self.social.local_community_ties
        features["geographic_stability"] = self.social.geographic_stability
        features["social_isolation"] = 1.0 if self.social.social_isolation_indicators else 0.0
        features["conflict_drama_normalized"] = min(self.social.conflict_drama_indicators / 5, 1.0)
        features["relationship_instability_normalized"] = min(self.social.relationship_instability_signals / 5, 1.0)
        features["social_support_score"] = self.social.social_support_score
        features["community_rootedness_score"] = self.social.community_rootedness_score
        features["relationship_stability_score"] = self.social.relationship_stability_score

        return features

    def to_dict(self) -> Dict[str, Any]:
        """Convert to nested dict for serialization."""
        return {
            "traditional": asdict(self.traditional),
            "professional": asdict(self.professional),
            "lifestyle": asdict(self.lifestyle),
            "social": asdict(self.social)
        }


class FeatureExtractor:
    """
    Extracts and processes features for the risk scoring model.
    """

    # Industry stability ratings (higher = more stable)
    INDUSTRY_STABILITY = {
        "healthcare": 0.9,
        "government": 0.95,
        "education": 0.85,
        "finance": 0.8,
        "technology": 0.7,
        "consulting": 0.6,
        "retail": 0.5,
        "hospitality": 0.4,
        "entertainment": 0.45,
        "construction": 0.55,
        "manufacturing": 0.65,
        "real estate": 0.6,
        "energy": 0.7,
        "agriculture": 0.6,
        "transportation": 0.65,
        "legal": 0.85,
        "nonprofit": 0.7,
        "default": 0.5
    }

    def __init__(self, keywords_client: KeywordsAIClient = None):
        """
        Initialize the feature extractor.

        Args:
            keywords_client: Keywords AI client for profile analysis
        """
        self.keywords_client = keywords_client

    def extract_traditional_features(self, data: Dict[str, Any]) -> TraditionalFeatures:
        """
        Extract traditional underwriting features from application data.
        """
        features = TraditionalFeatures()

        # Credit
        features.credit_score = float(data.get("credit_score", 0))
        features.credit_history_years = float(data.get("credit_history_years", 0))

        # Income & Employment
        features.annual_income = float(data.get("annual_income", 0))
        features.employment_length_months = int(data.get("employment_length_months", 0))
        features.is_self_employed = bool(data.get("is_self_employed", False))
        features.income_verified = bool(data.get("income_verified", False))

        # Debt
        features.monthly_debt_payments = float(data.get("monthly_debt_payments", 0))
        if features.annual_income > 0:
            monthly_income = features.annual_income / 12
            features.debt_to_income_ratio = data.get(
                "debt_to_income_ratio",
                features.monthly_debt_payments / monthly_income if monthly_income > 0 else 0
            )
        else:
            features.debt_to_income_ratio = float(data.get("debt_to_income_ratio", 0))

        # Loan Details
        features.loan_amount = float(data.get("loan_amount", 0))
        features.property_value = float(data.get("property_value", 0))
        if features.property_value > 0:
            features.loan_to_value_ratio = data.get(
                "loan_to_value_ratio",
                features.loan_amount / features.property_value
            )
        else:
            features.loan_to_value_ratio = float(data.get("loan_to_value_ratio", 0))

        features.loan_purpose = data.get("loan_purpose", "purchase")
        features.property_type = data.get("property_type", "single_family")
        features.is_primary_residence = bool(data.get("is_primary_residence", True))

        # Assets
        features.total_assets = float(data.get("total_assets", 0))
        features.liquid_assets = float(data.get("liquid_assets", 0))
        features.reserves_months = int(data.get("reserves_months", 0))

        return features

    def extract_professional_features(self, analysis_text: str) -> ProfessionalFeatures:
        """
        Extract professional features from LinkedIn/professional profile analysis.
        """
        if not self.keywords_client:
            raise ValueError("Keywords AI client required for feature extraction")

        schema = {
            "type": "object",
            "properties": {
                "current_job_months": {"type": "integer", "description": "Months at current job"},
                "total_experience_years": {"type": "number", "description": "Total years of experience"},
                "jobs_last_5_years": {"type": "integer", "description": "Number of jobs in last 5 years"},
                "career_trajectory": {
                    "type": "string",
                    "enum": ["declining", "unstable", "stable", "growing", "rapidly_growing"]
                },
                "education_level": {
                    "type": "string",
                    "enum": ["unknown", "high_school", "associate", "bachelor", "master", "phd"]
                },
                "industry": {"type": "string", "description": "Primary industry/sector"},
                "profile_completeness": {"type": "number", "description": "0-1 scale"},
                "has_recommendations": {"type": "boolean"},
                "connection_count": {"type": "string", "enum": ["low", "medium", "high"]},
                "employment_gaps": {"type": "integer"},
                "red_flags": {"type": "array", "items": {"type": "string"}}
            }
        }

        try:
            extracted = self.keywords_client.extract_structured_data(text=analysis_text, schema=schema)
        except Exception as e:
            print(f"Warning: Could not extract professional features: {e}")
            return ProfessionalFeatures()

        return self._build_professional_features(extracted)

    def _build_professional_features(self, extracted: Dict[str, Any]) -> ProfessionalFeatures:
        """Build ProfessionalFeatures from extracted data."""
        features = ProfessionalFeatures()

        features.current_job_months = int(extracted.get("current_job_months", 0))
        features.total_experience_years = float(extracted.get("total_experience_years", 0))
        features.jobs_last_5_years = int(extracted.get("jobs_last_5_years", 1))

        trajectory_map = {
            "declining": 1, "unstable": 2, "stable": 3, "growing": 4, "rapidly_growing": 5
        }
        features.career_trajectory = trajectory_map.get(
            extracted.get("career_trajectory", "stable"), 3
        )

        education_map = {
            "unknown": 0, "high_school": 1, "associate": 2, "bachelor": 3, "master": 4, "phd": 5
        }
        features.education_level = education_map.get(
            extracted.get("education_level", "unknown"), 0
        )
        features.has_advanced_degree = features.education_level >= 4

        features.industry = extracted.get("industry", "").lower()
        features.industry_stability = self.INDUSTRY_STABILITY.get(
            features.industry, self.INDUSTRY_STABILITY["default"]
        )

        features.profile_completeness = float(extracted.get("profile_completeness", 0.5))
        features.has_recommendations = bool(extracted.get("has_recommendations", False))

        connection_map = {"low": 1, "medium": 2, "high": 3}
        features.connection_count_tier = connection_map.get(
            extracted.get("connection_count", "medium"), 2
        )

        features.employment_gaps = int(extracted.get("employment_gaps", 0))
        features.frequent_job_changes = features.jobs_last_5_years > 3
        features.profile_inconsistencies = len(extracted.get("red_flags", []))

        # Calculate derived scores
        features.job_stability_score = self._calculate_job_stability_score(features)
        features.professional_credibility_score = self._calculate_professional_credibility_score(features)

        return features

    def extract_lifestyle_features(self, analysis_text: str) -> LifestyleFeatures:
        """
        Extract lifestyle features from Instagram/Facebook/TikTok analysis.
        """
        if not self.keywords_client:
            raise ValueError("Keywords AI client required for feature extraction")

        schema = {
            "type": "object",
            "properties": {
                "lifestyle_level": {
                    "type": "string",
                    "enum": ["frugal", "modest", "comfortable", "affluent", "lavish"],
                    "description": "Apparent lifestyle/spending level"
                },
                "spending_vs_income": {
                    "type": "string",
                    "enum": ["underspending", "balanced", "overspending"],
                    "description": "Does spending appear to match typical income for their profession?"
                },
                "luxury_items_visible": {"type": "boolean", "description": "Designer goods, expensive watches, etc."},
                "frequent_expensive_travel": {"type": "boolean", "description": "Multiple luxury vacations per year"},
                "vehicle_type": {
                    "type": "string",
                    "enum": ["economy", "standard", "luxury"],
                    "description": "Type of vehicle if visible"
                },
                "housing_quality": {
                    "type": "string",
                    "enum": ["modest", "average", "upscale"],
                    "description": "Apparent housing quality"
                },
                "appears_homeowner": {"type": "boolean"},
                "travel_frequency": {
                    "type": "string",
                    "enum": ["rarely", "occasionally", "frequently"]
                },
                "expensive_hobbies": {"type": "boolean", "description": "Golf, yachting, etc."},
                "gambling_indicators": {"type": "boolean", "description": "Casino visits, betting posts"},
                "substance_use_indicators": {"type": "boolean", "description": "Excessive alcohol, drug references"},
                "financial_responsibility_signals": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Positive financial indicators (investing posts, budgeting, etc.)"
                },
                "financial_irresponsibility_signals": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Concerning financial indicators"
                }
            }
        }

        try:
            extracted = self.keywords_client.extract_structured_data(text=analysis_text, schema=schema)
        except Exception as e:
            print(f"Warning: Could not extract lifestyle features: {e}")
            return LifestyleFeatures()

        return self._build_lifestyle_features(extracted)

    def _build_lifestyle_features(self, extracted: Dict[str, Any]) -> LifestyleFeatures:
        """Build LifestyleFeatures from extracted data."""
        features = LifestyleFeatures()

        lifestyle_map = {"frugal": 1, "modest": 2, "comfortable": 3, "affluent": 4, "lavish": 5}
        features.lifestyle_level = lifestyle_map.get(
            extracted.get("lifestyle_level", "comfortable"), 3
        )

        spending_map = {"underspending": 0.2, "balanced": 0.5, "overspending": 0.8}
        features.apparent_spending_vs_income = spending_map.get(
            extracted.get("spending_vs_income", "balanced"), 0.5
        )

        features.luxury_items_visible = bool(extracted.get("luxury_items_visible", False))
        features.frequent_expensive_travel = bool(extracted.get("frequent_expensive_travel", False))

        vehicle_map = {"economy": 1, "standard": 2, "luxury": 3}
        features.vehicle_tier = vehicle_map.get(extracted.get("vehicle_type", "standard"), 2)

        housing_map = {"modest": 1, "average": 2, "upscale": 3}
        features.housing_quality_apparent = housing_map.get(
            extracted.get("housing_quality", "average"), 2
        )

        features.appears_homeowner = bool(extracted.get("appears_homeowner", False))

        travel_map = {"rarely": 1, "occasionally": 2, "frequently": 3}
        features.travel_frequency = travel_map.get(
            extracted.get("travel_frequency", "occasionally"), 2
        )

        features.expensive_hobbies = bool(extracted.get("expensive_hobbies", False))
        features.gambling_indicators = bool(extracted.get("gambling_indicators", False))
        features.substance_use_indicators = bool(extracted.get("substance_use_indicators", False))

        features.financial_responsibility_signals = len(
            extracted.get("financial_responsibility_signals", [])
        )
        features.financial_irresponsibility_signals = len(
            extracted.get("financial_irresponsibility_signals", [])
        )

        # Calculate derived scores
        features.lifestyle_stability_score = self._calculate_lifestyle_stability_score(features)
        features.income_lifestyle_alignment = self._calculate_income_lifestyle_alignment(features)

        return features

    def extract_social_features(self, analysis_text: str) -> SocialConnectednessFeatures:
        """
        Extract social connectedness features from social media analysis.
        """
        if not self.keywords_client:
            raise ValueError("Keywords AI client required for feature extraction")

        schema = {
            "type": "object",
            "properties": {
                "follower_tier": {
                    "type": "string",
                    "enum": ["low", "medium", "high"],
                    "description": "low=<500, medium=500-5000, high=>5000"
                },
                "engagement_quality": {
                    "type": "string",
                    "enum": ["low", "medium", "high"],
                    "description": "Quality of engagement on posts"
                },
                "authentic_connections": {"type": "boolean", "description": "Appear to be real connections vs bought"},
                "relationship_status": {
                    "type": "string",
                    "enum": ["unknown", "single", "in_relationship", "married", "married_with_children"]
                },
                "family_presence": {
                    "type": "string",
                    "enum": ["none", "occasional", "frequent"],
                    "description": "How often family appears in content"
                },
                "appears_stable_relationship": {"type": "boolean"},
                "has_children": {"type": "boolean"},
                "community_involvement": {
                    "type": "string",
                    "enum": ["none", "low", "medium", "high"]
                },
                "group_memberships": {"type": "integer"},
                "volunteer_charity": {"type": "boolean"},
                "religious_community": {"type": "boolean"},
                "long_term_friendships": {"type": "boolean", "description": "Evidence of long-term friendships"},
                "local_ties": {
                    "type": "string",
                    "enum": ["weak", "moderate", "strong"],
                    "description": "Ties to local community"
                },
                "geographic_stability": {"type": "boolean", "description": "Appears settled vs frequent moves"},
                "social_isolation_indicators": {"type": "boolean"},
                "conflict_indicators": {"type": "integer", "description": "Count of drama/conflict posts"},
                "relationship_instability": {"type": "integer", "description": "Count of relationship issues"}
            }
        }

        try:
            extracted = self.keywords_client.extract_structured_data(text=analysis_text, schema=schema)
        except Exception as e:
            print(f"Warning: Could not extract social features: {e}")
            return SocialConnectednessFeatures()

        return self._build_social_features(extracted)

    def _build_social_features(self, extracted: Dict[str, Any]) -> SocialConnectednessFeatures:
        """Build SocialConnectednessFeatures from extracted data."""
        features = SocialConnectednessFeatures()

        tier_map = {"low": 1, "medium": 2, "high": 3}
        features.total_followers_tier = tier_map.get(extracted.get("follower_tier", "medium"), 2)

        engagement_map = {"low": 0.2, "medium": 0.5, "high": 0.8}
        features.engagement_rate = engagement_map.get(
            extracted.get("engagement_quality", "medium"), 0.5
        )

        features.authentic_connections = 0.8 if extracted.get("authentic_connections", True) else 0.3

        relationship_map = {
            "unknown": 0, "single": 1, "in_relationship": 2, "married": 3, "married_with_children": 4
        }
        features.relationship_status = relationship_map.get(
            extracted.get("relationship_status", "unknown"), 0
        )

        family_map = {"none": 0.1, "occasional": 0.5, "frequent": 0.9}
        features.family_presence_in_content = family_map.get(
            extracted.get("family_presence", "occasional"), 0.5
        )

        features.appears_stable_relationship = bool(extracted.get("appears_stable_relationship", False))
        features.has_children = bool(extracted.get("has_children", False))

        community_map = {"none": 0.0, "low": 0.3, "medium": 0.6, "high": 0.9}
        features.community_involvement = community_map.get(
            extracted.get("community_involvement", "low"), 0.3
        )

        features.group_memberships = int(extracted.get("group_memberships", 0))
        features.volunteer_charity_involvement = bool(extracted.get("volunteer_charity", False))
        features.religious_community_ties = bool(extracted.get("religious_community", False))
        features.long_term_friendships_visible = bool(extracted.get("long_term_friendships", False))

        ties_map = {"weak": 0.2, "moderate": 0.5, "strong": 0.8}
        features.local_community_ties = ties_map.get(extracted.get("local_ties", "moderate"), 0.5)

        features.geographic_stability = 0.8 if extracted.get("geographic_stability", True) else 0.3
        features.social_isolation_indicators = bool(extracted.get("social_isolation_indicators", False))
        features.conflict_drama_indicators = int(extracted.get("conflict_indicators", 0))
        features.relationship_instability_signals = int(extracted.get("relationship_instability", 0))

        # Calculate derived scores
        features.social_support_score = self._calculate_social_support_score(features)
        features.community_rootedness_score = self._calculate_community_rootedness_score(features)
        features.relationship_stability_score = self._calculate_relationship_stability_score(features)

        return features

    # ============ DERIVED SCORE CALCULATIONS ============

    def _calculate_job_stability_score(self, features: ProfessionalFeatures) -> float:
        """Calculate job stability score (0-1, higher is more stable)."""
        score = 0.5

        # Current job tenure (up to +0.3)
        tenure_bonus = min(features.current_job_months / 60, 1.0) * 0.3
        score += tenure_bonus

        # Job hopping penalty (up to -0.3)
        if features.jobs_last_5_years > 3:
            hopping_penalty = min((features.jobs_last_5_years - 3) * 0.1, 0.3)
            score -= hopping_penalty

        # Employment gaps penalty (up to -0.2)
        gap_penalty = min(features.employment_gaps * 0.1, 0.2)
        score -= gap_penalty

        # Career trajectory bonus/penalty
        trajectory_adjustment = (features.career_trajectory - 3) * 0.05
        score += trajectory_adjustment

        return max(0.0, min(1.0, score))

    def _calculate_professional_credibility_score(self, features: ProfessionalFeatures) -> float:
        """Calculate professional credibility score (0-1)."""
        score = 0.0

        score += (features.education_level / 5) * 0.25
        score += min(features.total_experience_years / 20, 1.0) * 0.25
        score += features.profile_completeness * 0.2
        score += (features.connection_count_tier / 3) * 0.15
        if features.has_recommendations:
            score += 0.1
        score += features.industry_stability * 0.05

        return max(0.0, min(1.0, score))

    def _calculate_lifestyle_stability_score(self, features: LifestyleFeatures) -> float:
        """Calculate lifestyle stability score (0-1, higher = more stable/responsible)."""
        score = 0.5

        # Gambling and substance penalties
        if features.gambling_indicators:
            score -= 0.2
        if features.substance_use_indicators:
            score -= 0.15

        # Overspending penalty
        if features.apparent_spending_vs_income > 0.6:
            score -= (features.apparent_spending_vs_income - 0.6) * 0.5

        # Financial signals
        score += min(features.financial_responsibility_signals * 0.05, 0.2)
        score -= min(features.financial_irresponsibility_signals * 0.05, 0.2)

        # Homeowner bonus
        if features.appears_homeowner:
            score += 0.1

        return max(0.0, min(1.0, score))

    def _calculate_income_lifestyle_alignment(self, features: LifestyleFeatures) -> float:
        """Calculate how well lifestyle aligns with apparent income (0-1)."""
        # Start with inverse of spending vs income
        alignment = 1.0 - abs(features.apparent_spending_vs_income - 0.5) * 2

        # Penalize luxury indicators if lifestyle seems beyond means
        if features.luxury_items_visible and features.apparent_spending_vs_income > 0.6:
            alignment -= 0.2
        if features.frequent_expensive_travel and features.apparent_spending_vs_income > 0.6:
            alignment -= 0.15

        return max(0.0, min(1.0, alignment))

    def _calculate_social_support_score(self, features: SocialConnectednessFeatures) -> float:
        """Calculate strength of social support network (0-1)."""
        score = 0.0

        score += features.family_presence_in_content * 0.2
        score += features.community_involvement * 0.2
        if features.appears_stable_relationship:
            score += 0.15
        if features.long_term_friendships_visible:
            score += 0.15
        if features.volunteer_charity_involvement:
            score += 0.1
        score += features.authentic_connections * 0.1

        # Penalties
        if features.social_isolation_indicators:
            score -= 0.2
        score -= min(features.conflict_drama_indicators * 0.05, 0.15)

        return max(0.0, min(1.0, score))

    def _calculate_community_rootedness_score(self, features: SocialConnectednessFeatures) -> float:
        """Calculate ties to local community (0-1)."""
        score = 0.0

        score += features.local_community_ties * 0.3
        score += features.geographic_stability * 0.25
        score += features.community_involvement * 0.2
        score += min(features.group_memberships / 10, 1.0) * 0.15
        if features.religious_community_ties:
            score += 0.1

        return max(0.0, min(1.0, score))

    def _calculate_relationship_stability_score(self, features: SocialConnectednessFeatures) -> float:
        """Calculate relationship stability (0-1)."""
        score = 0.5

        if features.appears_stable_relationship:
            score += 0.2
        if features.relationship_status >= 3:  # Married
            score += 0.1
        if features.has_children:
            score += 0.05

        # Penalties
        score -= min(features.relationship_instability_signals * 0.1, 0.3)
        if features.social_isolation_indicators:
            score -= 0.1

        return max(0.0, min(1.0, score))

    # ============ MAIN EXTRACTION METHOD ============

    def extract_all_features(
        self,
        traditional_data: Dict[str, Any],
        professional_analysis: str = None,
        lifestyle_analysis: str = None,
        social_analysis: str = None
    ) -> CombinedFeatures:
        """
        Extract all features from available data sources.

        Args:
            traditional_data: Standard loan application data
            professional_analysis: LinkedIn/professional profile analysis text
            lifestyle_analysis: Instagram/lifestyle profile analysis text
            social_analysis: Social connectedness analysis text (can be same as lifestyle)

        Returns:
            CombinedFeatures with all extracted features
        """
        # Extract traditional features
        traditional = self.extract_traditional_features(traditional_data)

        # Extract professional features
        if professional_analysis and self.keywords_client:
            professional = self.extract_professional_features(professional_analysis)
        else:
            professional = ProfessionalFeatures()

        # Extract lifestyle features
        if lifestyle_analysis and self.keywords_client:
            lifestyle = self.extract_lifestyle_features(lifestyle_analysis)
        else:
            lifestyle = LifestyleFeatures()

        # Extract social features
        if social_analysis and self.keywords_client:
            social = self.extract_social_features(social_analysis)
        elif lifestyle_analysis and self.keywords_client:
            # Use lifestyle analysis if no separate social analysis
            social = self.extract_social_features(lifestyle_analysis)
        else:
            social = SocialConnectednessFeatures()

        return CombinedFeatures(
            traditional=traditional,
            professional=professional,
            lifestyle=lifestyle,
            social=social
        )


def create_sample_application() -> Dict[str, Any]:
    """Create a sample loan application for testing."""
    return {
        "credit_score": 720,
        "credit_history_years": 12,
        "annual_income": 95000,
        "employment_length_months": 36,
        "is_self_employed": False,
        "income_verified": True,
        "monthly_debt_payments": 1500,
        "loan_amount": 350000,
        "property_value": 450000,
        "loan_purpose": "purchase",
        "property_type": "single_family",
        "is_primary_residence": True,
        "total_assets": 120000,
        "liquid_assets": 80000,
        "reserves_months": 6
    }


if __name__ == "__main__":
    print("Testing Feature Extractor...")

    extractor = FeatureExtractor()

    # Test traditional features
    sample_data = create_sample_application()
    traditional = extractor.extract_traditional_features(sample_data)
    print("\nTraditional Features:")
    print(f"  Credit Score: {traditional.credit_score}")
    print(f"  DTI Ratio: {traditional.debt_to_income_ratio:.2%}")
    print(f"  LTV Ratio: {traditional.loan_to_value_ratio:.2%}")

    # Test with mock features
    professional = ProfessionalFeatures(
        current_job_months=36,
        total_experience_years=10,
        jobs_last_5_years=2,
        career_trajectory=4,
        education_level=3,
        industry_stability=0.7,
        profile_completeness=0.85,
        has_recommendations=True,
        connection_count_tier=3
    )
    professional.job_stability_score = extractor._calculate_job_stability_score(professional)
    professional.professional_credibility_score = extractor._calculate_professional_credibility_score(professional)

    lifestyle = LifestyleFeatures(
        lifestyle_level=3,
        apparent_spending_vs_income=0.5,
        appears_homeowner=True,
        financial_responsibility_signals=2
    )
    lifestyle.lifestyle_stability_score = extractor._calculate_lifestyle_stability_score(lifestyle)
    lifestyle.income_lifestyle_alignment = extractor._calculate_income_lifestyle_alignment(lifestyle)

    social = SocialConnectednessFeatures(
        total_followers_tier=2,
        relationship_status=3,
        appears_stable_relationship=True,
        community_involvement=0.6,
        long_term_friendships_visible=True
    )
    social.social_support_score = extractor._calculate_social_support_score(social)
    social.community_rootedness_score = extractor._calculate_community_rootedness_score(social)
    social.relationship_stability_score = extractor._calculate_relationship_stability_score(social)

    print("\nProfessional Features:")
    print(f"  Job Stability Score: {professional.job_stability_score:.2f}")
    print(f"  Professional Credibility: {professional.professional_credibility_score:.2f}")

    print("\nLifestyle Features:")
    print(f"  Lifestyle Stability Score: {lifestyle.lifestyle_stability_score:.2f}")
    print(f"  Income-Lifestyle Alignment: {lifestyle.income_lifestyle_alignment:.2f}")

    print("\nSocial Features:")
    print(f"  Social Support Score: {social.social_support_score:.2f}")
    print(f"  Community Rootedness: {social.community_rootedness_score:.2f}")
    print(f"  Relationship Stability: {social.relationship_stability_score:.2f}")

    # Combined features
    combined = CombinedFeatures(
        traditional=traditional,
        professional=professional,
        lifestyle=lifestyle,
        social=social
    )
    model_input = combined.to_model_input()

    print(f"\nTotal Model Input Features: {len(model_input)}")
    print("\nSample features:")
    for i, (key, value) in enumerate(sorted(model_input.items())):
        if i < 10:
            print(f"  {key}: {value:.3f}")
    print("  ...")
