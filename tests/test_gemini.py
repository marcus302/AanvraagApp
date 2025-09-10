import pytest
from google import genai
from aanvraagapp.config import settings


# @pytest.mark.skip(reason="Uses Gemini API")
async def test_gemini_url_context():
    """
    RVO does not allow Gemini to dynamically retrieve URL's on the website it seems.
    """
    client = genai.Client(api_key=settings.gemini_api_key).aio

    tools = [
        {"url_context": {}}
    ]

    test_url = "https://www.rvo.nl/subsidies-financiering/besluit-bijstandverlening-zelfstandigen-bbz"
    
    # Use URL context to summarize the page
    response = await client.models.generate_content(
        model="gemini-2.5-flash",
        contents=f"Summarize the requirements for the subsidy at {test_url}",
        config=genai.types.GenerateContentConfig(
            tools=tools
        )
    )

    assert response.candidates is not None
    assert response.candidates[0].url_context_metadata is not None
    assert response.candidates[0].url_context_metadata.url_metadata is not None
    assert response.candidates[0].url_context_metadata.url_metadata[0].url_retrieval_status is not None

    assert response.candidates[0].url_context_metadata.url_metadata[0].url_retrieval_status.value == "URL_RETRIEVAL_STATUS_ERROR"
