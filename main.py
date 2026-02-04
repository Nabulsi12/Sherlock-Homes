"""
Sherlock Homes - AI-Powered Mortgage Underwriting Platform
==========================================================

Main entry point that integrates all backend components:
- Keywords AI client for LLM calls
- Profile analyzer for social media analysis
- Feature extractor for ML-ready features
- Risk scorer for loan application assessment

Usage:
    python main.py                          # Run interactive mode
    python main.py --score <application_id> # Score a specific test case
    python main.py --analyze <profile_url>  # Analyze a social profile
    python main.py --test                   # Run all test cases
"""

import json
import argparse
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import backend modules
from keywords_client import KeywordsAIClient
from profile_analyzer import analyze_profile, analyze_multiple_profiles, AnalysisMode
from feature_extractor import (
    FeatureExtractor,
    CombinedFeatures,
    TraditionalFeatures,
    ProfessionalFeatures,
    LifestyleFeatures,
    SocialConnectednessFeatures
)
from risk_scorer import RiskScorer, TEST_CASES


# =============================================================================
# SHERLOCK HOMES MAIN APPLICATION
# =============================================================================

class SherlockHomes:
    """
    Main application class for Sherlock Homes underwriting platform.
    Orchestrates all backend components for comprehensive loan assessment.
    """

    def __init__(self):
        """Initialize all backend components."""
        print("Initializing Sherlock Homes...")

        # Initialize Keywords AI client (for OpenAI calls via proxy)
        try:
            self.keywords_client = KeywordsAIClient()
            print("  [OK] Keywords AI client initialized")
        except ValueError as e:
            print(f"  [WARNING] Keywords AI client: {e}")
            self.keywords_client = None

        # Initialize feature extractor
        self.feature_extractor = FeatureExtractor(keywords_client=self.keywords_client)
        print("  [OK] Feature extractor initialized")

        # Initialize risk scorer
        self.risk_scorer = RiskScorer()
        print("  [OK] Risk scorer initialized")

        print("Sherlock Homes ready.\n")

    def analyze_social_profiles(
        self,
        linkedin_url: Optional[str] = None,
        instagram_url: Optional[str] = None,
        twitter_url: Optional[str] = None,
        facebook_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze social media profiles for underwriting insights.

        Args:
            linkedin_url: LinkedIn profile URL
            instagram_url: Instagram profile URL
            twitter_url: Twitter/X profile URL
            facebook_url: Facebook profile URL

        Returns:
            Combined analysis results
        """
        urls = []
        if linkedin_url:
            urls.append(linkedin_url)
        if instagram_url:
            urls.append(instagram_url)
        if twitter_url:
            urls.append(twitter_url)
        if facebook_url:
            urls.append(facebook_url)

        if not urls:
            return {"status": "error", "message": "No profile URLs provided"}

        if len(urls) == 1:
            result = analyze_profile(urls[0], mode=AnalysisMode.COMPREHENSIVE)
            return result.to_dict()
        else:
            result = analyze_multiple_profiles(urls, mode=AnalysisMode.COMPREHENSIVE)
            return result.to_dict()

    def extract_features(
        self,
        application_data: Dict[str, Any],
        professional_analysis: str = None,
        lifestyle_analysis: str = None
    ) -> Dict[str, Any]:
        """
        Extract ML-ready features from application data and profile analyses.

        Args:
            application_data: Traditional loan application data
            professional_analysis: LinkedIn/professional analysis text
            lifestyle_analysis: Instagram/lifestyle analysis text

        Returns:
            Normalized features ready for ML model
        """
        combined = self.feature_extractor.extract_all_features(
            traditional_data=application_data,
            professional_analysis=professional_analysis,
            lifestyle_analysis=lifestyle_analysis
        )
        return {
            "features": combined.to_model_input(),
            "raw": combined.to_dict()
        }

    def score_application(self, application: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate risk score for a loan application.

        Args:
            application: Loan application data

        Returns:
            Risk score and analysis
        """
        return self.risk_scorer.score_application(application)

    def score_test_cases(self) -> list:
        """
        Score all test cases from the dashboard.

        Returns:
            List of risk score results
        """
        return self.risk_scorer.score_all_test_cases()

    def process_full_application(
        self,
        application_data: Dict[str, Any],
        linkedin_url: Optional[str] = None,
        instagram_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process a complete loan application with social media analysis.

        This is the main workflow that:
        1. Analyzes social media profiles (if provided)
        2. Extracts features from all sources
        3. Calculates risk score
        4. Returns comprehensive assessment

        Args:
            application_data: Traditional loan application data
            linkedin_url: LinkedIn profile for professional analysis
            instagram_url: Instagram profile for lifestyle analysis

        Returns:
            Comprehensive assessment results
        """
        results = {
            "application": application_data,
            "social_analysis": None,
            "features": None,
            "risk_score": None
        }

        # Step 1: Analyze social media if URLs provided
        if linkedin_url or instagram_url:
            print("Step 1: Analyzing social media profiles...")
            social = self.analyze_social_profiles(
                linkedin_url=linkedin_url,
                instagram_url=instagram_url
            )
            results["social_analysis"] = social

        # Step 2: Extract features
        print("Step 2: Extracting features...")
        professional_text = None
        lifestyle_text = None

        if results["social_analysis"]:
            # Extract analysis text for feature extraction
            if "profiles" in results["social_analysis"]:
                for profile in results["social_analysis"]["profiles"]:
                    if profile.get("platform") == "linkedin":
                        professional_text = profile.get("raw_analysis")
                    elif profile.get("platform") in ["instagram", "facebook"]:
                        lifestyle_text = profile.get("raw_analysis")
            elif results["social_analysis"].get("raw_analysis"):
                professional_text = results["social_analysis"]["raw_analysis"]

        features = self.extract_features(
            application_data=application_data,
            professional_analysis=professional_text,
            lifestyle_analysis=lifestyle_text
        )
        results["features"] = features

        # Step 3: Calculate risk score
        print("Step 3: Calculating risk score...")
        risk = self.score_application(application_data)
        results["risk_score"] = risk

        return results


# =============================================================================
# CLI INTERFACE
# =============================================================================

def run_interactive():
    """Run interactive mode."""
    app = SherlockHomes()

    print("=" * 60)
    print("SHERLOCK HOMES - Interactive Mode")
    print("=" * 60)
    print()
    print("Commands:")
    print("  test     - Score all test cases")
    print("  score    - Score a specific application")
    print("  analyze  - Analyze a social profile")
    print("  quit     - Exit")
    print()

    while True:
        try:
            cmd = input("sherlock> ").strip().lower()

            if cmd in ["quit", "exit", "q"]:
                print("Goodbye!")
                break

            elif cmd == "test":
                print("\nScoring test cases...")
                print("-" * 40)
                for case in TEST_CASES:
                    print(f"\n{case['id']}: {case['borrower']}")
                    print(f"  Loan: ${case['loan_amount']:,}")
                    print(f"  Property: ${case['property_value']:,}")
                    print(f"  LTV: {case['ltv']}%")
                    print(f"  Current Risk Score: {case['current_risk_score']}")
                    result = app.score_application(case)
                    if result.get("risk_score"):
                        print(f"  AI Risk Score: {result['risk_score']}")
                    else:
                        print(f"  AI Risk Score: Not configured (see risk_scorer.py)")

            elif cmd == "score":
                print("\nEnter application details:")
                borrower = input("  Borrower name: ")
                loan_amount = float(input("  Loan amount: $"))
                property_value = float(input("  Property value: $"))
                loan_type = input("  Loan type (e.g., 30-Year Fixed Conventional): ")

                application = {
                    "borrower": borrower,
                    "loan_amount": loan_amount,
                    "property_value": property_value,
                    "ltv": (loan_amount / property_value) * 100,
                    "loan_type": loan_type
                }

                result = app.score_application(application)
                print(f"\nResult: {json.dumps(result, indent=2)}")

            elif cmd == "analyze":
                url = input("Enter profile URL: ")
                result = app.analyze_social_profiles(linkedin_url=url)
                print(f"\nAnalysis: {json.dumps(result, indent=2)}")

            elif cmd == "help":
                print("\nCommands: test, score, analyze, quit")

            elif cmd:
                print(f"Unknown command: {cmd}. Type 'help' for commands.")

        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Sherlock Homes - AI-Powered Mortgage Underwriting",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        "--test", "-t",
        action="store_true",
        help="Run risk scoring on all test cases"
    )

    parser.add_argument(
        "--score", "-s",
        type=str,
        help="Score a specific test case by ID (e.g., LN-2024-08472)"
    )

    parser.add_argument(
        "--analyze", "-a",
        type=str,
        help="Analyze a social media profile URL"
    )

    parser.add_argument(
        "--interactive", "-i",
        action="store_true",
        help="Run in interactive mode"
    )

    parser.add_argument(
        "--output", "-o",
        type=str,
        help="Output file for results (JSON)"
    )

    args = parser.parse_args()

    # Initialize application
    app = SherlockHomes()

    if args.test:
        print("\n" + "=" * 60)
        print("SCORING ALL TEST CASES")
        print("=" * 60)

        results = []
        for case in TEST_CASES:
            print(f"\n{case['id']}: {case['borrower']}")
            print(f"  Loan: ${case['loan_amount']:,} | LTV: {case['ltv']}%")
            print(f"  Dashboard Risk Score: {case['current_risk_score']}")

            result = app.score_application(case)
            result["dashboard_score"] = case["current_risk_score"]
            results.append(result)

            if result.get("risk_score"):
                print(f"  AI Calculated Score: {result['risk_score']}")
            else:
                print("  AI Score: Prompt not configured")

        if args.output:
            with open(args.output, "w") as f:
                json.dump(results, f, indent=2)
            print(f"\nResults saved to: {args.output}")

    elif args.score:
        case = next((c for c in TEST_CASES if c["id"] == args.score), None)
        if case:
            print(f"\nScoring {case['id']}: {case['borrower']}")
            result = app.score_application(case)
            print(json.dumps(result, indent=2))
        else:
            print(f"Test case not found: {args.score}")
            print("Available cases:", [c["id"] for c in TEST_CASES])

    elif args.analyze:
        print(f"\nAnalyzing profile: {args.analyze}")
        result = app.analyze_social_profiles(linkedin_url=args.analyze)
        print(json.dumps(result, indent=2))

        if args.output:
            with open(args.output, "w") as f:
                json.dump(result, f, indent=2)
            print(f"\nResults saved to: {args.output}")

    elif args.interactive:
        run_interactive()

    else:
        # Default: run interactive mode
        run_interactive()


if __name__ == "__main__":
    main()
