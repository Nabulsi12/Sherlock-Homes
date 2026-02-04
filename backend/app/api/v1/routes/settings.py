"""
User Settings Endpoints
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime

from app.api.v1.routes.auth import get_current_user

router = APIRouter()

# In-memory settings storage (use database in production)
_user_settings = {}

# Default settings template
DEFAULT_SETTINGS = {
    "notifications": {
        "email_on_approval": True,
        "email_on_decline": True,
        "email_on_review": True,
        "email_daily_summary": False,
        "push_notifications": True
    },
    "display": {
        "theme": "light",  # light, dark, auto
        "dashboard_layout": "grid",  # grid, list
        "applications_per_page": 10,
        "show_risk_scores": True,
        "show_ai_insights": True
    },
    "underwriting": {
        "auto_approve_threshold": 30,  # Risk score below this = auto approve
        "auto_decline_threshold": 75,  # Risk score above this = auto decline
        "require_manual_review": True,
        "include_social_analysis": True,
        "compliance_check_level": "standard"  # basic, standard, strict
    },
    "api": {
        "keywords_ai_enabled": True,
        "perplexity_enabled": True,
        "rate_limit": 100  # requests per minute
    },
    "privacy": {
        "data_retention_days": 365,
        "anonymize_reports": False,
        "share_analytics": True
    }
}


# ============ Schemas ============

class NotificationSettings(BaseModel):
    """Notification preferences"""
    email_on_approval: Optional[bool] = True
    email_on_decline: Optional[bool] = True
    email_on_review: Optional[bool] = True
    email_daily_summary: Optional[bool] = False
    push_notifications: Optional[bool] = True


class DisplaySettings(BaseModel):
    """Display preferences"""
    theme: Optional[str] = "light"
    dashboard_layout: Optional[str] = "grid"
    applications_per_page: Optional[int] = Field(10, ge=5, le=50)
    show_risk_scores: Optional[bool] = True
    show_ai_insights: Optional[bool] = True


class UnderwritingSettings(BaseModel):
    """Underwriting configuration"""
    auto_approve_threshold: Optional[int] = Field(30, ge=0, le=100)
    auto_decline_threshold: Optional[int] = Field(75, ge=0, le=100)
    require_manual_review: Optional[bool] = True
    include_social_analysis: Optional[bool] = True
    compliance_check_level: Optional[str] = "standard"


class APISettings(BaseModel):
    """API configuration"""
    keywords_ai_enabled: Optional[bool] = True
    perplexity_enabled: Optional[bool] = True
    rate_limit: Optional[int] = Field(100, ge=10, le=1000)


class PrivacySettings(BaseModel):
    """Privacy settings"""
    data_retention_days: Optional[int] = Field(365, ge=30, le=730)
    anonymize_reports: Optional[bool] = False
    share_analytics: Optional[bool] = True


class UserSettings(BaseModel):
    """Complete user settings"""
    notifications: Optional[NotificationSettings] = None
    display: Optional[DisplaySettings] = None
    underwriting: Optional[UnderwritingSettings] = None
    api: Optional[APISettings] = None
    privacy: Optional[PrivacySettings] = None


class SettingsResponse(BaseModel):
    """Settings response"""
    user_id: str
    settings: Dict[str, Any]
    updated_at: str


class SettingsUpdateRequest(BaseModel):
    """Partial settings update"""
    notifications: Optional[NotificationSettings] = None
    display: Optional[DisplaySettings] = None
    underwriting: Optional[UnderwritingSettings] = None
    api: Optional[APISettings] = None
    privacy: Optional[PrivacySettings] = None


# ============ Helper Functions ============

def get_user_settings(user_id: str) -> dict:
    """Get settings for a user, creating defaults if needed"""
    if user_id not in _user_settings:
        _user_settings[user_id] = {
            "settings": DEFAULT_SETTINGS.copy(),
            "updated_at": datetime.utcnow().isoformat()
        }
    return _user_settings[user_id]


def deep_merge(base: dict, updates: dict) -> dict:
    """Deep merge two dictionaries"""
    result = base.copy()
    for key, value in updates.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        elif value is not None:
            result[key] = value
    return result


# ============ Endpoints ============

@router.get("/settings", response_model=SettingsResponse)
async def get_settings(current_user: dict = Depends(get_current_user)):
    """
    Get current user's settings
    """
    user_id = current_user["user_id"]
    user_settings = get_user_settings(user_id)

    return SettingsResponse(
        user_id=user_id,
        settings=user_settings["settings"],
        updated_at=user_settings["updated_at"]
    )


@router.put("/settings", response_model=SettingsResponse)
async def update_settings(
    updates: SettingsUpdateRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Update user settings (partial update supported)
    """
    user_id = current_user["user_id"]
    current_settings = get_user_settings(user_id)

    # Convert updates to dict, excluding None values
    update_dict = {}
    if updates.notifications:
        update_dict["notifications"] = updates.notifications.dict(exclude_none=True)
    if updates.display:
        update_dict["display"] = updates.display.dict(exclude_none=True)
    if updates.underwriting:
        update_dict["underwriting"] = updates.underwriting.dict(exclude_none=True)
    if updates.api:
        update_dict["api"] = updates.api.dict(exclude_none=True)
    if updates.privacy:
        update_dict["privacy"] = updates.privacy.dict(exclude_none=True)

    # Merge updates into current settings
    merged = deep_merge(current_settings["settings"], update_dict)

    # Validate underwriting thresholds
    if merged["underwriting"]["auto_approve_threshold"] >= merged["underwriting"]["auto_decline_threshold"]:
        raise HTTPException(
            status_code=400,
            detail="Auto-approve threshold must be less than auto-decline threshold"
        )

    # Save updated settings
    _user_settings[user_id] = {
        "settings": merged,
        "updated_at": datetime.utcnow().isoformat()
    }

    return SettingsResponse(
        user_id=user_id,
        settings=merged,
        updated_at=_user_settings[user_id]["updated_at"]
    )


@router.post("/settings/reset")
async def reset_settings(current_user: dict = Depends(get_current_user)):
    """
    Reset settings to defaults
    """
    user_id = current_user["user_id"]

    _user_settings[user_id] = {
        "settings": DEFAULT_SETTINGS.copy(),
        "updated_at": datetime.utcnow().isoformat()
    }

    return {
        "message": "Settings reset to defaults",
        "updated_at": _user_settings[user_id]["updated_at"]
    }


@router.get("/settings/defaults")
async def get_default_settings():
    """
    Get default settings template (no auth required)
    """
    return {
        "defaults": DEFAULT_SETTINGS,
        "description": {
            "notifications": "Email and push notification preferences",
            "display": "UI display preferences",
            "underwriting": "Automated underwriting thresholds and rules",
            "api": "External API integrations",
            "privacy": "Data privacy and retention settings"
        }
    }


# ============ Specific Setting Updates ============

@router.put("/settings/notifications", response_model=SettingsResponse)
async def update_notification_settings(
    notifications: NotificationSettings,
    current_user: dict = Depends(get_current_user)
):
    """
    Update only notification settings
    """
    return await update_settings(
        SettingsUpdateRequest(notifications=notifications),
        current_user
    )


@router.put("/settings/display", response_model=SettingsResponse)
async def update_display_settings(
    display: DisplaySettings,
    current_user: dict = Depends(get_current_user)
):
    """
    Update only display settings
    """
    return await update_settings(
        SettingsUpdateRequest(display=display),
        current_user
    )


@router.put("/settings/underwriting", response_model=SettingsResponse)
async def update_underwriting_settings(
    underwriting: UnderwritingSettings,
    current_user: dict = Depends(get_current_user)
):
    """
    Update only underwriting settings
    """
    return await update_settings(
        SettingsUpdateRequest(underwriting=underwriting),
        current_user
    )


@router.put("/settings/theme")
async def update_theme(
    theme: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Quick theme toggle endpoint
    """
    if theme not in ["light", "dark", "auto"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid theme. Must be: light, dark, or auto"
        )

    return await update_settings(
        SettingsUpdateRequest(display=DisplaySettings(theme=theme)),
        current_user
    )
