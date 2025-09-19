from datetime import date
from pydantic import BaseModel
from aanvraagapp.types import TargetAudience, FinancialInstrument


class ListingFieldData(BaseModel):
    is_open: bool | None
    opens_at: date | None
    closes_at: date | None
    last_checked: date | None
    name: str
    target_audience: TargetAudience
    financial_instrument: FinancialInstrument
    target_audience_desc: str
    
    @classmethod
    def get_documentation(cls) -> str:
        return f"""
        ListingFieldData represents information about a subsidy:

        Use None if you cannot determine the proper value or if the necessary information is missing.

        Additional information about (some) fields or values:
        
        Fields:
        - is_open: Whether the subsidy application is currently open for submissions
        - opens_at: The date when applications open
        - closes_at: The deadline date for applications
        - last_checked: The date when this information was last verified
        - target_audience_desc: A high quality description of who can apply for this subsidy
        
        Target Audience options:
        {TargetAudience.get_documentation()}
        
        Financial Instrument options:
        {FinancialInstrument.get_documentation()}
        """


class ClientFieldData(BaseModel):
    audience_type: TargetAudience
    audience_desc: str
    
    @classmethod
    def get_documentation(cls) -> str:
        return f"""
        ClientFieldData represents information about a client:

        Use None if you cannot determine the proper value or if the necessary information is missing.

        Additional information about (some) fields or values:
        
        Fields:
        - audience_type: The category that best describes this client's organization type
        - audience_desc: A high quality description of the client's business, activities, and characteristics in a couple of sentences
        
        Target Audience options:
        {TargetAudience.get_documentation()}
        """


StructuredOutputSchema = ListingFieldData | ClientFieldData