import os
from dotenv import load_dotenv


class Config:
    # Load environment variables from a .env file if present
    load_dotenv()
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret")
    DEBUG = os.getenv("FLASK_DEBUG", "1") == "1"
    TESTING = os.getenv("FLASK_TESTING", "0") == "1"
    # Example: postgresql://user:password@host:5432/dbname
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/Sonaged_reporting")
    # Twilio settings
    TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")
    TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
    TWILIO_WHATSAPP_NUMBER = os.getenv("TWILIO_WHATSAPP_NUMBER", "whatsapp:+00000000000")


config = Config()



