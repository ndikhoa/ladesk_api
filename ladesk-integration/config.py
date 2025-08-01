import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    # Ladesk Cloud Configuration
    LADESK_CLOUD_API_KEY_V1 = os.getenv('LADESK_CLOUD_API_KEY_V1', '')
    LADESK_CLOUD_API_KEY_V3 = os.getenv('LADESK_CLOUD_API_KEY_V3', '')
    LADESK_CLOUD_BASE_URL_V1 = os.getenv('LADESK_CLOUD_BASE_URL_V1', 'https://social.ladesk.com/api')
    LADESK_CLOUD_BASE_URL_V3 = os.getenv('LADESK_CLOUD_BASE_URL_V3', 'https://social.ladesk.com/api/v3')
    LADESK_CLOUD_USER_IDENTIFIER = os.getenv('LADESK_CLOUD_USER_IDENTIFIER', '1pkaew79')
    FACEBOOK_DEPARTMENT_CLOUD = os.getenv('FACEBOOK_DEPARTMENT_CLOUD', 'dw51dt2g')

    # Ladesk On-Premise Configuration
    LADESK_ONPREMISE_API_KEY_V1 = os.getenv('LADESK_ONPREMISE_API_KEY_V1', '')
    LADESK_ONPREMISE_API_KEY_V3 = os.getenv('LADESK_ONPREMISE_API_KEY_V3', '')
    LADESK_ONPREMISE_BASE_URL_V1 = os.getenv('LADESK_ONPREMISE_BASE_URL_V1', 'https://social-on-premise.ladesk.com/api')
    LADESK_ONPREMISE_BASE_URL_V3 = os.getenv('LADESK_ONPREMISE_BASE_URL_V3', 'https://social-on-premise.ladesk.com/api/v3')
    LADESK_ONPREMISE_USER_IDENTIFIER = os.getenv('LADESK_ONPREMISE_USER_IDENTIFIER', 'k6citev3')
    FACEBOOK_DEPARTMENT_ONPREMISE = os.getenv('FACEBOOK_DEPARTMENT_ONPREMISE', 'on1zin8g')

    # Application Configuration
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    DB_PATH = os.getenv('DB_PATH', 'ladesk_integration.db')
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here')
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', 3000))
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'logs/app.log')
    WEBHOOK_SECRET = os.getenv('WEBHOOK_SECRET', 'your-webhook-secret')

    # Webhook URL Configuration
    WEBHOOK_BASE_URL = os.getenv('WEBHOOK_BASE_URL', 'https://45dc157d7046.ngrok-free.app').strip()
    WEBHOOK_CLOUD_ENDPOINT = f"{WEBHOOK_BASE_URL}/webhook/ladesk-cloud"
    WEBHOOK_ONPREMISE_ENDPOINT = f"{WEBHOOK_BASE_URL}/webhook/ladesk-onpremise"

    # On-Premise Integration Configuration
    LADESK_ONPREMISE_DEPARTMENT_ID = os.getenv('LADESK_ONPREMISE_DEPARTMENT_ID', 'on1zin8g')
    LADESK_ONPREMISE_RECIPIENT_EMAIL = os.getenv('LADESK_ONPREMISE_RECIPIENT_EMAIL', 'support@mail.social-on-premise.ladesk.com')