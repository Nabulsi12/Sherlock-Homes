"""
Custom Exception Classes
"""


class SherlockException(Exception):
    """Base exception for Sherlocke Homes application"""
    pass


class ValidationException(SherlockException):
    """Raised when validation fails"""
    pass


class ComplianceException(SherlockException):
    """Raised when compliance check fails"""
    pass


class RiskCalculationException(SherlockException):
    """Raised when risk calculation fails"""
    pass


class AIServiceException(SherlockException):
    """Raised when AI service encounters an error"""
    pass
