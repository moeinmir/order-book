from pathlib import Path
from datetime import timedelta
from dotenv import load_dotenv
import os
load_dotenv()

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60), 
    'REFRESH_TOKEN_LIFETIME': timedelta(days=30), 
}

BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = os.environ.get("SECRET_KEY")
DEBUG = True
ALLOWED_HOSTS = []
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'accounts',
    'tokensbalances',
    'orders',
    'rest_framework',
    'rest_framework_simplejwt',
    'drf_yasg',
]
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'orderbook.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'orderbook.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'orderbook',
        'USER': 'postgres',
        'PASSWORD': 'changeme',
        'HOST': 'localhost',
        'PORT': '5432',
         'TEST': {
            'NAME': 'orderbook',
        },
    }

}

AUTH_USER_MODEL = 'accounts.CustomUser'

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True
STATIC_URL = 'static/'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
}
APP_MNEMONIC = os.environ.get("APP_MNEMONIC")

APP_COIN = "eth"

WEB3_PROVIDER_URI = f"https://sepolia.infura.io/v3/{os.environ.get('SEPOLIA_INFORA_KEY')}"

SWAGGER_SETTINGS = {
    'SECURITY_DEFINITIONS': {
        'Bearer': {
            'type': 'apiKey',
            'in': 'header',
            'name': 'Authorization',
            'description': 'JWT Authorization header using the Bearer scheme. Example: "Authorization: Bearer <token>"',
        }
    },
}

MAX_BIGINT = 2**63 - 1

BASE_DIR = Path(__file__).resolve().parent.parent

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "DEBUG",
    },
}

CENTRAL_HD_WALLET_ADDRESS = os.environ.get("CENTRAL_HD_WALLET_ADDRESS")

CENTRAL_HD_WALLET_INDEX = os.environ.get("CENTRAL_HD_WALLET_INDEX")

KAFKA_CONFIG = {
    'bootstrap.servers': 'localhost:39092', 
    'group.id': 'order-matching-group',     
    'auto.offset.reset': 'earliest',        
}

REDIS_CONFIG = {
    'host':"localhost",
    'port':6379,
    'db':0,
    'decode_responses':True, 
    'password':'12345678'
}

CHAIN_ID = 11155111
ESTIMATED_GAS_FOR_ERC20_TRANSFER = 700000
