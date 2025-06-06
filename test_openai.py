import os
from dotenv import load_dotenv
import openai


load_dotenv()


def test_openai_connection() -> None:
    """Verify that the OpenAI API can be reached with the provided key."""
    api_key = os.getenv("OPENAI_API_KEY")

    assert api_key and api_key != "your_openai_api_key_here", "Invalid API key in .env file"

    client = openai.OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": "Hello"}],
        max_tokens=5,
    )
    assert response is not None
