from datetime import date
from pydantic import BaseModel, Field
from aanvraagapp.types import (
    TargetAudience,
    FinancialInstrument,
    BusinessIdentity,
    ConditionEval,
)
import textwrap


class ListingFieldData(BaseModel):
    is_open: bool | None = Field(
        None,
        description="Whether the subsidy application is currently open for submissions",
    )
    opens_at: date | None = Field(None, description="The date when applications open")
    closes_at: date | None = Field(
        None, description="The deadline date for applications"
    )
    last_checked: date | None = Field(
        None, description="The date when this information was last verified"
    )
    name: str = Field(description="A good name for the subsidy in Dutch")
    target_audiences: list[TargetAudience] = Field(
        min_length=1,
        description="The categories that best describe the target audiences for this subsidy. "
        "Make sure you include all audiences that the subsidy seems to be intended for. Only "
        "use OTHER if of one the audiences really does not fit into one of the other categories.",
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
        return textwrap.dedent(f"""
        ListingFieldData represents information about a listing:

        Use None if you cannot determine the proper value or if the necessary information is missing.

        Additional information about (some) fields or values:
        
        target_audiences options:
        {TargetAudience.get_documentation()}
        
        fiancial_instrument options:
        {FinancialInstrument.get_documentation()}
        """).strip()


class ClientFieldData(BaseModel):
    business_identity: BusinessIdentity = Field(
        description="The category that best describes the most probably business identity of "
        "this client."
    )
    audience_desc: str = Field(
        description="A high quality description of the client's business, activities, "
        "and characteristics in a couple of sentences in Dutch"
    )

    @classmethod
    def get_documentation(cls) -> str:
        return textwrap.dedent(f"""
        ClientFieldData represents information about a client:

        Use None if you cannot determine the proper value or if the necessary information is missing.

        A common mistake is to assign to business_identity what customers this client looks for, but this is WRONG! You should assign the category that best fits what the client is itself.

        Additional information about (some) fields or values:
        
        business_identity options:
        {BusinessIdentity.get_documentation()}
        """).strip()


class ClientListingMatchCondition(BaseModel):
    condition_desc: str = Field(
        description="One or several sentences to describe the condition."
    )
    condition_eval: ConditionEval = Field(
        description="The evaluation of the condition in condition_desc on the basis of the client and listing subscription."
    )
    reasoning: str = Field(
        description="Brief explanation of why the condition was evaluated with this result."
    )


class ClientListingMatchResult(BaseModel):
    conditions: list[ClientListingMatchCondition] = Field(
        description="All conditions for this listing and client combination, where each condition should be evaluated. Allowed to be empty if listing_ambiguous is True."
    )
    listing_ambiguous: bool = Field(
        description="Set this to True and conditions to an empty list if the listing does not represent a coherent whole that a single set of conditions can be defined for. Set to False if this is possible, in which case the list of conditions should be set."
    )

    @classmethod
    def get_documentation(cls) -> str:
        return textwrap.dedent(f"""
        ClientListingMatchResult represents information about a combination of a client and a listing:

        Set listing_ambiguous to False and conditions to an empty list if the given listing does not form a coherent whole or single unit. This sometimes happens when a listing actually represents multiple different sub listings, for example.

        Set listing_ambiguous to True and fill in conditions with all conditions that the client has to meet in order to be eligible for the listing. For each condition, you'll have to evaluate it and give your reasoning.

        Some example scenarios to help you evaluate conditions:
        1. The listing description states that only pharmaceutical companies can apply. The client description does not contain any reference to this, and describes a software company. The condition therefore FAILS.
        2. The listing description says that it's intended for companies that look for investors. Nowhere does the client description says it's looking for funding, but the client could easily decide to look for funding, so the condition is therefore an OPPORTUNITY.
        3. The listing description says it's intended for funding of innovative and technologically riskful product development. Nowhere does the client description say they are engaged in this, but the client could easily start such a project, so the condition is an OPPORTUNITY.
        4. The listing description says it's intended to reimburse farmers for damaged crops. The client description states it's a software company. They have nothing in commong, so the condition FAILS.
        5. The listing description states it funds social projects. The client is an association that organizes cooking workshops for the elderly. The condition PASSES.

        Additional information about (some) fields or values:

        condition_eval:
        {ConditionEval.get_documentation()}
        """).strip()


StructuredOutputSchema = ListingFieldData | ClientFieldData
