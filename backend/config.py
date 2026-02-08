import os
from dotenv import load_dotenv

load_dotenv()

API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", 8000))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
RULES_FILE = os.getenv("RULES_FILE", "rules/default_rules.json")
LLM_ENDPOINT = os.getenv("LLM_ENDPOINT", "http://localhost:8001")
