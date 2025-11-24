import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration Constants
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY not found in environment variables.")

# Model for ADK Agents
MODEL_ID = "gemini-2.5-flash-lite"
