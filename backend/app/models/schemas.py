"""
Pydantic Schemas for Request/Response Models
"""

from pydantic import BaseModel, Field, EmailStr, HttpUrl
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class LoanType(str, Enum):
    """Loan type enumeration"""
    CONVENTIONAL_30 = "30-Year Fixed Conventional"
    CONVENTIONAL_15 = "15-Year Fixed Conventional"
    FHA_30 = "30-Year Fixed FHA"
    VA_30 = "30-Year Fixed VA"
    ARM_7_1 = "7/1 ARM"
    ARM_5_1 = "5/1 ARM"


class LoanPurpose(str, Enum):
    """Loan purpose enumeration"""
    PURCHASE = "Purchase"
    REFINANCE_RATE = "Refinance - Rate/Term"
    REFINANCE_CASHOUT = "Refinance - Cash Out"


class PropertyType(str, Enum):
    """Property type enumeration"""
    SINGLE_FAMILY = "Single Family Detached"
    TOWNHOUSE = "Townhouse"
    CONDO = "Condo"
    PUD = "PUD"


class Occupancy(str, Enum):
    """Occupancy type enumeration"""
    PRIMARY = "Primary Residence"
    SECOND_HOME = "Second Home"
    INVESTMENT = "Investment Property"


class RiskLevel(str, Enum):
    """Risk level enumeration"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ApplicantInfo(BaseModel):
    """Loan applicant information"""
    full_name: str = Field(..., description="Full legal name")
    email: EmailStr = Field(..., description="Email address")
    phone: str = Field(..., description="Phone number")
    ssn: Optional[str] = Field(None, description="Social Security Number")
    date_of_birth: Optional[str] = Field(None, description="Date of birth")

    # Employment
    employer_name: Optional[str] = None
    annual_income: float = Field(..., description="Annual income in dollars")
    years_employed: Optional[float] = None

    # Online presence for AI data gathering
    linkedin_url: Optional[HttpUrl] = None
    facebook_url: Optional[HttpUrl] = None
    instagram_handle: Optional[str] = None
    twitter_handle: Optional[str] = None
    personal_website: Optional[HttpUrl] = None
    other_social_links: Optional[str] = None

    # Credit
    credit_score: int = Field(..., ge=300, le=850, description="Credit score")


class PropertyInfo(BaseModel):
    """Property information"""
    address: str = Field(..., description="Full property address")
    estimated_value: float = Field(..., description="Estimated property value")
    property_type: PropertyType
    occupancy: Occupancy


class LoanDetails(BaseModel):
    """Loan details"""
    loan_amount: float = Field(..., description="Requested loan amount")
    loan_type: LoanType
    loan_purpose: LoanPurpose
    down_payment: Optional[float] = Field(None, description="Down payment amount")


class DocumentInfo(BaseModel):
    """Uploaded document information"""
    document_type: str = Field(..., description="Type of document (W-2, 1099, etc.)")
    file_name: str
    file_path: Optional[str] = None
    upload_date: datetime = Field(default_factory=datetime.utcnow)


class LoanApplicationRequest(BaseModel):
    """Loan application request schema"""
    applicant: ApplicantInfo
    property_info: PropertyInfo
    loan_details: LoanDetails
    documents: Optional[List[DocumentInfo]] = []
    additional_notes: Optional[str] = None


class ComplianceCheck(BaseModel):
    """Compliance verification result"""
    compliant: bool
    guidelines_checked: List[str] = []
    violations: List[str] = []
    warnings: List[str] = []
    fannie_mae_compliant: bool
    freddie_mac_compliant: bool
    details: Optional[str] = None


class RiskFactors(BaseModel):
    """Individual risk factors"""
    credit_score_risk: str
    dti_ratio_risk: str
    ltv_ratio_risk: str
    employment_stability_risk: str
    income_verification_risk: str
    property_risk: str


class RiskAssessment(BaseModel):
    """Risk assessment result"""
    risk_score: int = Field(..., ge=0, le=100, description="Risk score 0-100")
    risk_level: RiskLevel
    dti_ratio: Optional[float] = Field(None, description="Debt-to-Income ratio")
    ltv_ratio: Optional[float] = Field(None, description="Loan-to-Value ratio")
    risk_factors: Optional[RiskFactors] = None
    recommendation: str
    estimated_interest_rate: Optional[float] = None
    estimated_monthly_payment: Optional[float] = None


class GatheredData(BaseModel):
    """Data gathered by AI agent (compatible with Joseph's profile_analyzer)"""
    sources: List[str] = []

    # Profile analysis summaries (from Joseph's profile_analyzer)
    professional_summary: Optional[str] = None
    lifestyle_summary: Optional[str] = None
    social_summary: Optional[str] = None

    # Risk indicators (from Joseph's profile_analyzer)
    red_flags: List[str] = []
    positive_indicators: List[str] = []

    # Legacy fields (for backward compatibility)
    employment_verification: Optional[Dict[str, Any]] = None
    income_verification: Optional[Dict[str, Any]] = None
    credit_history: Optional[Dict[str, Any]] = None
    public_records: Optional[Dict[str, Any]] = None
    social_media_insights: Optional[Dict[str, Any]] = None
    additional_findings: Optional[str] = None


class LoanApplicationResponse(BaseModel):
    """
    Loan application response schema

    Returns analysis based on Big 3 + Fourth Factor:
    - Big 3: Income, Credit Score, Collateral/Property Value (in risk_assessment)
    - Fourth Factor: Social media insights (in fourth_factor)
    """
    application_id: str
    status: str
    submitted_at: datetime = Field(default_factory=datetime.utcnow)
    processed_at: Optional[datetime] = None

    # Traditional Big 3 Analysis
    risk_assessment: Optional[RiskAssessment] = None
    compliance_check: Optional[ComplianceCheck] = None

    # Fourth Factor: Social Media Insights
    fourth_factor: Optional[GatheredData] = Field(
        None,
        description="Social media insights and profile analysis - the fourth factor beyond Big 3"
    )

    # ML Features (60+ normalized features for future model training)
    ml_features: Optional[Dict[str, float]] = Field(
        None,
        description="Machine learning features extracted from application and profiles"
    )

    # AI Assessment Summary
    ai_summary: Optional[Dict[str, Any]] = Field(
        None,
        description="AI-generated assessment with ai_risk_score (0-100) and summary text"
    )

    # Processing metadata
    processing_time_seconds: Optional[float] = None


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    version: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    services: Dict[str, str] = {}


# ============ Quick Assessment Schemas ============

class QuickAssessmentRequest(BaseModel):
    """Quick pre-qualification request - simplified form"""
    borrower_name: str = Field(..., description="Full legal name")
    credit_score: int = Field(..., ge=300, le=850, description="Credit score")
    annual_income: float = Field(..., description="Annual income in dollars")
    loan_amount: float = Field(..., description="Requested loan amount")
    property_value: float = Field(..., description="Property value")
    loan_type: LoanType = Field(..., description="Type of loan")
    monthly_debts: Optional[float] = Field(0, description="Monthly debt payments")


class QuickAssessmentResponse(BaseModel):
    """Quick pre-qualification response"""
    risk_score: int = Field(..., ge=0, le=100)
    risk_level: RiskLevel
    dti_ratio: float
    ltv_ratio: float
    recommendation: str
    likely_to_qualify: bool
    estimated_interest_rate: Optional[float] = None
    estimated_monthly_payment: Optional[float] = None
    factors: Dict[str, str] = {}


# ============ Dashboard Stats Schemas ============

class DashboardStats(BaseModel):
    """Dashboard statistics"""
    total_applications: int
    approved: int
    pending: int
    declined: int
    under_review: int
    approval_rate: float
    average_risk_score: float
    average_processing_time: float


# ============ Application List Schemas ============

class ApplicationSummary(BaseModel):
    """Summary of a loan application for list view"""
    application_id: str
    status: str
    borrower_name: str
    loan_type: str
    loan_amount: float
    property_value: float
    ltv_ratio: float
    risk_score: int
    credit_score: Optional[int] = None
    submitted_at: Optional[str] = None
    processed_at: Optional[str] = None


class ApplicationListResponse(BaseModel):
    """Response for listing applications"""
    applications: List[ApplicationSummary]
    total: int
    skip: int
    limit: int


# ============ Status Update Schemas ============

class StatusUpdateRequest(BaseModel):
    """Request to update application status"""
    status: str = Field(..., description="New status: approved, pending, review, declined")
    notes: Optional[str] = None


class StatusUpdateResponse(BaseModel):
    """Response after status update"""
    application_id: str
    old_status: str
    new_status: str
    updated_at: datetime


# ============ Document Upload Schemas ============

class DocumentUploadResponse(BaseModel):
    """Response after document upload"""
    document_id: str
    document_type: str
    file_name: str
    file_size: int
    upload_date: datetime
    status: str = "uploaded"
