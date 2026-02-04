"""
Sherlock Homes API Server

Simple Flask server that handles form submissions from the frontend
and returns risk assessment reports.

Run with: python api_server.py
Server runs on: http://localhost:5000
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from risk_scorer import process_form_submission, RiskScorer, TEST_CASES

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend requests


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({"status": "ok", "service": "Sherlock Homes API"})


@app.route('/api/score', methods=['POST'])
def score_application():
    """
    Score a loan application.

    Expected JSON body:
    {
        "borrower_name": "John Doe",
        "loan_amount": 450000,
        "property_value": 550000,
        "loan_type": "30-Year Fixed Conventional",
        "property_address": "123 Main St, Austin, TX",
        "credit_score": 720,
        "annual_income": 120000,
        "monthly_debts": 800,
        "employment_years": 5,
        "reserves_months": 6,
        "linkedin_url": "https://linkedin.com/in/...",  // optional
        "instagram_url": "https://instagram.com/..."    // optional
    }
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({"status": "error", "message": "No data provided"}), 400

        result = process_form_submission(data)

        if result["status"] == "success":
            return jsonify(result)
        else:
            return jsonify(result), 400

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/test-cases', methods=['GET'])
def get_test_cases():
    """Get all test cases with their scores."""
    try:
        scorer = RiskScorer()
        results = []

        for case in TEST_CASES:
            report = scorer.score_application(case)
            results.append({
                "case": case,
                "report": report.to_dict()
            })

        return jsonify({"status": "success", "results": results})

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/test-cases/<case_id>', methods=['GET'])
def get_test_case(case_id):
    """Get a specific test case with its score."""
    try:
        case = next((c for c in TEST_CASES if c["id"] == case_id), None)

        if not case:
            return jsonify({"status": "error", "message": f"Case {case_id} not found"}), 404

        scorer = RiskScorer()
        report = scorer.score_application(case)

        return jsonify({
            "status": "success",
            "case": case,
            "report": report.to_dict()
        })

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == '__main__':
    print("=" * 50)
    print("Sherlock Homes API Server")
    print("=" * 50)
    print()
    print("Starting server on http://localhost:5000")
    print()
    print("Endpoints:")
    print("  GET  /api/health       - Health check")
    print("  POST /api/score        - Score a new application")
    print("  GET  /api/test-cases   - Get all test cases with scores")
    print("  GET  /api/test-cases/<id> - Get specific test case")
    print()

    app.run(debug=True, port=5000)
