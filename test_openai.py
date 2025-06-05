import os
from dotenv import load_dotenv
import openai

# Load environment variables
load_dotenv()

def test_openai_connection():
    api_key = os.getenv('OPENAI_API_KEY')

    print(f"🔑 API Key found: {api_key[:10]}...{api_key[-4:] if api_key else 'None'}")

    if not api_key or api_key == 'your_openai_api_key_here':
        print("❌ Invalid API key in .env file")
        return False

    try:
        client = openai.OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Hello"}],
            max_tokens=5
        )
        print("✅ OpenAI API connection successful!")
        return True
    except Exception as e:
        print(f"❌ OpenAI API error: {e}")
        return False

if __name__ == "__main__":
    test_openai_connection()