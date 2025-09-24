from datetime import date
from pydantic import BaseModel, Field
from aanvraagapp.types import TargetAudience, FinancialInstrument, BusinessIdentity


class ListingFieldData(BaseModel):
    is_open: bool | None = Field(
        None, description="Whether the subsidy application is currently open for submissions"
    )
    opens_at: date | None = Field(
        None, description="The date when applications open"
    )
    closes_at: date | None = Field(
        None, description="The deadline date for applications"
    )
    last_checked: date | None = Field(
        None, description="The date when this information was last verified"
    )
    name: str = Field(
        description="A good name for the subsidy in Dutch"
    )
    target_audiences: list[TargetAudience] = Field(
        min_length=1,
        description="The categories that best describe the target audiences for this subsidy. "
        "Make sure you include all audiences that the subsidy seems to be intended for. Only "
        "use OTHER if of one the audiences really does not fit into one of the other categories."
    )
    financial_instrument: FinancialInstrument = Field(
        description="The type of financial support offered by this subsidy"
    )
    target_audience_desc: str = Field(
        description="A high quality description of who can apply for this subsidy in a couple "
        "of sentences in Dutch"
    )
    
    @classmethod
    def get_documentation(cls) -> str:
        return f"""
        ListingFieldData represents information about a subsidy:

        Use None if you cannot determine the proper value or if the necessary information is missing.

        Additional information about (some) fields or values:
        
        target_audiences options:
        {TargetAudience.get_documentation()}
        
        fiancial_instrument options:
        {FinancialInstrument.get_documentation()}
        """


class ClientFieldData(BaseModel):
    business_identity: BusinessIdentity = Field(
        description="The category that best describes the most probably business identity of "
        "this client. Note that this is about the client him/herself, and NOT about the client's "
        "intended customers."
    )
    audience_desc: str = Field(
        description="A high quality description of the client's business, activities, "
        "and characteristics in a couple of sentences in Dutch"
    )
    
    @classmethod
    def get_documentation(cls) -> str:
        return f"""
        ClientFieldData represents information about a client:

        Use None if you cannot determine the proper value or if the necessary information is missing.

        A common mistake is to assign to business_identity what customers this client looks for, but this is WRONG! You should assign the category that best fits what the client is itself. Customers and partners of the client should have no effect on what gets filled in here!

        Additional information about (some) fields or values:
        
        business_identity options:
        {BusinessIdentity.get_documentation()}
        """


class ClientListingMatchScore(BaseModel):
    score: float = Field(
        description="A score between 0.0 and 1.0 indicating how well the client matches the listing"
    )
    reasoning: str = Field(
        description="Brief explanation of why this score was assigned"
    )
    
    @classmethod
    def get_documentation(cls) -> str:
        return """
        ClientListingMatchScore represents how well a client matches a listing:
        
        - score: A float between 0.0 and 1.0 where 1.0 is a perfect match
        - reasoning: A brief explanation of the scoring decision
        """


StructuredOutputSchema = ListingFieldData | ClientFieldData
