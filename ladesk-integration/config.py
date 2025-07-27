import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    # Ladesk Cloud Configuration
    LADESK_CLOUD_API_KEY_V1 = os.getenv('LADESK_CLOUD_API_KEY_V1', 'wm6if4kwlipheqh2x4ztxc6pr73mqc66gz5pd2e0h1')
    LADESK_CLOUD_API_KEY_V3 = os.getenv('LADESK_CLOUD_API_KEY_V3', '94jxficvclwl444533ctuidl9y7bm41fsxh5m5ujl4')
    LADESK_CLOUD_BASE_URL_V1 = os.getenv('LADESK_CLOUD_BASE_URL_V1', 'https://social.ladesk.com/api')
    LADESK_CLOUD_BASE_URL_V3 = os.getenv('LADESK_CLOUD_BASE_URL_V3', 'https://social.ladesk.com/api/v3')
    LADESK_CLOUD_USER_IDENTIFIER = os.getenv('LADESK_CLOUD_USER_IDENTIFIER', '1pkaew79')
    FACEBOOK_DEPARTMENT_CLOUD = os.getenv('FACEBOOK_DEPARTMENT_CLOUD', 'dw51dt2g')

    # Ladesk On-Premise Configuration
    LADESK_ONPREMISE_API_KEY_V1 = os.getenv('LADESK_ONPREMISE_API_KEY_V1', 'mhbH7aBvKBAP1R0H94zyOxEYECgE8lUv')
    LADESK_ONPREMISE_API_KEY_V3 = os.getenv('LADESK_ONPREMISE_API_KEY_V3', '9x05ce07vfnk83bkhjddeafp7gl3h1jrktgcp4wmbi')
    LADESK_ONPREMISE_BASE_URL_V1 = os.getenv('LADESK_ONPREMISE_BASE_URL_V1', 'https://social-on-premise.ladesk.com/api')
    LADESK_ONPREMISE_BASE_URL_V3 = os.getenv('LADESK_ONPREMISE_BASE_URL_V3', 'https://social-on-premise.ladesk.com/api/v3')
    LADESK_ONPREMISE_USER_IDENTIFIER = os.getenv('LADESK_ONPREMISE_USER_IDENTIFIER', 'k6citev3')
    FACEBOOK_DEPARTMENT_ONPREMISE = os.getenv('FACEBOOK_DEPARTMENT_ONPREMISE', 'on1zin8g')

    # Application Configuration1pkaew79
    DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'
    DB_PATH = os.getenv('DB_PATH', 'ladesk_integration.db')
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here')
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', 3000))
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'logs/app.log')
    WEBHOOK_SECRET = os.getenv('WEBHOOK_SECRET', 'your-webhook-secret')

# On-Premise Integration
ONPREMISE_WEBHOOK_URL = os.getenv('ONPREMISE_WEBHOOK_URL', None) 
