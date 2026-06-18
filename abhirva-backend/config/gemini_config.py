import os
from google import genai
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

def get_gemini_client():
    """
    Initializes and returns the Gemini client.
    """
    if not GEMINI_API_KEY:
        raise ValueError("Gemini API key not found in environment variables.")
    
    # Initialize the client from the new google-genai SDK
    client = genai.Client(api_key=GEMINI_API_KEY)
    return client

# Global singleton client
gemini_client = get_gemini_client()
