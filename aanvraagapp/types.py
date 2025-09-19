from enum import Enum, auto
from typing import Literal

class TargetAudience(str, Enum):
    SME = auto()
    AGRICULTURE = auto()
    FINANCIAL_INSTITUTION = auto()
    LARGE_COMPANY = auto()
    NGO_OR_NON_PROFIT = auto()
    PUBLIC_SECTOR = auto()
    PRIVATE_INDIVIDUALS = auto()
    SCHOOL_OR_EDUCATIONAL_INSTITUTION = auto()
    OTHER = auto()
    
    @classmethod
    def get_documentation(cls) -> str:
        return """
        - SME: Small and Medium Enterprises. In Dutch called "MKB".
        - FINANCIAL_INSTITUTION: Banks, credit unions, and other financial entities.
        - LARGE_COMPANY: Large corporations and enterprises. In Dutch called "Midden/Groot bedrijf".
        - OTHER: Choose this if no other option applies.
        """

class FinancialInstrument(str, Enum):
    SUBSIDY = auto()
    LOAN = auto()
    LOAN_GUARANTEE = auto()
    OTHER = auto()
    
    @classmethod
    def get_documentation(cls) -> str:
        return """
        - OTHER: Choose this if no other option applies.
        """


AIProvider = Literal["gemini", "ollama"]