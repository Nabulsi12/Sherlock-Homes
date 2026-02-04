# Social Media Analysis Feature - Implementation Complete

## Overview

The **Fourth Factor** social media analysis feature has been fully implemented in Sherlocke Homes. This feature analyzes applicants' social media profiles to provide additional insights beyond traditional underwriting factors (Credit Score, Income, Collateral).

## What It Does

The system analyzes social media profiles to extract:

### 1. Professional Features (LinkedIn)
- Current job title and company
- Employment history and tenure
- Education level and institutions
- Career trajectory (growing, stable, declining)
- Industry stability
- Professional network size and credibility

### 2. Lifestyle Features (Instagram/Facebook/TikTok)
- Apparent lifestyle level (frugal to lavish)
- Spending patterns vs. income
- Travel frequency
- Hobbies and interests
- Housing quality indicators
- Financial responsibility signals

### 3. Social Connectedness Features
- Network size and quality
- Family presence and stability
- Community involvement
- Relationship status
- Support system indicators

## How It Works

### Backend Architecture

1. **Profile Analyzer** (`backend/app/services/profile_analyzer.py`)
   - Uses Perplexity API's Sonar model to search and analyze profiles
   - Supports LinkedIn, Instagram, Twitter, Facebook, TikTok
   - Extracts structured data from unstructured profile information

2. **Feature Extractor** (`backend/app/services/feature_extractor.py`)
   - Converts profile analysis into 60+ normalized ML features
   - Includes professional, lifestyle, and social connectedness scores
   - Generates derived metrics (job stability, lifestyle alignment, etc.)

3. **AI Agent** (`backend/app/services/ai_agent.py`)
   - Orchestrates the analysis workflow
   - Combines traditional Big 3 factors with Fourth Factor insights
   - Returns comprehensive risk assessment

### Frontend Integration

The HTML form ([underwriting-ai.html](underwriting-ai.html)) now includes:

- **Input Fields** for social media URLs:
  - LinkedIn URL
  - Facebook URL
  - Instagram handle
  - Twitter handle

- **Result Display** showing:
  - Professional profile summary
  - Lifestyle indicators
  - Positive indicators (✓)
  - Items to review (⚠)
  - Overall social media insights

## Usage

### 1. Configure Environment

Add to your `.env` file:

```env
# Required for social media analysis
PERPLEXITY_API_KEY=your_perplexity_api_key_here
KEYWORDS_API_KEY=your_keywords_ai_key_here
```

Get your Perplexity API key from: https://www.perplexity.ai/settings/api

### 2. Fill Out Application Form

In the "Submit Full Application" modal:

1. Fill in all required borrower information
2. **Add social media profiles** (optional but recommended):
   - LinkedIn: `https://linkedin.com/in/username`
   - Facebook: `https://facebook.com/username`
   - Instagram: `@username` or `https://instagram.com/username`
   - Twitter: `@handle` or `https://twitter.com/handle`

3. Click "Submit Application"

### 3. Review Results

The analysis report will include:

- Traditional underwriting analysis (Credit, DTI, LTV)
- **NEW: Social Media Insights (Fourth Factor)** section showing:
  - Number of profiles analyzed
  - Professional background
  - Lifestyle indicators
  - Positive factors supporting the application
  - Any concerns or red flags

## API Endpoints

### POST /api/v1/loan-applications

**Request Body** (LoanApplicationRequest):
```json
{
  "applicant": {
    "full_name": "John Smith",
    "email": "john@example.com",
    "phone": "555-0123",
    "annual_income": 120000,
    "credit_score": 750,
    "linkedin_url": "https://linkedin.com/in/johnsmith",
    "instagram_handle": "@johnsmith",
    "facebook_url": "https://facebook.com/johnsmith",
    "twitter_handle": "@johnsmith"
  },
  "property_info": { ... },
  "loan_details": { ... }
}
```

**Response** (LoanApplicationResponse):
```json
{
  "application_id": "LN-2026-abc123",
  "status": "review",
  "risk_assessment": { ... },
  "fourth_factor": {
    "sources": ["linkedin.com/in/johnsmith", "instagram.com/johnsmith"],
    "professional_summary": "Senior Software Engineer...",
    "lifestyle_summary": "Moderate lifestyle...",
    "positive_indicators": [
      "10 years stable employment",
      "Active community involvement"
    ],
    "red_flags": [],
    "additional_findings": "Analyzed 2 social media profiles..."
  },
  "ml_features": { ... }
}
```

## Technical Details

### ML Features Generated

The system generates 60+ normalized features (0-1 scale):

- **Traditional (10 features)**: credit_score_normalized, dti_ratio, ltv_ratio, etc.
- **Professional (15 features)**: job_stability_score, career_trajectory, education_level, etc.
- **Lifestyle (16 features)**: lifestyle_stability_score, income_lifestyle_alignment, etc.
- **Social (19 features)**: social_support_score, community_rootedness, etc.

These features can be used for future ML model training.

### Privacy & Compliance

- **Public Data Only**: Analyzes only publicly available profile information
- **No Scraping**: Uses Perplexity's search API, not web scraping
- **Fannie Mae Compliant**: Follows Selling Guide requirements
- **Transparent**: All findings shown to applicant and underwriter

## Testing

### Manual Test

1. Start the backend:
   ```bash
   cd backend
   uvicorn app.main:app --reload
   ```

2. Open [underwriting-ai.html](underwriting-ai.html) in browser

3. Submit a test application with social media URLs

4. Verify the "Fourth Factor" section appears in results

### Example Test URLs

You can use public profiles for testing:
- LinkedIn: Any public LinkedIn profile URL
- Instagram: Public Instagram profiles
- Twitter: Public Twitter/X profiles

## Files Modified

1. ✅ [underwriting-ai.html](underwriting-ai.html)
   - Updated `submitApplication()` to send social media URLs
   - Modified `generateDetailedAnalysis()` to display Fourth Factor
   - Changed endpoint from `/quick-assessment` to `/loan-applications`

2. ✅ [backend/.env.example](backend/.env.example)
   - Added `PERPLEXITY_API_KEY` requirement

3. ✅ [backend/app/services/ai_agent.py](backend/app/services/ai_agent.py)
   - Already implemented! ✨

4. ✅ [backend/app/services/profile_analyzer.py](backend/app/services/profile_analyzer.py)
   - Already implemented! ✨

5. ✅ [backend/app/services/feature_extractor.py](backend/app/services/feature_extractor.py)
   - Already implemented! ✨

## Next Steps (Optional Enhancements)

- [ ] Add profile analysis caching to reduce API calls
- [ ] Implement batch profile analysis for multiple applicants
- [ ] Add ML model training pipeline using extracted features
- [ ] Create admin dashboard to view Fourth Factor insights across all applications
- [ ] Add configurable weights for Fourth Factor in risk scoring

## Questions?

The social media analysis is **fully functional** and integrated. Just add your `PERPLEXITY_API_KEY` to the `.env` file and start submitting applications with social media URLs!
