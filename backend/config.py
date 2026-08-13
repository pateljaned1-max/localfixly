import os
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)

# Load environment variables from .env file if present
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

DB_PATH = os.environ.get("LOCALFIX_DB_PATH", os.path.join(PROJECT_ROOT, "database", "localfix.db"))
if not os.path.isabs(DB_PATH):
    DB_PATH = os.path.join(PROJECT_ROOT, DB_PATH)

JWT_SECRET = os.environ.get("JWT_SECRET")
if not JWT_SECRET:
    # Fail-safe warning for production setup
    JWT_SECRET = "localfix-default-dev-secret-key-do-not-use-in-prod"

JWT_ALGORITHM = "HS256"
JWT_EXPIRES_HOURS = 24

CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "*").split(",")
SEED_DEMO_DATA = os.environ.get("SEED_DEMO_DATA", "True").lower() in ("true", "1", "yes")
