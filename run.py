"""
Sherlock Homes - One-Click Server
=================================

Run this file to start both the API server and frontend.
Opens in your browser automatically.

Usage: python run.py
"""

import sys
import webbrowser
import threading
import time

# Check for required packages
try:
    from flask import Flask, request, jsonify, send_from_directory, Response
    from flask_cors import CORS
except ImportError as e:
    print("\n" + "=" * 50)
    print("  MISSING DEPENDENCIES")
    print("=" * 50)
    print(f"\n  Error: {e}")
    print("\n  Please install required packages:")
    print("  pip install flask flask-cors")
    print("\n" + "=" * 50)
    input("\n  Press Enter to exit...")
    sys.exit(1)

# Import risk scorer components
try:
    from risk_scorer import process_form_submission, RiskScorer, TEST_CASES
    SCORER_AVAILABLE = True
except ImportError:
    SCORER_AVAILABLE = False
    TEST_CASES = []

app = Flask(__name__)
CORS(app)

# =============================================================================
# EMBEDDED FRONTEND HTML
# =============================================================================

FRONTEND_HTML = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sherlock Homes - Single Family Home Loan Underwriting</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        :root {
            --primary: #2563eb;
            --primary-dark: #1d4ed8;
            --secondary: #0f172a;
            --accent: #10b981;
            --danger: #ef4444;
            --warning: #f59e0b;
            --bg-light: #f8fafc;
            --text-gray: #64748b;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: var(--bg-light);
            color: var(--secondary);
            line-height: 1.6;
        }
        nav {
            background: white;
            padding: 1rem 2rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            position: fixed;
            width: 100%;
            top: 0;
            z-index: 1000;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .logo {
            font-size: 1.5rem;
            font-weight: 700;
            color: var(--primary);
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        .logo svg { width: 32px; height: 32px; }
        .nav-links {
            display: flex;
            gap: 2rem;
            list-style: none;
        }
        .nav-links a {
            text-decoration: none;
            color: var(--secondary);
            font-weight: 500;
            transition: color 0.2s;
        }
        .nav-links a:hover { color: var(--primary); }
        .nav-btn {
            background: var(--primary);
            color: white;
            border: none;
            padding: 0.75rem 1.5rem;
            border-radius: 8px;
            font-weight: 600;
            cursor: pointer;
            transition: background 0.2s;
        }
        .nav-btn:hover { background: var(--primary-dark); }
        .hero {
            padding: 8rem 2rem 4rem;
            background: linear-gradient(rgba(0,0,0,0.6), rgba(0,0,0,0.6)), linear-gradient(135deg, #1e3a5f 0%, #0f172a 100%);
            color: white;
            text-align: center;
        }
        .hero h1 { font-size: 3rem; margin-bottom: 1rem; font-weight: 800; }
        .hero p { font-size: 1.25rem; opacity: 0.9; max-width: 600px; margin: 0 auto 2rem; }
        .hero-stats { display: flex; justify-content: center; gap: 4rem; margin-top: 3rem; }
        .stat { text-align: center; }
        .stat-value { font-size: 2.5rem; font-weight: 700; }
        .stat-label { opacity: 0.8; font-size: 0.9rem; }
        .main-content {
            max-width: 1400px;
            margin: 0 auto;
            padding: 3rem 2rem;
            display: grid;
            grid-template-columns: 1fr 400px;
            gap: 2rem;
        }
        .dashboard {
            background: white;
            border-radius: 16px;
            padding: 2rem;
            box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
        }
        .section-title {
            font-size: 1.25rem;
            font-weight: 600;
            margin-bottom: 1.5rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        .applications { display: grid; grid-template-columns: repeat(2, 1fr); gap: 1.5rem; }
        .app-card {
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            overflow: hidden;
            transition: all 0.2s;
            background: white;
        }
        .app-card:hover {
            border-color: var(--primary);
            box-shadow: 0 4px 12px rgba(37, 99, 235, 0.15);
            transform: translateY(-2px);
        }
        .app-card-image { width: 100%; height: 160px; object-fit: cover; background: #e2e8f0; }
        .app-card-content { padding: 1.25rem; }
        .app-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.75rem; }
        .app-id { font-weight: 600; color: var(--secondary); }
        .app-type { font-size: 0.85rem; color: var(--text-gray); }
        .app-address { font-size: 0.9rem; color: var(--text-gray); margin-bottom: 1rem; display: flex; align-items: center; gap: 0.35rem; }
        .status-badge { padding: 0.25rem 0.75rem; border-radius: 20px; font-size: 0.75rem; font-weight: 600; }
        .status-approved { background: #d1fae5; color: #065f46; }
        .status-pending { background: #fef3c7; color: #92400e; }
        .status-review { background: #dbeafe; color: #1e40af; }
        .status-declined { background: #fee2e2; color: #991b1b; }
        .app-details { display: grid; grid-template-columns: repeat(2, 1fr); gap: 0.75rem; margin-bottom: 1rem; }
        .detail-item { font-size: 0.85rem; }
        .detail-label { color: var(--text-gray); margin-bottom: 0.25rem; }
        .detail-value { font-weight: 600; }
        .risk-score { display: flex; align-items: center; gap: 0.75rem; }
        .risk-bar { flex: 1; height: 8px; background: #e2e8f0; border-radius: 4px; overflow: hidden; }
        .risk-fill { height: 100%; border-radius: 4px; }
        .risk-low { background: var(--accent); }
        .risk-medium { background: var(--warning); }
        .risk-high { background: var(--danger); }
        .card-actions { display: flex; gap: 0.5rem; margin-top: 1rem; padding-top: 1rem; border-top: 1px solid #e2e8f0; }
        .card-btn { flex: 1; padding: 0.5rem 1rem; border-radius: 6px; font-size: 0.85rem; font-weight: 500; cursor: pointer; text-align: center; border: none; }
        .btn-details { background: var(--bg-light); color: var(--secondary); border: 1px solid #e2e8f0; }
        .btn-details:hover { border-color: var(--primary); color: var(--primary); }
        .btn-report { background: var(--secondary); color: white; }
        .btn-report:hover { background: #1e293b; }
        .sidebar { display: flex; flex-direction: column; gap: 2rem; }
        .form-card { background: white; border-radius: 16px; padding: 1.5rem; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); }
        .form-group { margin-bottom: 1.25rem; }
        .form-group label { display: block; font-weight: 500; margin-bottom: 0.5rem; font-size: 0.9rem; }
        .form-group input, .form-group select, .form-group textarea {
            width: 100%;
            padding: 0.75rem 1rem;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            font-size: 1rem;
        }
        .form-group input:focus, .form-group select:focus, .form-group textarea:focus {
            outline: none;
            border-color: var(--primary);
        }
        .form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }
        .form-row .form-group { margin-bottom: 0; }
        .submit-btn {
            width: 100%;
            background: var(--primary);
            color: white;
            border: none;
            padding: 1rem;
            border-radius: 8px;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 0.5rem;
        }
        .submit-btn:hover { background: var(--primary-dark); }
        .analysis-panel { background: var(--secondary); color: white; border-radius: 16px; padding: 1.5rem; }
        .analysis-panel .section-title { color: white; }
        .ai-indicator { display: flex; align-items: center; gap: 0.5rem; margin-bottom: 1rem; padding: 0.75rem; background: rgba(255,255,255,0.1); border-radius: 8px; }
        .pulse { width: 10px; height: 10px; background: var(--accent); border-radius: 50%; animation: pulse 2s infinite; }
        @keyframes pulse { 0%, 100% { opacity: 1; transform: scale(1); } 50% { opacity: 0.5; transform: scale(1.2); } }
        .analysis-items { display: flex; flex-direction: column; gap: 0.75rem; }
        .analysis-item { display: flex; justify-content: space-between; padding: 0.75rem; background: rgba(255,255,255,0.05); border-radius: 8px; }
        .analysis-label { opacity: 0.8; }
        .analysis-value { font-weight: 600; }
        .analysis-value.positive { color: var(--accent); }
        .analysis-value.warning { color: var(--warning); }
        .features { background: white; padding: 4rem 2rem; }
        .features-container { max-width: 1200px; margin: 0 auto; }
        .features-title { text-align: center; font-size: 2rem; margin-bottom: 3rem; }
        .features-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 2rem; }
        .feature-card { padding: 2rem; border-radius: 12px; background: var(--bg-light); text-align: center; }
        .feature-icon { width: 60px; height: 60px; background: var(--primary); border-radius: 12px; display: flex; align-items: center; justify-content: center; margin: 0 auto 1rem; }
        .feature-icon svg { width: 30px; height: 30px; color: white; stroke: white; }
        .feature-card h3 { margin-bottom: 0.5rem; }
        .feature-card p { color: var(--text-gray); font-size: 0.9rem; }

        /* Modal Styles */
        .modal-overlay {
            display: none;
            position: fixed;
            top: 0; left: 0; right: 0; bottom: 0;
            background: rgba(0,0,0,0.5);
            z-index: 2000;
            align-items: center;
            justify-content: center;
        }
        .modal-overlay.active { display: flex; }
        .modal {
            background: white;
            border-radius: 16px;
            padding: 2rem;
            max-width: 600px;
            width: 90%;
            max-height: 90vh;
            overflow-y: auto;
        }
        .modal-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem; }
        .modal-close { background: none; border: none; font-size: 1.5rem; cursor: pointer; color: var(--text-gray); }
        .modal-section { margin-bottom: 1.5rem; padding-bottom: 1.5rem; border-bottom: 1px solid #e2e8f0; }
        .modal-section:last-of-type { border-bottom: none; margin-bottom: 0; padding-bottom: 0; }
        .modal-section h4 { margin-bottom: 1rem; color: var(--text-gray); font-size: 0.85rem; text-transform: uppercase; letter-spacing: 0.05em; }
        .report-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; }
        .report-item { background: var(--bg-light); padding: 1rem; border-radius: 8px; }
        .report-item-label { font-size: 0.8rem; color: var(--text-gray); margin-bottom: 0.25rem; }
        .report-item-value { font-weight: 600; font-size: 1.1rem; }
        .ai-notes { background: var(--secondary); color: white; padding: 1.5rem; border-radius: 8px; }
        .ai-notes h5 { margin-bottom: 0.75rem; display: flex; align-items: center; gap: 0.5rem; }
        .ai-notes-content { white-space: pre-wrap; line-height: 1.6; opacity: 0.9; }
        .risk-summary { text-align: center; padding: 1.5rem; background: var(--bg-light); border-radius: 12px; margin-bottom: 1.5rem; }
        .risk-score-display { font-size: 3rem; font-weight: 700; }
        .risk-category { font-size: 1.1rem; font-weight: 600; }
        .recommendation-badge { display: inline-block; margin-top: 1rem; padding: 0.5rem 1rem; border-radius: 20px; font-weight: 600; }
        .breakdown-item { display: flex; justify-content: space-between; padding: 0.75rem; background: var(--bg-light); border-radius: 8px; margin-bottom: 0.5rem; }
        .breakdown-item span:last-child { font-weight: 600; }
        .loading { display: inline-block; width: 20px; height: 20px; border: 2px solid rgba(255,255,255,0.3); border-radius: 50%; border-top-color: white; animation: spin 1s linear infinite; }
        @keyframes spin { to { transform: rotate(360deg); } }
        footer { background: var(--secondary); color: white; padding: 2rem; text-align: center; }
        footer p { opacity: 0.7; }
        @media (max-width: 1024px) { .main-content { grid-template-columns: 1fr; } }
        @media (max-width: 768px) {
            .hero h1 { font-size: 2rem; }
            .hero-stats { flex-direction: column; gap: 1.5rem; }
            .nav-links { display: none; }
            .applications { grid-template-columns: 1fr; }
            .form-row { grid-template-columns: 1fr; }
            .report-grid { grid-template-columns: 1fr 1fr; }
        }
    </style>
</head>
<body>
    <nav>
        <div class="logo">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z"/>
                <polyline points="9 22 9 12 15 12 15 22"/>
            </svg>
            Sherlock Homes
        </div>
        <ul class="nav-links">
            <li><a href="#">Dashboard</a></li>
            <li><a href="#">Applications</a></li>
            <li><a href="#">Settings</a></li>
        </ul>
        <button class="nav-btn" onclick="openModal()">+ New Loan Application</button>
    </nav>

    <section class="hero">
        <h1>AI-Powered Mortgage Underwriting</h1>
        <p>Streamline single family home loan decisions with intelligent risk assessment and automated document analysis.</p>
        <div class="hero-stats">
            <div class="stat">
                <div class="stat-value">99.4%</div>
                <div class="stat-label">Approval Accuracy</div>
            </div>
            <div class="stat">
                <div class="stat-value">9.5s</div>
                <div class="stat-label">Avg. Decision Time</div>
            </div>
        </div>
    </section>

    <main class="main-content" id="dashboard">
        <div class="dashboard">
            <h2 class="section-title">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <rect x="3" y="3" width="18" height="18" rx="2"/>
                    <path d="M3 9h18M9 21V9"/>
                </svg>
                Recent Loan Applications
            </h2>
            <div class="applications">
                <div class="app-card">
                    <img src="https://images.unsplash.com/photo-1564013799919-ab600027ffc6?w=400&h=300&fit=crop" alt="Property" class="app-card-image">
                    <div class="app-card-content">
                        <div class="app-header">
                            <div>
                                <div class="app-id">LN-2024-08472</div>
                                <div class="app-type">30-Year Fixed Conventional</div>
                            </div>
                            <span class="status-badge status-approved">Approved</span>
                        </div>
                        <div class="app-address">
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0118 0z"/>
                                <circle cx="12" cy="10" r="3"/>
                            </svg>
                            1847 Oak Valley Dr, Austin, TX
                        </div>
                        <div class="app-details">
                            <div class="detail-item"><div class="detail-label">Borrower</div><div class="detail-value">James Morrison</div></div>
                            <div class="detail-item"><div class="detail-label">Loan Amount</div><div class="detail-value">$1,420,000</div></div>
                            <div class="detail-item"><div class="detail-label">Property Value</div><div class="detail-value">$1,775,000</div></div>
                            <div class="detail-item"><div class="detail-label">LTV</div><div class="detail-value">80.0%</div></div>
                        </div>
                        <div class="risk-score">
                            <span class="detail-label">Risk: 18</span>
                            <div class="risk-bar"><div class="risk-fill risk-low" style="width: 18%"></div></div>
                        </div>
                        <div class="card-actions">
                            <button class="card-btn btn-details" onclick="showDetails('LN-2024-08472')">View Details</button>
                            <button class="card-btn btn-report" onclick="viewReport('LN-2024-08472')">View Report</button>
                        </div>
                    </div>
                </div>

                <div class="app-card">
                    <img src="https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?w=400&h=300&fit=crop" alt="Property" class="app-card-image">
                    <div class="app-card-content">
                        <div class="app-header">
                            <div>
                                <div class="app-id">LN-2024-08471</div>
                                <div class="app-type">15-Year Fixed Conventional</div>
                            </div>
                            <span class="status-badge status-pending">Pending Docs</span>
                        </div>
                        <div class="app-address">
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0118 0z"/>
                                <circle cx="12" cy="10" r="3"/>
                            </svg>
                            2234 Maple Creek Ln, Denver, CO
                        </div>
                        <div class="app-details">
                            <div class="detail-item"><div class="detail-label">Borrower</div><div class="detail-value">Sarah Chen</div></div>
                            <div class="detail-item"><div class="detail-label">Loan Amount</div><div class="detail-value">$960,000</div></div>
                            <div class="detail-item"><div class="detail-label">Property Value</div><div class="detail-value">$1,280,000</div></div>
                            <div class="detail-item"><div class="detail-label">LTV</div><div class="detail-value">75.0%</div></div>
                        </div>
                        <div class="risk-score">
                            <span class="detail-label">Risk: 32</span>
                            <div class="risk-bar"><div class="risk-fill risk-low" style="width: 32%"></div></div>
                        </div>
                        <div class="card-actions">
                            <button class="card-btn btn-details" onclick="showDetails('LN-2024-08471')">View Details</button>
                            <button class="card-btn btn-report" onclick="viewReport('LN-2024-08471')">View Report</button>
                        </div>
                    </div>
                </div>

                <div class="app-card">
                    <img src="https://images.unsplash.com/photo-1600585154340-be6161a56a0c?w=400&h=300&fit=crop" alt="Property" class="app-card-image">
                    <div class="app-card-content">
                        <div class="app-header">
                            <div>
                                <div class="app-id">LN-2024-08470</div>
                                <div class="app-type">30-Year Fixed FHA</div>
                            </div>
                            <span class="status-badge status-review">Under Review</span>
                        </div>
                        <div class="app-address">
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0118 0z"/>
                                <circle cx="12" cy="10" r="3"/>
                            </svg>
                            789 Sunset Blvd, Phoenix, AZ
                        </div>
                        <div class="app-details">
                            <div class="detail-item"><div class="detail-label">Borrower</div><div class="detail-value">Michael Torres</div></div>
                            <div class="detail-item"><div class="detail-label">Loan Amount</div><div class="detail-value">$825,000</div></div>
                            <div class="detail-item"><div class="detail-label">Property Value</div><div class="detail-value">$865,000</div></div>
                            <div class="detail-item"><div class="detail-label">LTV</div><div class="detail-value">95.4%</div></div>
                        </div>
                        <div class="risk-score">
                            <span class="detail-label">Risk: 58</span>
                            <div class="risk-bar"><div class="risk-fill risk-medium" style="width: 58%"></div></div>
                        </div>
                        <div class="card-actions">
                            <button class="card-btn btn-details" onclick="showDetails('LN-2024-08470')">View Details</button>
                            <button class="card-btn btn-report" onclick="viewReport('LN-2024-08470')">View Report</button>
                        </div>
                    </div>
                </div>

                <div class="app-card">
                    <img src="https://images.unsplash.com/photo-1605276374104-dee2a0ed3cd6?w=400&h=300&fit=crop" alt="Property" class="app-card-image">
                    <div class="app-card-content">
                        <div class="app-header">
                            <div>
                                <div class="app-id">LN-2024-08469</div>
                                <div class="app-type">30-Year Fixed Conventional</div>
                            </div>
                            <span class="status-badge status-declined">Declined</span>
                        </div>
                        <div class="app-address">
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0118 0z"/>
                                <circle cx="12" cy="10" r="3"/>
                            </svg>
                            456 Pine Ridge Way, Seattle, WA
                        </div>
                        <div class="app-details">
                            <div class="detail-item"><div class="detail-label">Borrower</div><div class="detail-value">Robert Blake</div></div>
                            <div class="detail-item"><div class="detail-label">Loan Amount</div><div class="detail-value">$2,150,000</div></div>
                            <div class="detail-item"><div class="detail-label">Property Value</div><div class="detail-value">$2,250,000</div></div>
                            <div class="detail-item"><div class="detail-label">LTV</div><div class="detail-value">95.6%</div></div>
                        </div>
                        <div class="risk-score">
                            <span class="detail-label">Risk: 84</span>
                            <div class="risk-bar"><div class="risk-fill risk-high" style="width: 84%"></div></div>
                        </div>
                        <div class="card-actions">
                            <button class="card-btn btn-details" onclick="showDetails('LN-2024-08469')">View Details</button>
                            <button class="card-btn btn-report" onclick="viewReport('LN-2024-08469')">View Report</button>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <div class="sidebar">
            <div class="form-card">
                <h3 class="section-title">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/>
                        <path d="M14 2v6h6M12 18v-6M9 15h6"/>
                    </svg>
                    Quick Pre-Qualification
                </h3>
                <form id="quickForm" onsubmit="runQuickAssessment(event)">
                    <div class="form-group">
                        <label>Credit Score</label>
                        <input type="number" id="qf_credit" placeholder="e.g., 720" min="300" max="850" required>
                    </div>
                    <div class="form-row">
                        <div class="form-group">
                            <label>Loan Amount</label>
                            <input type="number" id="qf_loan" placeholder="e.g., 350000" required>
                        </div>
                        <div class="form-group">
                            <label>Property Value</label>
                            <input type="number" id="qf_value" placeholder="e.g., 425000" required>
                        </div>
                    </div>
                    <div class="form-group">
                        <label>Annual Income</label>
                        <input type="number" id="qf_income" placeholder="e.g., 120000" required>
                    </div>
                    <button type="submit" class="submit-btn" id="qf_btn">
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <circle cx="12" cy="12" r="10"/>
                            <path d="M12 6v6l4 2"/>
                        </svg>
                        Quick Check
                    </button>
                </form>
            </div>

            <div class="analysis-panel">
                <h3 class="section-title">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M12 2a10 10 0 1010 10H12V2z"/>
                        <path d="M12 2a10 10 0 00-8.5 15"/>
                    </svg>
                    AI Analysis Engine
                </h3>
                <div class="ai-indicator">
                    <div class="pulse"></div>
                    <span>System Active - Ready</span>
                </div>
                <div class="analysis-items">
                    <div class="analysis-item"><span class="analysis-label">Credit Analysis</span><span class="analysis-value positive">Excellent</span></div>
                    <div class="analysis-item"><span class="analysis-label">DTI Ratio</span><span class="analysis-value positive">32%</span></div>
                    <div class="analysis-item"><span class="analysis-label">LTV Ratio</span><span class="analysis-value warning">89%</span></div>
                    <div class="analysis-item"><span class="analysis-label">Income Verified</span><span class="analysis-value positive">Yes</span></div>
                </div>
            </div>
        </div>
    </main>

    <section class="features">
        <div class="features-container">
            <h2 class="features-title">Intelligent Mortgage Underwriting</h2>
            <div class="features-grid">
                <div class="feature-card">
                    <div class="feature-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/></svg></div>
                    <h3>Instant Decisions</h3>
                    <p>AI processes loan applications in seconds, providing immediate pre-qualification decisions.</p>
                </div>
                <div class="feature-card">
                    <div class="feature-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><path d="M14 2v6h6M16 13H8M16 17H8M10 9H8"/></svg></div>
                    <h3>Document Analysis</h3>
                    <p>Automated extraction and verification of W-2s, tax returns, bank statements, and pay stubs.</p>
                </div>
                <div class="feature-card">
                    <div class="feature-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg></div>
                    <h3>Risk Assessment</h3>
                    <p>Comprehensive analysis of DTI, LTV, credit history, and employment stability.</p>
                </div>
                <div class="feature-card">
                    <div class="feature-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="1" y="4" width="22" height="16" rx="2"/><path d="M1 10h22"/></svg></div>
                    <h3>Compliance Check</h3>
                    <p>Automatic verification against Fannie Mae, Freddie Mac, FHA, and VA guidelines.</p>
                </div>
            </div>
        </div>
    </section>

    <!-- New Application Modal -->
    <div class="modal-overlay" id="appModal">
        <div class="modal">
            <div class="modal-header">
                <h3>New Loan Application</h3>
                <button class="modal-close" onclick="closeModal()">&times;</button>
            </div>
            <form id="appForm" onsubmit="submitApplication(event)">
                <div class="modal-section">
                    <h4>Borrower Information</h4>
                    <div class="form-group">
                        <label>Full Legal Name *</label>
                        <input type="text" id="borrower_name" required>
                    </div>
                    <div class="form-row">
                        <div class="form-group">
                            <label>Credit Score *</label>
                            <input type="number" id="credit_score" placeholder="e.g., 720" min="300" max="850" required>
                        </div>
                        <div class="form-group">
                            <label>Annual Income *</label>
                            <input type="number" id="annual_income" placeholder="e.g., 120000" required>
                        </div>
                    </div>
                    <div class="form-row">
                        <div class="form-group">
                            <label>Monthly Debts *</label>
                            <input type="number" id="monthly_debts" placeholder="e.g., 800" required>
                        </div>
                        <div class="form-group">
                            <label>Employment Years *</label>
                            <input type="number" id="employment_years" placeholder="e.g., 5" min="0" required>
                        </div>
                    </div>
                </div>

                <div class="modal-section">
                    <h4>Loan Details</h4>
                    <div class="form-row">
                        <div class="form-group">
                            <label>Loan Amount *</label>
                            <input type="number" id="loan_amount" placeholder="e.g., 450000" required>
                        </div>
                        <div class="form-group">
                            <label>Property Value *</label>
                            <input type="number" id="property_value" placeholder="e.g., 550000" required>
                        </div>
                    </div>
                    <div class="form-row">
                        <div class="form-group">
                            <label>Loan Type *</label>
                            <select id="loan_type" required>
                                <option value="">Select...</option>
                                <option value="30-Year Fixed Conventional">30-Year Fixed Conventional</option>
                                <option value="15-Year Fixed Conventional">15-Year Fixed Conventional</option>
                                <option value="30-Year Fixed FHA">30-Year Fixed FHA</option>
                                <option value="30-Year Fixed VA">30-Year Fixed VA</option>
                                <option value="7/1 ARM">7/1 ARM</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label>Reserves (Months) *</label>
                            <input type="number" id="reserves_months" placeholder="e.g., 6" min="0" required>
                        </div>
                    </div>
                    <div class="form-group">
                        <label>Property Address *</label>
                        <input type="text" id="property_address" placeholder="123 Main St, City, State" required>
                    </div>
                </div>

                <div class="modal-section">
                    <h4>Online Presence (Optional)</h4>
                    <div class="form-group">
                        <label>LinkedIn URL</label>
                        <input type="url" id="linkedin_url" placeholder="https://linkedin.com/in/...">
                    </div>
                </div>

                <button type="submit" class="submit-btn" id="submit_btn">Submit for AI Underwriting</button>
            </form>
        </div>
    </div>

    <!-- Report Modal -->
    <div class="modal-overlay" id="reportModal">
        <div class="modal" style="max-width: 700px;">
            <div class="modal-header">
                <h3>AI Underwriting Report - <span id="reportAppId"></span></h3>
                <button class="modal-close" onclick="closeReportModal()">&times;</button>
            </div>

            <div class="risk-summary">
                <div class="report-item-label">Composite Risk Score</div>
                <div class="risk-score-display" id="riskScoreDisplay">--</div>
                <div class="risk-category" id="riskCategory">--</div>
                <div class="recommendation-badge" id="recommendation">--</div>
            </div>

            <div class="modal-section">
                <h4>Loan Summary</h4>
                <div class="report-grid">
                    <div class="report-item"><div class="report-item-label">Borrower</div><div class="report-item-value" id="rptBorrower">--</div></div>
                    <div class="report-item"><div class="report-item-label">Loan Amount</div><div class="report-item-value" id="rptLoanAmount">--</div></div>
                    <div class="report-item"><div class="report-item-label">Property Value</div><div class="report-item-value" id="rptPropertyValue">--</div></div>
                    <div class="report-item"><div class="report-item-label">LTV Ratio</div><div class="report-item-value" id="rptLTV">--</div></div>
                    <div class="report-item"><div class="report-item-label">DTI Ratio</div><div class="report-item-value" id="rptDTI">--</div></div>
                    <div class="report-item"><div class="report-item-label">Loan Type</div><div class="report-item-value" id="rptLoanType">--</div></div>
                </div>
            </div>

            <div class="modal-section">
                <h4>Risk Score Breakdown</h4>
                <div class="breakdown-item"><span>Credit Score Risk (35%)</span><span id="bdCredit">--</span></div>
                <div class="breakdown-item"><span>DTI Risk (25%)</span><span id="bdDTI">--</span></div>
                <div class="breakdown-item"><span>LTV Risk (20%)</span><span id="bdLTV">--</span></div>
                <div class="breakdown-item"><span>Employment Risk (10%)</span><span id="bdEmployment">--</span></div>
                <div class="breakdown-item"><span>Reserves Risk (10%)</span><span id="bdReserves">--</span></div>
                <div class="breakdown-item" style="background: #eff6ff; border: 1px solid var(--primary);"><span style="color: var(--primary);">Feature Modifiers</span><span id="bdModifiers" style="color: var(--primary);">--</span></div>
            </div>

            <div class="modal-section">
                <h4>AI Analysis</h4>
                <div class="ai-notes">
                    <h5><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg> Sherlock Homes Assessment</h5>
                    <div class="ai-notes-content" id="rptAnalysis">--</div>
                </div>
            </div>

            <div style="text-align: center; margin-top: 1rem;">
                <button class="submit-btn" style="width: auto; padding: 0.75rem 2rem;" onclick="window.print()">Print Report</button>
            </div>
        </div>
    </div>

    <footer>
        <p>&copy; 2026 Sherlock Homes. Single Family Home Loan Underwriting Platform.</p>
    </footer>

    <script>
        function openModal() { document.getElementById('appModal').classList.add('active'); }
        function closeModal() { document.getElementById('appModal').classList.remove('active'); }
        function closeReportModal() { document.getElementById('reportModal').classList.remove('active'); }

        function showDetails(appId) { alert('Viewing details for ' + appId); }

        async function viewReport(appId) {
            document.getElementById('reportAppId').textContent = appId;
            try {
                const response = await fetch('/api/test-cases/' + appId);
                const result = await response.json();
                if (result.status === 'success') {
                    displayReport(result.report, result.case);
                }
            } catch (e) { console.log('Using static data'); }
            document.getElementById('reportModal').classList.add('active');
        }

        function runQuickAssessment(e) {
            e.preventDefault();
            const credit = parseInt(document.getElementById('qf_credit').value);
            const loan = parseFloat(document.getElementById('qf_loan').value);
            const value = parseFloat(document.getElementById('qf_value').value);
            const income = parseFloat(document.getElementById('qf_income').value);
            const ltv = (loan / value * 100).toFixed(1);
            const dti = ((loan * 0.006 + 500) / (income / 12) * 100).toFixed(1);
            let risk = 'Low';
            if (credit < 680 || ltv > 90 || dti > 43) risk = 'High';
            else if (credit < 720 || ltv > 80 || dti > 36) risk = 'Medium';
            alert('Quick Assessment Results:\\n\\nLTV: ' + ltv + '%\\nEst. DTI: ' + dti + '%\\nRisk Level: ' + risk);
        }

        async function submitApplication(e) {
            e.preventDefault();
            const btn = document.getElementById('submit_btn');
            btn.innerHTML = '<div class="loading"></div> Processing...';
            btn.disabled = true;

            const formData = {
                borrower_name: document.getElementById('borrower_name').value,
                credit_score: parseInt(document.getElementById('credit_score').value),
                annual_income: parseFloat(document.getElementById('annual_income').value),
                monthly_debts: parseFloat(document.getElementById('monthly_debts').value),
                employment_years: parseInt(document.getElementById('employment_years').value),
                loan_amount: parseFloat(document.getElementById('loan_amount').value),
                property_value: parseFloat(document.getElementById('property_value').value),
                loan_type: document.getElementById('loan_type').value,
                reserves_months: parseInt(document.getElementById('reserves_months').value),
                property_address: document.getElementById('property_address').value,
                linkedin_url: document.getElementById('linkedin_url').value || null
            };

            try {
                const response = await fetch('/api/score', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(formData)
                });
                const result = await response.json();
                if (result.status === 'success') {
                    closeModal();
                    displayReport(result.report, formData);
                    document.getElementById('reportModal').classList.add('active');
                } else {
                    alert('Error: ' + (result.message || 'Failed to process'));
                }
            } catch (error) {
                alert('Failed to connect to server');
            } finally {
                btn.innerHTML = 'Submit for AI Underwriting';
                btn.disabled = false;
            }
        }

        function displayReport(report, formData) {
            document.getElementById('reportAppId').textContent = 'NEW-' + Date.now().toString().slice(-6);
            const score = report.risk_score;
            const scoreEl = document.getElementById('riskScoreDisplay');
            const catEl = document.getElementById('riskCategory');
            const recEl = document.getElementById('recommendation');

            scoreEl.textContent = score;
            catEl.textContent = report.risk_category;

            if (score <= 30) { scoreEl.style.color = 'var(--accent)'; recEl.style.background = '#d1fae5'; recEl.style.color = '#065f46'; recEl.textContent = 'APPROVE'; }
            else if (score <= 50) { scoreEl.style.color = 'var(--warning)'; recEl.style.background = '#fef3c7'; recEl.style.color = '#92400e'; recEl.textContent = 'CONDITIONAL'; }
            else if (score <= 70) { scoreEl.style.color = '#f97316'; recEl.style.background = '#ffedd5'; recEl.style.color = '#9a3412'; recEl.textContent = 'REVIEW'; }
            else { scoreEl.style.color = 'var(--danger)'; recEl.style.background = '#fee2e2'; recEl.style.color = '#991b1b'; recEl.textContent = 'DECLINE'; }

            document.getElementById('rptBorrower').textContent = formData.borrower_name || formData.borrower || '--';
            document.getElementById('rptLoanAmount').textContent = formatCurrency(formData.loan_amount);
            document.getElementById('rptPropertyValue').textContent = formatCurrency(formData.property_value);
            document.getElementById('rptLTV').textContent = (report.ltv || 0).toFixed(1) + '%';
            document.getElementById('rptDTI').textContent = (report.dti || 0).toFixed(1) + '%';
            document.getElementById('rptLoanType').textContent = formData.loan_type;

            if (report.score_breakdown) {
                const bd = report.score_breakdown;
                document.getElementById('bdCredit').textContent = bd.credit_risk.toFixed(1) + ' pts';
                document.getElementById('bdDTI').textContent = bd.dti_risk.toFixed(1) + ' pts';
                document.getElementById('bdLTV').textContent = bd.ltv_risk.toFixed(1) + ' pts';
                document.getElementById('bdEmployment').textContent = bd.employment_risk.toFixed(1) + ' pts';
                document.getElementById('bdReserves').textContent = bd.reserves_risk.toFixed(1) + ' pts';
                const mod = bd.feature_modifiers || 0;
                document.getElementById('bdModifiers').textContent = (mod >= 0 ? '+' : '') + mod.toFixed(1) + ' pts';
            }

            const analysisEl = document.getElementById('rptAnalysis');
            if (report.ai_analysis && !report.ai_analysis.includes('not configured')) {
                analysisEl.textContent = report.ai_analysis;
            } else {
                let notes = [];
                const cs = formData.credit_score || report.credit_score;
                if (cs >= 740) notes.push('Excellent credit score indicates strong repayment history.');
                else if (cs >= 680) notes.push('Good credit score meets conventional loan requirements.');
                else notes.push('Credit score below optimal range.');
                if (report.dti <= 36) notes.push('DTI ratio within healthy limits.');
                else if (report.dti <= 43) notes.push('DTI ratio approaching upper limits.');
                else notes.push('High DTI ratio presents risk.');
                if (report.ltv <= 80) notes.push('Strong LTV - no PMI required.');
                analysisEl.textContent = notes.join('\\n\\n');
            }
        }

        function formatCurrency(amount) {
            return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', minimumFractionDigits: 0, maximumFractionDigits: 0 }).format(amount);
        }

        document.getElementById('appModal').addEventListener('click', function(e) { if (e.target === this) closeModal(); });
        document.getElementById('reportModal').addEventListener('click', function(e) { if (e.target === this) closeReportModal(); });
        document.addEventListener('keydown', function(e) { if (e.key === 'Escape') { closeModal(); closeReportModal(); } });
    </script>
</body>
</html>'''


# =============================================================================
# API ROUTES
# =============================================================================

@app.route('/')
def index():
    """Serve the frontend."""
    return Response(FRONTEND_HTML, mimetype='text/html')


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        "status": "ok",
        "service": "Sherlock Homes API",
        "scorer_available": SCORER_AVAILABLE
    })


@app.route('/api/score', methods=['POST'])
def score_application():
    """Score a loan application."""
    try:
        data = request.get_json()

        if not data:
            return jsonify({"status": "error", "message": "No data provided"}), 400

        if not SCORER_AVAILABLE:
            return jsonify({
                "status": "error",
                "message": "Risk scorer not available. Check risk_scorer.py imports."
            }), 500

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
    if not SCORER_AVAILABLE:
        return jsonify({"status": "error", "message": "Scorer not available"}), 500

    try:
        scorer = RiskScorer()
        results = []
        for case in TEST_CASES:
            report = scorer.score_application(case)
            results.append({"case": case, "report": report.to_dict()})
        return jsonify({"status": "success", "results": results})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/test-cases/<case_id>', methods=['GET'])
def get_test_case(case_id):
    """Get a specific test case with its score."""
    if not SCORER_AVAILABLE:
        return jsonify({"status": "error", "message": "Scorer not available"}), 500

    try:
        case = next((c for c in TEST_CASES if c["id"] == case_id), None)
        if not case:
            return jsonify({"status": "error", "message": f"Case {case_id} not found"}), 404

        scorer = RiskScorer()
        report = scorer.score_application(case)
        return jsonify({"status": "success", "case": case, "report": report.to_dict()})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# =============================================================================
# MAIN
# =============================================================================

def open_browser():
    """Open browser after a short delay."""
    time.sleep(1.5)
    webbrowser.open('http://localhost:5000')


if __name__ == '__main__':
    try:
        print()
        print("=" * 50)
        print("  SHERLOCK HOMES - AI Mortgage Underwriting")
        print("=" * 50)
        print()
        print("  Server starting at: http://localhost:5000")
        print("  Opening browser automatically...")
        print()
        print("  Press Ctrl+C to stop the server")
        print("=" * 50)
        print()

        # Open browser in background thread
        threading.Thread(target=open_browser, daemon=True).start()

        # Run Flask server
        app.run(debug=False, port=5000, host='0.0.0.0')

    except Exception as e:
        print()
        print("=" * 50)
        print("  ERROR")
        print("=" * 50)
        print(f"\n  {e}")
        print()
        input("  Press Enter to exit...")
        sys.exit(1)
