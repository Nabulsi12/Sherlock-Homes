"""
Loan Application Endpoints
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from app.models.schemas import (
    LoanApplicationRequest,
    LoanApplicationResponse,
    ApplicationListResponse,
    ApplicationSummary,
    StatusUpdateRequest,
    StatusUpdateResponse
)
from app.services.ai_agent import AIAgentService
from app.storage import (
    save_application,
    get_application,
    list_applications,
    update_application_status
)
from app.utils.logger import logger
import uuid
from datetime import datetime
import time

router = APIRouter()


@router.post("/loan-applications", response_model=LoanApplicationResponse)
async def create_loan_application(
    application: LoanApplicationRequest,
    background_tasks: BackgroundTasks
):
    """
    Submit a new loan application for analysis

    Analyzes traditional Big 3 + Fourth Factor:
    1. Income (from application data)
    2. Credit Score (from application data)
    3. Collateral/Property Value (from application data)
    4. Social Media Insights (from profile analysis - the fourth factor)

    This endpoint:
    1. Validates the application data
    2. Gathers social media insights (Fourth Factor)
    3. Extracts 60+ ML features
    4. Performs risk assessment based on Big 3 + Fourth Factor
    5. Checks compliance with Fannie Mae/Freddie Mac guidelines
    """
    start_time = time.time()
    application_id = f"LN-{datetime.now().year}-{str(uuid.uuid4())[:8]}"

    logger.info(f"Processing loan application {application_id} for {application.applicant.full_name}")

    try:
        # Initialize AI Agent Service
        ai_service = AIAgentService()

        # Run comprehensive analysis (Big 3 + Fourth Factor)
        analysis_result = await ai_service.analyze_loan_application(
            application_id=application_id,
            application=application
        )

        processing_time = time.time() - start_time

        # Calculate LTV ratio
        ltv_ratio = (application.loan_details.loan_amount / application.property_info.estimated_value) * 100

        # Get risk assessment
        risk_assessment = analysis_result.get("risk_assessment")
        ai_summary = analysis_result.get("ai_summary", {})

        # Use AI-determined risk score if available, otherwise fall back to calculated score
        try:
            ai_risk_score = ai_summary.get("ai_risk_score")
            if ai_risk_score is not None and isinstance(ai_risk_score, (int, float)):
                risk_score = int(ai_risk_score)
                logger.info(f"Using AI-determined risk score: {risk_score} (calculated was {risk_assessment.risk_score if risk_assessment else 'N/A'})")
            else:
                # Fallback to calculated score
                risk_score = risk_assessment.risk_score if risk_assessment else 50
                logger.info(f"Using calculated risk score: {risk_score} (AI score not available)")
        except Exception as e:
            # Fallback to calculated score on any error
            risk_score = risk_assessment.risk_score if risk_assessment else 50
            logger.warning(f"Error extracting AI risk score: {str(e)}. Using calculated score: {risk_score}")

        # Determine status based on risk score
        if risk_score <= 35:
            status = "approved"
        elif risk_score <= 60:
            status = "review"
        else:
            status = "declined"

        # Update risk_assessment with AI-determined score if different
        if risk_assessment and ai_summary.get("ai_risk_score") is not None:
            # Create updated risk assessment with AI score
            risk_assessment.risk_score = risk_score

        response = LoanApplicationResponse(
            application_id=application_id,
            status=status,
            submitted_at=datetime.utcnow(),
            processed_at=datetime.utcnow(),
            risk_assessment=risk_assessment,
            compliance_check=analysis_result.get("compliance_check"),
            fourth_factor=analysis_result.get("fourth_factor"),
            ml_features=analysis_result.get("ml_features"),
            ai_summary=ai_summary if ai_summary else None,
            processing_time_seconds=round(processing_time, 2)
        )

        # Save to storage
        save_application(application_id, {
            "application_id": application_id,
            "status": status,
            "borrower_name": application.applicant.full_name,
            "loan_type": application.loan_details.loan_type.value,
            "loan_amount": application.loan_details.loan_amount,
            "property_value": application.property_info.estimated_value,
            "ltv_ratio": round(ltv_ratio, 1),
            "risk_score": risk_score,
            "credit_score": application.applicant.credit_score,
            "annual_income": application.applicant.annual_income,
            "dti_ratio": risk_assessment.dti_ratio if risk_assessment else 0,
            "ai_summary": ai_summary.get("summary", ""),
            "ai_risk_score": ai_summary.get("ai_risk_score"),
            "submitted_at": datetime.utcnow().isoformat(),
            "processed_at": datetime.utcnow().isoformat(),
            "full_response": response.dict()
        })

        logger.info(f"Successfully processed application {application_id} in {processing_time:.2f}s")

        return response

    except Exception as e:
        logger.error(f"Error processing application {application_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing loan application: {str(e)}"
        )


@router.get("/loan-applications/{application_id}")
async def get_loan_application(application_id: str):
    """
    Retrieve a loan application by ID
    """
    app = get_application(application_id)

    if not app:
        raise HTTPException(
            status_code=404,
            detail=f"Application {application_id} not found"
        )

    # Return full response if available, otherwise return stored data
    if "full_response" in app:
        return app["full_response"]

    return ApplicationSummary(
        application_id=app["application_id"],
        status=app["status"],
        borrower_name=app["borrower_name"],
        loan_type=app["loan_type"],
        loan_amount=app["loan_amount"],
        property_value=app["property_value"],
        ltv_ratio=app["ltv_ratio"],
        risk_score=app["risk_score"],
        credit_score=app.get("credit_score"),
        submitted_at=app.get("submitted_at"),
        processed_at=app.get("processed_at")
    )


@router.get("/loan-applications", response_model=ApplicationListResponse)
async def list_loan_applications(
    skip: int = 0,
    limit: int = 10,
    status: str = None
):
    """
    List loan applications with optional filtering

    Parameters:
    - skip: Number of records to skip (pagination)
    - limit: Maximum number of records to return
    - status: Filter by status (approved, pending, review, declined)
    """
    apps, total = list_applications(skip=skip, limit=limit, status=status)

    summaries = [
        ApplicationSummary(
            application_id=app["application_id"],
            status=app["status"],
            borrower_name=app["borrower_name"],
            loan_type=app["loan_type"],
            loan_amount=app["loan_amount"],
            property_value=app["property_value"],
            ltv_ratio=app["ltv_ratio"],
            risk_score=app["risk_score"],
            credit_score=app.get("credit_score"),
            submitted_at=app.get("submitted_at"),
            processed_at=app.get("processed_at")
        )
        for app in apps
    ]

    return ApplicationListResponse(
        applications=summaries,
        total=total,
        skip=skip,
        limit=limit
    )


@router.patch("/loan-applications/{application_id}/status", response_model=StatusUpdateResponse)
async def update_status(
    application_id: str,
    request: StatusUpdateRequest
):
    """
    Update the status of a loan application

    Valid statuses: approved, pending, review, declined
    """
    # Validate status
    valid_statuses = {"approved", "pending", "review", "declined"}
    if request.status not in valid_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
        )

    app = get_application(application_id)
    if not app:
        raise HTTPException(
            status_code=404,
            detail=f"Application {application_id} not found"
        )

    old_status = app["status"]
    updated = update_application_status(application_id, request.status)

    if not updated:
        raise HTTPException(
            status_code=500,
            detail="Failed to update application status"
        )

    logger.info(f"Application {application_id} status changed: {old_status} -> {request.status}")

    return StatusUpdateResponse(
        application_id=application_id,
        old_status=old_status,
        new_status=request.status,
        updated_at=datetime.utcnow()
    )
