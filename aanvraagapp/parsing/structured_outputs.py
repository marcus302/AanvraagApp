from datetime import date
from pydantic import BaseModel, Field
from aanvraagapp.types import TargetAudience, FinancialInstrument


class ListingFieldData(BaseModel):
    is_open: bool | None = Field(None, description="Whether the subsidy application is currently open for submissions")
    opens_at: date | None = Field(None, description="The date when applications open")
    closes_at: date | None = Field(None, description="The deadline date for applications")
    last_checked: date | None = Field(None, description="The date when this information was last verified")
    name: str = Field(description="A good name for the subsidy in Dutch")
    target_audience: TargetAudience = Field(description="The category that best describes the target audience for this subsidy")
    financial_instrument: FinancialInstrument = Field(description="The type of financial support offered by this subsidy")
    target_audience_desc: str = Field(description="A high quality description of who can apply for this subsidy in a couple of sentences in Dutch")
    
    @classmethod
    def get_documentation(cls) -> str:
        return f"""
        ListingFieldData represents information about a subsidy:

        Use None if you cannot determine the proper value or if the necessary information is missing.

        Additional information about (some) fields or values:
        
        Target Audience options:
        {TargetAudience.get_documentation()}
        
        Financial Instrument options:
        {FinancialInstrument.get_documentation()}
        """


class ClientFieldData(BaseModel):
    audience_type: TargetAudience = Field(description="The category that best describes this client's organization type")
    audience_desc: str = Field(description="A high quality description of the client's business, activities, and characteristics in a couple of sentences in Dutch")
    
    @classmethod
    def get_documentation(cls) -> str:
        return f"""
        ClientFieldData represents information about a client:

        Use None if you cannot determine the proper value or if the necessary information is missing.

        Additional information about (some) fields or values:
        
        Target Audience options:
        {TargetAudience.get_documentation()}
        """


StructuredOutputSchema = ListingFieldData | ClientFieldData
