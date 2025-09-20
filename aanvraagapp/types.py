from enum import StrEnum, auto
from typing import Literal

class TargetAudience(StrEnum):
    SME = auto()
    AGRICULTURE = auto()
    FINANCIAL_INSTITUTION = auto()
    LARGE_COMPANY = auto()
    NGO_OR_NON_PROFIT = auto()
    PUBLIC_SECTOR = auto()
    PRIVATE_INDIVIDUALS = auto()
    SCHOOL_OR_EDUCATIONAL_INSTITUTION = auto()
    PRIVATE_PUBLIC_COLLABORATION = auto()
    OTHER = auto()
    
    @classmethod
    def get_documentation(cls) -> str:
        return """
        - SME: Small and Medium Enterprises. In Dutch called "MKB".
        - FINANCIAL_INSTITUTION: Banks, credit unions, and other financial entities.
        - LARGE_COMPANY: Large corporations and enterprises. In Dutch called "Midden/Groot bedrijf".
        - PUBLIC_SECTOR: Municipalities, provinces, government agencies, etc.
        - OTHER: Choose this if no other option applies.
        """

class FinancialInstrument(StrEnum):
    SUBSIDY = auto()
    LOAN = auto()
    LOAN_GUARANTEE = auto()
    OTHER = auto()
    
    @classmethod
    def get_documentation(cls) -> str:
        return """
        - LOAN_GUARANTEE: A construction where there is an entity that is willing to offer collateral so that a loan can be granted.
        - OTHER: Choose this if no other option applies.
        """


AIProvider = Literal["gemini", "ollama"]