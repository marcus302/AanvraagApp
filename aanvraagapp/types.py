from enum import StrEnum, auto
from typing import Literal
import textwrap
from inspect import cleandoc

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


class BusinessIdentity(StrEnum):
    SME = auto()
    AGRICULTURE = auto()
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


class ConditionEval(StrEnum):
    PASSES = auto()
    UNCLEAR = auto()
    FAILS = auto()
    OPPORTUNITY = auto()

    @classmethod
    def get_documentation(cls) -> str:
        return """
        - PASSES: We can say with near certainty that the condition is fully met.
        - UNCLEAR: There is not enough information to say that the condition is met or not. We are reasonably sure that the client cannot adapt to this condition and become eligible.
        - FAILS: We can say with near certainty that the client fails to meet the condition for this listing.
        - OPPORTUNITY: There is no clear indication that this condition is met, but this is a reasonable opportunity for the client to adapt to the condition and become eligible.
        """


class MatchEval(StrEnum):
    BAD = auto()
    UNCLEAR = auto()
    INTERESTING = auto()
    VERY_GOOD = auto()

    @classmethod
    def get_documentation(cls) -> str:
        return """
        - BAD: The match has a very low chance of relevance or success.
        - UNCLEAR: There is not enough information to consider this to be a bad or good match.
        - INTERESTING: There are no reasons to think that the client can't be eligble.
        - VERY_GOOD: This is a match made in heaven. This client is most definitely eligble.
        """


AIProvider = Literal["gemini", "ollama"]