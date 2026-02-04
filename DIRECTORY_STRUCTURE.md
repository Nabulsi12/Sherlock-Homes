# Sherlocke Homes - Complete Directory Structure

## Project Overview
```
Keywords-AI-January-31st/
├── backend/                          # FastAPI Backend
├── claude.md                         # Product specification
├── underwriting-ai.html              # Frontend demo
├── Fannie Mae December 10, 2025 Selling Guide.pdf
└── DIRECTORY_STRUCTURE.md           # This file
```

## Backend Structure (Complete)

```
backend/
│
├── app/                             # Main application package
│   │
│   ├── __init__.py                 # Package initialization
│   ├── main.py                     # FastAPI app entry point ⭐
│   ├── config.py                   # Configuration management
│   ├── dependencies.py             # Dependency injection
│   │
│   ├── api/                        # API routes
│   │   ├── __init__.py
│   │   └── v1/                     # API version 1
│   │       ├── __init__.py
│   │       ├── api.py              # Route aggregator
│   │       └── routes/             # Individual route modules
│   │           ├── __init__.py
│   │           ├── health.py       # Health check endpoints
│   │           ├── loan_applications.py  # Main loan endpoints ⭐
│   │           └── reports.py      # Report generation
│   │
│   ├── models/                     # Data models
│   │   ├── __init__.py
│   │   └── schemas.py              # Pydantic schemas ⭐
│   │
│   ├── services/                   # Business logic ⭐⭐⭐
│   │   ├── __init__.py
│   │   ├── ai_agent.py            # Main AI orchestrator
│   │   ├── risk_calculator.py     # Risk assessment engine
│   │   ├── compliance_checker.py  # Regulatory compliance
│   │   └── data_gatherer.py       # Data collection AI
│   │
│   ├── utils/                      # Utility functions
│   │   ├── __init__.py
│   │   ├── logger.py              # Logging setup
│   │   └── validators.py          # Input validation
│   │
│   └── core/                       # Core functionality
│       ├── __init__.py
│       └── exceptions.py           # Custom exceptions
│
├── tests/                          # Test suite
│   ├── __init__.py
│   ├── test_api/
│   │   ├── __init__.py
│   │   └── test_loan_applications.py
│   └── test_services/
│       ├── __init__.py
│       └── test_risk_calculator.py
│
├── requirements.txt                # Python dependencies
├── .env.example                   # Environment variables template
├── .gitignore                     # Git ignore rules
├── README.md                      # Setup and documentation ⭐
├── run.sh                         # Quick start (Unix/macOS)
└── run.bat                        # Quick start (Windows)
```

## Key Files Explained

### Entry Points
- **backend/app/main.py** - FastAPI application entry point, CORS setup, route registration
- **backend/run.bat** / **backend/run.sh** - Quick start scripts for your team

### API Routes
- **backend/app/api/v1/routes/loan_applications.py** - Main loan processing endpoint
- **backend/app/api/v1/routes/health.py** - Health check for monitoring
- **backend/app/api/v1/routes/reports.py** - Report generation (placeholder)

### Data Models
- **backend/app/models/schemas.py** - All Pydantic models:
  - LoanApplicationRequest
  - LoanApplicationResponse
  - RiskAssessment
  - ComplianceCheck
  - GatheredData

### Core Services (The Brain)
- **backend/app/services/ai_agent.py** - Orchestrates the entire analysis pipeline
- **backend/app/services/risk_calculator.py** - Calculates DTI, LTV, risk scores
- **backend/app/services/compliance_checker.py** - Validates Fannie Mae/Freddie Mac rules
- **backend/app/services/data_gatherer.py** - AI-powered data collection

### Configuration
- **backend/app/config.py** - Settings class using Pydantic
- **backend/.env.example** - Template for environment variables
- **backend/.env** - Your actual config (create from .env.example)

## Team Roles & Files

### Frontend Developers
Focus on:
- `underwriting-ai.html` (existing)
- Connect to API at `http://localhost:8000/api/v1/loan-applications`
- Review `backend/app/models/schemas.py` for request/response formats

### Backend Developers
Focus on:
- `backend/app/services/*.py` - Implement AI logic
- `backend/app/api/v1/routes/*.py` - Add endpoints
- `backend/tests/` - Write tests

### AI/ML Engineers
Focus on:
- `backend/app/services/ai_agent.py` - Claude prompt engineering
- `backend/app/services/data_gatherer.py` - Data collection logic
- `backend/app/services/compliance_checker.py` - PDF analysis

### DevOps
Focus on:
- `backend/requirements.txt` - Dependencies
- `backend/.env` - Configuration
- `backend/run.sh` / `run.bat` - Deployment scripts

## Quick Start Commands

### Backend Setup
```bash
cd backend

# Windows
run.bat

# Unix/macOS/Linux
chmod +x run.sh
./run.sh

# Or manual:
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
cp .env.example .env
# Edit .env and add CLAUDE_API_KEY
python -m app.main
```

### Access Points
- API: http://localhost:8000
- Interactive Docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## File Count Summary
- Python files: 31
- Config files: 4
- Documentation: 2
- Scripts: 2

**Total: 39 files organized in a production-ready structure**

## Next Steps for Your Team

1. **Backend Team**: Set up environment and test the API
   ```bash
   cd backend
   pip install -r requirements.txt
   cp .env.example .env
   # Add your CLAUDE_API_KEY to .env
   python -m app.main
   ```

2. **Frontend Team**: Update HTML to call the backend API
   - Endpoint: POST http://localhost:8000/api/v1/loan-applications
   - See schemas.py for exact JSON format

3. **AI Team**: Enhance the AI agent prompts in services/

4. **Testing Team**: Run tests and add more
   ```bash
   pytest
   ```

## Notes
- ⭐ = Critical files to review
- All services use async/await for performance
- Claude API integrated throughout
- Compliance checking references Fannie Mae PDF
- Ready for immediate development
