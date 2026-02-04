# Sherlocke Homes - Backend API

AI-Powered Loan Underwriting Platform Backend

## Quick Start

### 1. Prerequisites
- Python 3.9+
- pip
- Keywords AI API key (get from https://keywordsai.co)

### 2. Installation

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration

```bash
# Copy example environment file
cp .env.example .env

# Edit .env and add your Keywords AI API key
# Required: KEYWORDS_AI_API_KEY
# Note: DO NOT use quotes around the API key
```

### 4. Run the Server

```bash
# From the backend directory
python -m app.main

# Or using uvicorn directly
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:
- API: http://localhost:8000
- Interactive Docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Project Structure

```
backend/
├── app/
│   ├── api/v1/
│   │   ├── routes/
│   │   │   ├── health.py              # Health check endpoints
│   │   │   ├── loan_applications.py   # Loan application endpoints
│   │   │   └── reports.py             # Report generation endpoints
│   │   └── api.py                     # Route aggregator
│   │
│   ├── models/
│   │   └── schemas.py                 # Pydantic models
│   │
│   ├── services/
│   │   ├── ai_agent.py               # Main AI orchestration
│   │   ├── risk_calculator.py        # Risk assessment logic
│   │   ├── compliance_checker.py     # Regulatory compliance
│   │   └── data_gatherer.py          # Data collection
│   │
│   ├── utils/
│   │   ├── logger.py                 # Logging configuration
│   │   └── validators.py             # Input validation
│   │
│   ├── core/
│   │   └── exceptions.py             # Custom exceptions
│   │
│   ├── config.py                     # Configuration management
│   ├── dependencies.py               # Dependency injection
│   └── main.py                       # FastAPI app entry point
│
├── tests/                            # Test suite
├── requirements.txt                  # Python dependencies
├── .env.example                     # Environment variables template
└── README.md                        # This file
```

## API Endpoints

### Health Check
```
GET /api/v1/health
```

### Submit Loan Application
```
POST /api/v1/loan-applications
Content-Type: application/json

{
  "applicant": {
    "full_name": "John Doe",
    "email": "john@example.com",
    "phone": "555-123-4567",
    "credit_score": 720,
    "annual_income": 85000,
    "years_employed": 5
  },
  "property_info": {
    "address": "123 Main St, City, State 12345",
    "estimated_value": 425000,
    "property_type": "Single Family Detached",
    "occupancy": "Primary Residence"
  },
  "loan_details": {
    "loan_amount": 350000,
    "loan_type": "30-Year Fixed Conventional",
    "loan_purpose": "Purchase"
  }
}
```

### Get Application
```
GET /api/v1/loan-applications/{application_id}
```

### List Applications
```
GET /api/v1/loan-applications?skip=0&limit=10
```

## How It Works

### 1. Application Submission
When a loan application is submitted via POST /api/v1/loan-applications, the system:

### 2. AI Agent Orchestration
The `AIAgentService` coordinates:
- **Data Gathering**: Collects additional information about the applicant
- **Risk Assessment**: Calculates comprehensive risk scores
- **Compliance Check**: Validates against Fannie Mae/Freddie Mac guidelines
- **Report Generation**: Creates executive summary and detailed analysis

### 3. Risk Calculation
The `RiskCalculatorService` analyzes:
- Credit score risk
- DTI (Debt-to-Income) ratio
- LTV (Loan-to-Value) ratio
- Employment stability
- Income verification
- Property type and occupancy

### 4. Compliance Checking
The `ComplianceCheckerService` validates:
- Minimum credit score requirements
- Maximum DTI ratio limits
- Maximum LTV ratio limits
- Income documentation standards
- Property eligibility
- Occupancy requirements

### 5. Data Gathering
The `DataGathererService` uses AI to:
- Verify employment information
- Validate income claims
- Check social media presence
- Identify red flags or positive factors

## Development

### Running Tests
```bash
pytest
```

### Code Formatting
```bash
# Format code
black app/

# Sort imports
isort app/

# Lint
flake8 app/
```

### Type Checking
```bash
mypy app/
```

## Team Development Guide

### Adding New Endpoints
1. Create route file in `app/api/v1/routes/`
2. Define route handlers
3. Import and include in `app/api/v1/api.py`

### Adding New Services
1. Create service file in `app/services/`
2. Implement service class
3. Import in `app/services/__init__.py`
4. Use in routes via dependency injection

### Adding New Models
1. Define Pydantic models in `app/models/schemas.py`
2. Export from `app/models/__init__.py`

### Environment Variables
Add new variables in:
1. `app/config.py` (Settings class)
2. `.env.example` (documentation)
3. Your local `.env` file

## Production Considerations

For production deployment, consider:

1. **Security**
   - Enable authentication/authorization
   - Use HTTPS
   - Validate all inputs
   - Rate limiting
   - API key management

2. **Database**
   - Add PostgreSQL/MongoDB for persistence
   - Implement database models
   - Add migration system

3. **Monitoring**
   - Add application monitoring (Sentry, DataDog)
   - Implement health checks
   - Log aggregation

4. **Performance**
   - Add caching (Redis)
   - Implement background job processing
   - Optimize AI API calls

5. **Compliance**
   - Implement proper audit logging
   - Add data encryption
   - GDPR/privacy compliance

## Troubleshooting

### Common Issues

**Issue**: Import errors
**Solution**: Make sure you're in the backend directory and virtual environment is activated

**Issue**: Missing CLAUDE_API_KEY
**Solution**: Set CLAUDE_API_KEY in .env file

**Issue**: Port 8000 already in use
**Solution**: Change port in command: `uvicorn app.main:app --port 8001`

## Support

For questions or issues:
1. Check API documentation at http://localhost:8000/docs
2. Review error logs
3. Consult team members

## License

Hackathon Project - January 31, 2026
