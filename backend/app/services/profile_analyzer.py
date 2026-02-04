"""
Social Media Profile Analyzer

Analyzes social media profiles using Perplexity's Sonar API.
Supports multiple platforms: LinkedIn, Instagram, Twitter/X, Facebook.
Extracts professional info, lifestyle indicators, and social connectedness.

Usage:
    python profile_analyzer.py <profile_url> [--prompt "custom prompt"]
    python profile_analyzer.py <profile_url> --platform instagram --mode lifestyle
    python profile_analyzer.py --multi linkedin_url instagram_url twitter_url
"""

import argparse
import json
import os
import re
import sys
from enum import Enum
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import requests
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from .env file in project root
env_path = Path(__file__).parent.parent.parent.parent / ".env"
load_dotenv(env_path)

PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")
PERPLEXITY_API_URL = "https://api.perplexity.ai/chat/completions"


def extract_name_from_url(url: str) -> Optional[str]:
    """Extract a person's name from a social media URL."""
    url_lower = url.lower()

    # LinkedIn: /in/firstname-lastname/ or /in/firstnamelastname/
    if "linkedin.com/in/" in url_lower:
        match = re.search(r'linkedin\.com/in/([^/?]+)', url, re.IGNORECASE)
        if match:
            username = match.group(1).strip('/')
            # Convert hyphens/underscores to spaces and title case
            name = username.replace('-', ' ').replace('_', ' ')
            # Remove numbers at the end (like "john-doe-123")
            name = re.sub(r'\s*\d+$', '', name)
            return name.title()

    # Instagram/Twitter/TikTok: /@username or /username
    for platform in ['instagram.com/', 'twitter.com/', 'x.com/', 'tiktok.com/@', 'facebook.com/']:
        if platform in url_lower:
            match = re.search(rf'{re.escape(platform)}([^/?]+)', url, re.IGNORECASE)
            if match:
                return match.group(1).strip('/')

    return None


def search_person_info(
    name: str,
    platform: str = "linkedin",
    additional_context: str = None
) -> Dict[str, Any]:
    """
    Search for information about a person using Perplexity's search capabilities.

    This is a fallback when direct profile access isn't available.
    """
    if not PERPLEXITY_API_KEY:
        return {
            "status": "error",
            "raw_analysis": "PERPLEXITY_API_KEY not found."
        }

    # Build search query
    search_context = f" {additional_context}" if additional_context else ""

    if platform == "linkedin":
        search_query = f'"{name}" LinkedIn profile professional background'
    elif platform == "instagram":
        search_query = f'"{name}" Instagram'
    elif platform == "twitter":
        search_query = f'"{name}" Twitter OR X.com'
    else:
        search_query = f'"{name}" social media{search_context}'

    prompt = f"""Search for professional information about "{name}" and provide a comprehensive profile analysis.

SEARCH FOR AND EXTRACT:
1. **Current Position**: Job title and company
2. **Employment History**: Previous roles, companies, and approximate tenure
3. **Education**: Degrees, institutions, graduation years
4. **Industry/Sector**: What field they work in
5. **Skills & Expertise**: Technical and professional skills
6. **Career Trajectory**: Are they growing, stable, or declining in their career?
7. **Professional Network**: Any indicators of network size or influence
8. **Notable Achievements**: Awards, publications, speaking engagements
9. **Location**: Where they are based

ALSO IDENTIFY:
**RED FLAGS**: Any concerning patterns (frequent job changes, gaps, inconsistencies)
**POSITIVE INDICATORS**: Stability signs (long tenure, promotions, professional growth)

Search query to use: {search_query}

If information is not found, explicitly state "Not found" for that field.
Distinguish between verified facts and inferences."""

    headers = {
        "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
        "Content-Type": "application/json"
    }

    # Use sonar-pro for better search results
    payload = {
        "model": "sonar",
        "messages": [
            {
                "role": "system",
                "content": "You are a professional research analyst. Search the web thoroughly to find information about the specified person. Focus on professional/career information from LinkedIn, company websites, news articles, and other public sources. Be factual and cite sources when possible."
            },
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.1,
        "max_tokens": 3000
    }

    try:
        response = requests.post(
            PERPLEXITY_API_URL,
            headers=headers,
            json=payload,
            timeout=90
        )
        response.raise_for_status()

        result = response.json()
        raw_analysis = result["choices"][0]["message"]["content"]
        citations = result.get("citations", [])

        return {
            "status": "success",
            "raw_analysis": raw_analysis,
            "citations": citations,
            "search_query": search_query,
            "name": name
        }

    except Exception as e:
        return {
            "status": "error",
            "raw_analysis": f"Search failed: {str(e)}"
        }


class Platform(Enum):
    """Supported social media platforms."""
    LINKEDIN = "linkedin"
    INSTAGRAM = "instagram"
    TWITTER = "twitter"
    FACEBOOK = "facebook"
    TIKTOK = "tiktok"
    UNKNOWN = "unknown"


class AnalysisMode(Enum):
    """Analysis modes for different aspects."""
    PROFESSIONAL = "professional"  # Career, skills, employment
    LIFESTYLE = "lifestyle"  # Spending habits, hobbies, interests
    SOCIAL = "social"  # Connectedness, relationships, community
    COMPREHENSIVE = "comprehensive"  # All of the above


# Platform-specific feature sets
PLATFORM_FEATURES = {
    Platform.LINKEDIN: {
        AnalysisMode.PROFESSIONAL: [
            "Current job title and company",
            "Employment history and tenure at each role",
            "Total years of professional experience",
            "Education level and institutions",
            "Skills and endorsements",
            "Career progression trajectory",
            "Industry and sector",
            "Certifications and licenses",
        ],
        AnalysisMode.SOCIAL: [
            "Number of connections (estimate tier: <500, 500-1000, 1000+)",
            "Engagement level (posts, comments, activity)",
            "Recommendations received and given",
            "Professional group memberships",
            "Thought leadership indicators",
        ],
        AnalysisMode.LIFESTYLE: [
            "Work-life balance indicators",
            "Volunteer work and causes",
            "Professional interests and passions",
            "Side projects or entrepreneurial activities",
        ],
    },
    Platform.INSTAGRAM: {
        AnalysisMode.LIFESTYLE: [
            "Apparent lifestyle level (modest, comfortable, lavish)",
            "Travel frequency and destinations",
            "Hobbies and leisure activities",
            "Dining and entertainment habits",
            "Fashion and material possessions displayed",
            "Home/living situation indicators",
            "Vehicle ownership if visible",
            "Spending pattern indicators",
        ],
        AnalysisMode.SOCIAL: [
            "Follower count and engagement rate",
            "Friend/family presence in posts",
            "Community involvement",
            "Relationship status indicators",
            "Social circle size and quality",
            "Frequency of social gatherings",
        ],
        AnalysisMode.PROFESSIONAL: [
            "Any business or work-related content",
            "Side hustles or entrepreneurial activity",
            "Professional achievements shared",
        ],
    },
    Platform.TWITTER: {
        AnalysisMode.PROFESSIONAL: [
            "Professional topics discussed",
            "Industry engagement",
            "Thought leadership content",
            "Professional network interactions",
        ],
        AnalysisMode.LIFESTYLE: [
            "Interests and hobbies mentioned",
            "Political views if expressed",
            "Life events shared",
            "Daily routine indicators",
        ],
        AnalysisMode.SOCIAL: [
            "Follower/following ratio",
            "Engagement patterns",
            "Community involvement",
            "Conversation style and tone",
            "Network quality indicators",
        ],
    },
    Platform.FACEBOOK: {
        AnalysisMode.LIFESTYLE: [
            "Life events (marriage, home purchase, etc.)",
            "Family situation",
            "Hobbies and interests",
            "Check-ins and travel",
            "Lifestyle indicators from photos",
        ],
        AnalysisMode.SOCIAL: [
            "Friend count tier",
            "Family connections visible",
            "Community group memberships",
            "Event attendance",
            "Relationship status",
        ],
        AnalysisMode.PROFESSIONAL: [
            "Work history listed",
            "Education listed",
            "Professional page associations",
        ],
    },
    Platform.TIKTOK: {
        AnalysisMode.LIFESTYLE: [
            "Content themes and interests",
            "Lifestyle portrayed in videos",
            "Spending indicators",
            "Hobbies and activities",
        ],
        AnalysisMode.SOCIAL: [
            "Follower count",
            "Engagement rate",
            "Community participation",
            "Collaboration with others",
        ],
        AnalysisMode.PROFESSIONAL: [
            "Professional or educational content",
            "Business promotion",
            "Career-related content",
        ],
    },
}


@dataclass
class ProfileAnalysis:
    """Structured analysis results for a single profile."""
    url: str
    platform: str
    status: str
    professional_summary: Optional[str] = None
    lifestyle_summary: Optional[str] = None
    social_summary: Optional[str] = None
    red_flags: List[str] = None
    positive_indicators: List[str] = None
    raw_analysis: Optional[str] = None
    citations: List[str] = None

    def __post_init__(self):
        if self.red_flags is None:
            self.red_flags = []
        if self.positive_indicators is None:
            self.positive_indicators = []
        if self.citations is None:
            self.citations = []

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class MultiProfileAnalysis:
    """Combined analysis across multiple social media profiles."""
    profiles: List[ProfileAnalysis]
    overall_professional_score: float = 0.0  # 0-1
    overall_lifestyle_score: float = 0.0  # 0-1 (stability indicator)
    overall_social_score: float = 0.0  # 0-1 (connectedness)
    combined_red_flags: List[str] = None
    combined_positive_indicators: List[str] = None
    consistency_score: float = 0.0  # How consistent info is across platforms
    summary: Optional[str] = None

    def __post_init__(self):
        if self.combined_red_flags is None:
            self.combined_red_flags = []
        if self.combined_positive_indicators is None:
            self.combined_positive_indicators = []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "profiles": [p.to_dict() for p in self.profiles],
            "overall_professional_score": self.overall_professional_score,
            "overall_lifestyle_score": self.overall_lifestyle_score,
            "overall_social_score": self.overall_social_score,
            "combined_red_flags": self.combined_red_flags,
            "combined_positive_indicators": self.combined_positive_indicators,
            "consistency_score": self.consistency_score,
            "summary": self.summary,
        }


def detect_platform(url: str) -> Platform:
    """Detect the social media platform from a URL."""
    url_lower = url.lower()

    if "linkedin.com" in url_lower:
        return Platform.LINKEDIN
    elif "instagram.com" in url_lower:
        return Platform.INSTAGRAM
    elif "twitter.com" in url_lower or "x.com" in url_lower:
        return Platform.TWITTER
    elif "facebook.com" in url_lower or "fb.com" in url_lower:
        return Platform.FACEBOOK
    elif "tiktok.com" in url_lower:
        return Platform.TIKTOK
    else:
        return Platform.UNKNOWN


def build_analysis_prompt(
    platform: Platform,
    mode: AnalysisMode,
    custom_features: List[str] = None
) -> str:
    """Build an analysis prompt based on platform and mode."""

    if mode == AnalysisMode.COMPREHENSIVE:
        # Combine all modes for this platform
        all_features = []
        for m in [AnalysisMode.PROFESSIONAL, AnalysisMode.LIFESTYLE, AnalysisMode.SOCIAL]:
            features = PLATFORM_FEATURES.get(platform, {}).get(m, [])
            if features:
                all_features.append(f"\n**{m.value.upper()} ASPECTS:**")
                all_features.extend([f"- {f}" for f in features])
        features_text = "\n".join(all_features)
    else:
        features = custom_features or PLATFORM_FEATURES.get(platform, {}).get(mode, [])
        features_text = "\n".join([f"- {f}" for f in features])

    prompt = f"""Analyze this {platform.value} profile comprehensively for mortgage underwriting risk assessment.

EXTRACT THE FOLLOWING INFORMATION:
{features_text}

ALSO IDENTIFY:

**RED FLAGS (risk indicators):**
- Financial instability signs (frequent job changes, lifestyle beyond apparent means)
- Inconsistencies between claimed status and visible lifestyle
- Risky behaviors or habits
- Employment gaps or instability
- Any concerning patterns

**POSITIVE INDICATORS (stability signs):**
- Long-term employment
- Professional growth trajectory
- Stable lifestyle indicators
- Strong community ties
- Financial responsibility signs

**SOCIAL CONNECTEDNESS:**
- Size and quality of social network
- Family stability indicators
- Community involvement
- Support system indicators

Provide a structured analysis with clear sections. Note explicitly if information is not available or the profile is private."""

    return prompt


def analyze_profile(
    url: str,
    prompt: str = None,
    features: List[str] = None,
    mode: AnalysisMode = AnalysisMode.COMPREHENSIVE,
    platform: Platform = None
) -> ProfileAnalysis:
    """
    Analyze a social media profile using Perplexity Sonar API.

    Args:
        url: The social media profile URL to analyze
        prompt: Custom prompt for analysis (optional)
        features: List of specific features to look for (optional)
        mode: Analysis mode (professional, lifestyle, social, comprehensive)
        platform: Platform override (auto-detected if not provided)

    Returns:
        ProfileAnalysis dataclass with structured results
    """
    # Detect platform
    detected_platform = platform or detect_platform(url)

    if not PERPLEXITY_API_KEY:
        return ProfileAnalysis(
            url=url,
            platform=detected_platform.value,
            status="error",
            raw_analysis="PERPLEXITY_API_KEY not found. Please add it to your .env file."
        )

    # Build the analysis prompt
    if prompt:
        analysis_prompt = prompt
    elif features:
        features_text = "\n".join([f"- {f}" for f in features])
        analysis_prompt = f"""Analyze this profile and extract:\n{features_text}"""
    else:
        analysis_prompt = build_analysis_prompt(detected_platform, mode)

    # Prepare the API request
    headers = {
        "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
        "Content-Type": "application/json"
    }

    system_prompt = """You are an expert profile analyst for mortgage underwriting risk assessment.
Your job is to extract factual, objective information from social media profiles.
Focus on indicators of financial stability, employment consistency, lifestyle patterns, and social connectedness.
Be thorough but factual - only report what can be observed or reasonably inferred.
Clearly distinguish between facts and inferences.
If a profile is private or information is unavailable, state that explicitly."""

    payload = {
        "model": "sonar",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Profile URL: {url}\n\n{analysis_prompt}"}
        ],
        "temperature": 0.2,
        "max_tokens": 3000
    }

    try:
        response = requests.post(
            PERPLEXITY_API_URL,
            headers=headers,
            json=payload,
            timeout=90
        )
        response.raise_for_status()

        result = response.json()
        raw_analysis = result["choices"][0]["message"]["content"]
        citations = result.get("citations", [])

        # Parse the analysis into structured sections
        analysis = ProfileAnalysis(
            url=url,
            platform=detected_platform.value,
            status="success",
            raw_analysis=raw_analysis,
            citations=citations
        )

        # Extract sections from the analysis
        analysis = _parse_analysis_sections(analysis, raw_analysis)

        return analysis

    except requests.exceptions.HTTPError as e:
        return ProfileAnalysis(
            url=url,
            platform=detected_platform.value,
            status="error",
            raw_analysis=f"API error: {e.response.status_code} - {e.response.text}"
        )
    except requests.exceptions.RequestException as e:
        return ProfileAnalysis(
            url=url,
            platform=detected_platform.value,
            status="error",
            raw_analysis=f"Request failed: {str(e)}"
        )
    except (KeyError, IndexError) as e:
        return ProfileAnalysis(
            url=url,
            platform=detected_platform.value,
            status="error",
            raw_analysis=f"Unexpected API response format: {str(e)}"
        )


def _parse_analysis_sections(analysis: ProfileAnalysis, raw_text: str) -> ProfileAnalysis:
    """Parse raw analysis text into structured sections."""
    text_lower = raw_text.lower()

    # Try to extract red flags
    red_flag_patterns = [
        r"red flags?[:\s]*\n(.*?)(?=\n\n|\npositive|\n\*\*|$)",
        r"\*\*red flags?\*\*[:\s]*\n(.*?)(?=\n\n|\npositive|\n\*\*|$)",
    ]
    for pattern in red_flag_patterns:
        match = re.search(pattern, raw_text, re.IGNORECASE | re.DOTALL)
        if match:
            flags_text = match.group(1)
            flags = [f.strip().lstrip("-•* ") for f in flags_text.split("\n") if f.strip() and f.strip() != "None"]
            analysis.red_flags = [f for f in flags if len(f) > 3]
            break

    # Try to extract positive indicators
    positive_patterns = [
        r"positive indicators?[:\s]*\n(.*?)(?=\n\n|\nred|\n\*\*|$)",
        r"\*\*positive indicators?\*\*[:\s]*\n(.*?)(?=\n\n|\nred|\n\*\*|$)",
    ]
    for pattern in positive_patterns:
        match = re.search(pattern, raw_text, re.IGNORECASE | re.DOTALL)
        if match:
            pos_text = match.group(1)
            positives = [p.strip().lstrip("-•* ") for p in pos_text.split("\n") if p.strip() and p.strip() != "None"]
            analysis.positive_indicators = [p for p in positives if len(p) > 3]
            break

    # Extract section summaries based on content
    if "professional" in text_lower or "employment" in text_lower or "career" in text_lower:
        analysis.professional_summary = _extract_section(raw_text, ["professional", "employment", "career", "work"])

    if "lifestyle" in text_lower or "spending" in text_lower or "living" in text_lower:
        analysis.lifestyle_summary = _extract_section(raw_text, ["lifestyle", "spending", "living", "travel"])

    if "social" in text_lower or "connect" in text_lower or "network" in text_lower:
        analysis.social_summary = _extract_section(raw_text, ["social", "connect", "network", "community"])

    return analysis


def _extract_section(text: str, keywords: List[str]) -> Optional[str]:
    """Extract a section containing any of the keywords."""
    paragraphs = text.split("\n\n")
    relevant = []
    for para in paragraphs:
        if any(kw in para.lower() for kw in keywords):
            relevant.append(para.strip())
    return "\n\n".join(relevant[:2]) if relevant else None


def analyze_multiple_profiles(
    urls: List[str],
    mode: AnalysisMode = AnalysisMode.COMPREHENSIVE
) -> MultiProfileAnalysis:
    """
    Analyze multiple social media profiles and combine results.

    Args:
        urls: List of profile URLs to analyze
        mode: Analysis mode to use

    Returns:
        MultiProfileAnalysis with combined results
    """
    profiles = []

    for url in urls:
        print(f"Analyzing: {url}")
        analysis = analyze_profile(url, mode=mode)
        profiles.append(analysis)

    # Combine results
    combined = MultiProfileAnalysis(profiles=profiles)

    # Aggregate red flags and positive indicators
    for profile in profiles:
        if profile.red_flags:
            combined.combined_red_flags.extend(profile.red_flags)
        if profile.positive_indicators:
            combined.combined_positive_indicators.extend(profile.positive_indicators)

    # Remove duplicates
    combined.combined_red_flags = list(set(combined.combined_red_flags))
    combined.combined_positive_indicators = list(set(combined.combined_positive_indicators))

    # Generate combined summary using AI
    combined = _generate_combined_summary(combined)

    return combined


def _generate_combined_summary(analysis: MultiProfileAnalysis) -> MultiProfileAnalysis:
    """Generate a combined summary and scores from multiple profiles."""
    if not PERPLEXITY_API_KEY:
        return analysis

    # Build context from all profiles
    profiles_context = []
    for p in analysis.profiles:
        if p.status == "success":
            profiles_context.append(f"**{p.platform.upper()} ({p.url}):**\n{p.raw_analysis[:1500]}")

    if not profiles_context:
        return analysis

    prompt = f"""Based on the following social media profile analyses, provide:

1. **OVERALL PROFESSIONAL ASSESSMENT** (score 0-100):
   - Employment stability and career trajectory

2. **OVERALL LIFESTYLE ASSESSMENT** (score 0-100):
   - Financial stability indicators
   - Living within means vs. overspending signs

3. **OVERALL SOCIAL CONNECTEDNESS** (score 0-100):
   - Network strength and support system
   - Community ties and stability

4. **CONSISTENCY CHECK**:
   - How consistent is information across platforms?
   - Any discrepancies or concerns?

5. **COMBINED RISK SUMMARY**:
   - Key risk factors for mortgage underwriting
   - Key positive factors

PROFILES:
{chr(10).join(profiles_context)}

Return scores as numbers and provide brief justifications."""

    headers = {
        "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "sonar",
        "messages": [
            {
                "role": "system",
                "content": "You are a risk assessment analyst combining social media insights for mortgage underwriting."
            },
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.2,
        "max_tokens": 2000
    }

    try:
        response = requests.post(
            PERPLEXITY_API_URL,
            headers=headers,
            json=payload,
            timeout=90
        )
        response.raise_for_status()
        result = response.json()
        summary = result["choices"][0]["message"]["content"]
        analysis.summary = summary

        # Try to extract scores from summary
        score_patterns = [
            (r"professional[^\d]*(\d+)", "professional"),
            (r"lifestyle[^\d]*(\d+)", "lifestyle"),
            (r"social[^\d]*(\d+)", "social"),
            (r"consistency[^\d]*(\d+)", "consistency"),
        ]

        for pattern, score_type in score_patterns:
            match = re.search(pattern, summary, re.IGNORECASE)
            if match:
                score = min(int(match.group(1)), 100) / 100
                if score_type == "professional":
                    analysis.overall_professional_score = score
                elif score_type == "lifestyle":
                    analysis.overall_lifestyle_score = score
                elif score_type == "social":
                    analysis.overall_social_score = score
                elif score_type == "consistency":
                    analysis.consistency_score = score

    except Exception as e:
        analysis.summary = f"Could not generate combined summary: {str(e)}"

    return analysis


def main():
    parser = argparse.ArgumentParser(
        description="Analyze social media profiles for mortgage underwriting risk assessment",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Single profile analysis
  python profile_analyzer.py https://linkedin.com/in/username

  # Search-based analysis (better for LinkedIn)
  python profile_analyzer.py https://linkedin.com/in/username --search

  # Search by name directly
  python profile_analyzer.py --name "John Smith" --context "Software Engineer at Google"

  # Instagram lifestyle analysis
  python profile_analyzer.py https://instagram.com/username --mode lifestyle

  # Multiple profiles combined
  python profile_analyzer.py --multi https://linkedin.com/in/user https://instagram.com/user

  # Custom features
  python profile_analyzer.py https://linkedin.com/in/username --features "job stability,income indicators"
        """
    )

    parser.add_argument(
        "url",
        nargs="?",
        help="The social media profile URL to analyze"
    )

    parser.add_argument(
        "--multi", "-m",
        nargs="+",
        help="Multiple profile URLs to analyze together"
    )

    parser.add_argument(
        "--mode",
        choices=["professional", "lifestyle", "social", "comprehensive"],
        default="comprehensive",
        help="Analysis mode (default: comprehensive)"
    )

    parser.add_argument(
        "--prompt", "-p",
        help="Custom prompt for the analysis"
    )

    parser.add_argument(
        "--features", "-f",
        help="Comma-separated list of features to look for"
    )

    parser.add_argument(
        "--output", "-o",
        help="Output file to save results (JSON format)"
    )

    parser.add_argument(
        "--platform",
        choices=["linkedin", "instagram", "twitter", "facebook", "tiktok"],
        help="Override platform detection"
    )

    parser.add_argument(
        "--search", "-s",
        action="store_true",
        help="Use search-based approach instead of direct URL scraping (recommended for LinkedIn)"
    )

    parser.add_argument(
        "--name", "-n",
        help="Person's name to search for directly (without URL)"
    )

    parser.add_argument(
        "--context", "-c",
        help="Additional context for search (e.g., 'Software Engineer at Google')"
    )

    args = parser.parse_args()

    # Determine mode
    mode = AnalysisMode(args.mode)

    # Parse features if provided
    features = None
    if args.features:
        features = [f.strip() for f in args.features.split(",")]

    # Parse platform override
    platform = None
    if args.platform:
        platform = Platform(args.platform)

    # Search by name directly
    if args.name:
        print(f"Searching for: {args.name}")
        if args.context:
            print(f"Context: {args.context}")
        print("-" * 50)

        platform_str = args.platform if args.platform else "linkedin"
        search_result = search_person_info(
            name=args.name,
            platform=platform_str,
            additional_context=args.context
        )

        if search_result["status"] == "success":
            print("\n" + "=" * 50)
            print("SEARCH RESULTS")
            print("=" * 50)
            print(search_result["raw_analysis"])

            if search_result.get("citations"):
                print("\nSources:")
                for citation in search_result["citations"]:
                    print(f"  - {citation}")

            # Save to file
            if args.output:
                with open(args.output, "w", encoding="utf-8") as f:
                    json.dump(search_result, f, indent=2)
                print(f"\nResults saved to: {args.output}")
        else:
            print(f"\nError: {search_result['raw_analysis']}")
            sys.exit(1)

    # Multi-profile analysis
    elif args.multi:
        print(f"Analyzing {len(args.multi)} profiles...")
        print("-" * 50)
        result = analyze_multiple_profiles(args.multi, mode=mode)

        print("\n" + "=" * 50)
        print("COMBINED ANALYSIS")
        print("=" * 50)

        print(f"\nProfessional Score: {result.overall_professional_score * 100:.0f}/100")
        print(f"Lifestyle Score: {result.overall_lifestyle_score * 100:.0f}/100")
        print(f"Social Score: {result.overall_social_score * 100:.0f}/100")
        print(f"Consistency Score: {result.consistency_score * 100:.0f}/100")

        if result.combined_red_flags:
            print("\nRed Flags:")
            for flag in result.combined_red_flags[:5]:
                print(f"  - {flag}")

        if result.combined_positive_indicators:
            print("\nPositive Indicators:")
            for pos in result.combined_positive_indicators[:5]:
                print(f"  + {pos}")

        if result.summary:
            print(f"\nSummary:\n{result.summary}")

        # Save to file
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                json.dump(result.to_dict(), f, indent=2)
            print(f"\nResults saved to: {args.output}")

    # Single URL analysis
    elif args.url:
        # Use search-based approach if --search flag is set
        if args.search:
            name = extract_name_from_url(args.url)
            if not name:
                print("Could not extract name from URL. Please use --name flag instead.")
                sys.exit(1)

            detected_platform = platform.value if platform else detect_platform(args.url).value
            print(f"Search-based analysis for: {name}")
            print(f"Platform: {detected_platform}")
            if args.context:
                print(f"Context: {args.context}")
            print("-" * 50)

            search_result = search_person_info(
                name=name,
                platform=detected_platform,
                additional_context=args.context
            )

            if search_result["status"] == "success":
                # Convert to ProfileAnalysis for consistency
                result = ProfileAnalysis(
                    url=args.url,
                    platform=detected_platform,
                    status="success",
                    raw_analysis=search_result["raw_analysis"],
                    citations=search_result.get("citations", [])
                )
                result = _parse_analysis_sections(result, search_result["raw_analysis"])
            else:
                print(f"\nError: {search_result['raw_analysis']}")
                sys.exit(1)
        else:
            print(f"Analyzing profile: {args.url}")
            print(f"Mode: {mode.value}")
            print("-" * 50)

            result = analyze_profile(
                args.url,
                prompt=args.prompt,
                features=features,
                mode=mode,
                platform=platform
            )

        if result.status == "success":
            print(f"\nPlatform: {result.platform}")
            print("\n" + "=" * 50)
            print("ANALYSIS")
            print("=" * 50)
            print(result.raw_analysis)

            if result.red_flags:
                print("\nRed Flags:")
                for flag in result.red_flags:
                    print(f"  - {flag}")

            if result.positive_indicators:
                print("\nPositive Indicators:")
                for pos in result.positive_indicators:
                    print(f"  + {pos}")

            if result.citations:
                print("\nSources:")
                for citation in result.citations:
                    print(f"  - {citation}")

            # Save to file
            if args.output:
                with open(args.output, "w", encoding="utf-8") as f:
                    json.dump(result.to_dict(), f, indent=2)
                print(f"\nResults saved to: {args.output}")
        else:
            print(f"\nError: {result.raw_analysis}")
            sys.exit(1)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
