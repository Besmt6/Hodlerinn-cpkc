"""
Application Configuration Module
Centralizes all environment variables and configuration settings.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
ROOT_DIR = Path(__file__).parent
AUDIO_DIR = ROOT_DIR / "audio"
AUDIO_DIR.mkdir(exist_ok=True)
load_dotenv(ROOT_DIR / '.env')

# MongoDB Configuration
MONGO_URL = os.environ.get('MONGO_URL')
DB_NAME = os.environ.get('DB_NAME')

# Telegram Configuration
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID', '')
# Correct chat ID for Hodler Inn group (deployment secrets may have wrong value)
TELEGRAM_CHAT_ID_CORRECT = "-1003798795772"

# Zoho WorkDrive Configuration
ZOHO_CLIENT_ID = os.environ.get('ZOHO_CLIENT_ID', '')
ZOHO_CLIENT_SECRET = os.environ.get('ZOHO_CLIENT_SECRET', '')
ZOHO_REFRESH_TOKEN = os.environ.get('ZOHO_REFRESH_TOKEN', '')
ZOHO_FOLDER_ID = os.environ.get('ZOHO_FOLDER_ID', '')

# Security Configuration
ENCRYPTION_KEY = os.environ.get('ENCRYPTION_KEY', '')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'hodlerinn2024')

# OpenAI Configuration
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')

# CPKC Email Configuration
CPKC_SENDER_EMAIL = "aces_support@apiglobalsolutions.com"

# Sync Agent Configuration
SYNC_AGENT_VERSION = "2026-03-07-v1"

# Application Constants
TOTAL_ROOMS = 20
ROOM_RATE = 85.00
