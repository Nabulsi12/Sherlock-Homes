# Refactoring Plan - Integrating Joseph's Framework

## Summary

Joseph has built a sophisticated ML-based risk assessment framework. This document outlines how to integrate it with the existing FastAPI backend.

## Joseph's Framework Components

### 1. keywords_client.py ✅ COPIED
- **Location**: `backend/app/services/keywords_client.py`
- **Purpose**: Keywords AI client using OpenAI-compatible API
- **Key Features**:
  - Uses `requests` library (not anthropic SDK)
  - `KEYWORDS_API_KEY` env variable
  - Chat completions interface
  - Structured data extraction
  - Profile analysis support

### 2. feature_extractor.py ✅ COPIED
- **Location**: `backend/app/services/feature_extractor.py`
- **Purpose**: Extract 60+ ML features from loan applications and profiles
- **Key Classes**:
  - `TraditionalFeatures` - Standard underwriting data
  - `ProfessionalFeatures` - LinkedIn/career analysis
  - `LifestyleFeatures` - Instagram/spending patterns
  - `SocialConnectednessFeatures` - Social network strength
  - `CombinedFeatures` - All features with ML normalization

### 3. profile_analyzer.py ✅ COPIED
- **Location**: `backend/app/services/profile_analyzer.py`
- **Purpose**: Analyze social media profiles using Perplexity API
- **Supports**: LinkedIn, Instagram, Twitter, Facebook, TikTok
- **Requires**: `PERPLEXITY_API_KEY`

## Required Changes

### 1. Environment Variables

**OLD (.env)**:
```env
KEYWORDS_AI_API_KEY=S3eiYOsi.HPOo2XHIHSisMPVShybz3xwGJrT0S7zr
KEYWORDS_AI_BASE_URL=https://api.keywordsai.co/api/v1
```

**NEW (.env)**: ✅ UPDATED
```env
KEYWORDS_API_KEY=S3eiYOsi.HPOo2XHIHSisMPVShybz3xwGJrT0S7zr
PERPLEXITY_API_KEY=your_perplexity_key_here
```

### 2. Config Changes Needed

**File**: `backend/app/config.py`

**REPLACE**:
```python
KEYWORDS_AI_API_KEY: str
KEYWORDS_AI_BASE_URL: str = "https://api.keywordsai.co/api/v1"
```

**WITH**:
```python
KEYWORDS_API_KEY: str  # Matches Joseph's naming
PERPLEXITY_API_KEY: Optional[str] = None  # For profile analysis
```

### 3. Services to Refactor

#### A. DELETE: `backend/app/services/data_gatherer.py` ❌
**Why**: Replaced by `profile_analyzer.py` which actually scrapes profiles

#### B. REFACTOR: `backend/app/services/ai_agent.py` 🔄
**Changes Needed**:
1. Import Joseph's classes:
   ```python
   from app.services.keywords_client import KeywordsAIClient
   from app.services.feature_extractor import FeatureExtractor, CombinedFeatures
   from app.services.profile_analyzer import analyze_profile, analyze_multiple_profiles
   ```

2. Replace anthropic client:
   ```python
   # OLD
   self.client = anthropic.Anthropic(
       api_key=settings.KEYWORDS_AI_API_KEY,
       base_url=settings.KEYWORDS_AI_BASE_URL
   )

   # NEW
   self.client = KeywordsAIClient(api_key=settings.KEYWORDS_API_KEY)
   self.feature_extractor = FeatureExtractor(keywords_client=self.client)
   ```

3. Update data gathering to use profile_analyzer:
   ```python
   # OLD
   gathered_data = await self.data_gatherer.gather_applicant_data(application)

   # NEW
   profile_urls = []
   if application.applicant.linkedin_url:
       profile_urls.append(str(application.applicant.linkedin_url))
   if application.applicant.instagram_url:
       profile_urls.append(str(application.applicant.instagram_url))

   if profile_urls:
       multi_analysis = analyze_multiple_profiles(profile_urls)
       # Extract features from analysis
       features = self.feature_extractor.extract_all_features(
           traditional_data=application_to_dict(application),
           professional_analysis=multi_analysis.profiles[0].raw_analysis if len(multi_analysis.profiles) > 0 else None,
           lifestyle_analysis=multi_analysis.profiles[1].raw_analysis if len(multi_analysis.profiles) > 1 else None
       )
   else:
       # No profiles, use traditional data only
       features = self.feature_extractor.extract_all_features(
           traditional_data=application_to_dict(application)
       )
   ```

#### C. SIMPLIFY: `backend/app/services/risk_calculator.py` 🔄
**Changes Needed**:
1. Keep the basic calculations (DTI, LTV) as utilities
2. Remove complex risk scoring (Joseph's feature_extractor handles this better)
3. Use feature_extractor's normalized features for ML model

#### D. UPDATE: `backend/app/services/compliance_checker.py` 🔄
**Changes Needed**:
1. Replace anthropic client with keywords_client:
   ```python
   self.client = KeywordsAIClient(api_key=settings.KEYWORDS_API_KEY)
   ```

2. Update API calls to use keywords_client.complete()

### 4. Requirements.txt Updates

**ADD** (Joseph's dependencies):
```txt
requests==2.31.0
python-dotenv==1.0.1
```

**KEEP** (existing dependencies):
```txt
fastapi==0.109.0
uvicorn[standard]==0.27.0
pydantic==2.5.3
pydantic-settings==2.1.0
```

**REMOVE** (no longer needed):
```txt
anthropic==0.18.1  # Replaced by Keywords AI client
```

### 5. Schemas Updates

**File**: `backend/app/models/schemas.py`

**ADD** fields to support Joseph's features:
```python
class ApplicantInfo(BaseModel):
    # Existing fields...

    # Additional fields for profile analysis
    instagram_url: Optional[HttpUrl] = None  # Already exists
    # ... other social URLs already exist

class GatheredData(BaseModel):
    # UPDATE to match Joseph's ProfileAnalysis structure
    sources: List[str] = []
    professional_summary: Optional[str] = None
    lifestyle_summary: Optional[str] = None
    social_summary: Optional[str] = None
    red_flags: List[str] = []
    positive_indicators: List[str] = []

    # ML features
    combined_features: Optional[Dict[str, float]] = None
```

## Implementation Steps

1. ✅ Copy Joseph's files to `backend/app/services/`
2. ✅ Update `.env` with correct variable names
3. ⏳ Update `backend/app/config.py`
4. ⏳ Update `backend/requirements.txt`
5. ⏳ Refactor `ai_agent.py` to use Joseph's framework
6. ⏳ Simplify `risk_calculator.py`
7. ⏳ Update `compliance_checker.py` to use keywords_client
8. ⏳ Delete `data_gatherer.py`
9. ⏳ Update schemas to support new features
10. ⏳ Test the integrated system

## Testing Plan

1. Start the server: `python -m app.main`
2. Test health endpoint: GET `/api/v1/health`
3. Submit test loan application with social media URLs
4. Verify:
   - Profile analysis runs
   - Features extracted correctly
   - Risk assessment uses ML features
   - Compliance checking works
   - Report generation includes profile insights

## Benefits of Integration

1. **Real Profile Analysis**: Actually scrapes social media (vs simulation)
2. **ML-Ready Features**: 60+ normalized features for future ML models
3. **Better Risk Assessment**: Combines traditional + alternative data
4. **Structured Data**: Clean dataclasses for type safety
5. **Keywords AI Native**: Uses proper OpenAI-compatible API

## Notes

- Joseph's framework is production-quality
- My placeholder code was just scaffolding
- This integration creates a powerful underwriting platform
- Future: Add actual ML model to score the features
