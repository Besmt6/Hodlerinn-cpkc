"""
Telegram Service Module
Handles sending notifications to Telegram.
"""
import logging
import httpx
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, TELEGRAM_CHAT_ID_CORRECT

# Try to import telegram bot
try:
    from telegram import Bot
    telegram_bot = Bot(token=TELEGRAM_BOT_TOKEN) if TELEGRAM_BOT_TOKEN else None
except ImportError:
    Bot = None
    telegram_bot = None
    logging.warning("python-telegram-bot not installed, Telegram notifications disabled")

async def send_telegram_notification(message: str, use_correct_chat_id: bool = True) -> bool:
    """
    Send a notification message to the configured Telegram chat.
    
    Args:
        message: HTML-formatted message to send
        use_correct_chat_id: Use the hardcoded correct chat ID (recommended)
    
    Returns:
        True if message sent successfully, False otherwise
    """
    if not TELEGRAM_BOT_TOKEN:
        logging.warning("Telegram bot token not configured")
        return False
    
    chat_id = TELEGRAM_CHAT_ID_CORRECT if use_correct_chat_id else TELEGRAM_CHAT_ID
    
    if not chat_id:
        logging.warning("Telegram chat ID not configured")
        return False
    
    try:
        # Use httpx for async HTTP requests (more reliable than python-telegram-bot in some cases)
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
                json={
                    "chat_id": chat_id,
                    "text": message,
                    "parse_mode": "HTML"
                },
                timeout=10.0
            )
            
            if response.status_code == 200:
                logging.info(f"Telegram notification sent successfully")
                return True
            else:
                logging.error(f"Telegram API error: {response.status_code} - {response.text}")
                return False
                
    except Exception as e:
        logging.error(f"Failed to send Telegram notification: {e}")
        return False

async def send_telegram_photo(photo_bytes: bytes, caption: str = "") -> bool:
    """
    Send a photo to the configured Telegram chat.
    
    Args:
        photo_bytes: Image data as bytes
        caption: Optional caption for the photo
    
    Returns:
        True if photo sent successfully, False otherwise
    """
    if not TELEGRAM_BOT_TOKEN:
        return False
    
    chat_id = TELEGRAM_CHAT_ID_CORRECT
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto",
                data={"chat_id": chat_id, "caption": caption, "parse_mode": "HTML"},
                files={"photo": ("image.png", photo_bytes, "image/png")},
                timeout=30.0
            )
            return response.status_code == 200
    except Exception as e:
        logging.error(f"Failed to send Telegram photo: {e}")
        return False

async def send_telegram_document(document_bytes: bytes, filename: str, caption: str = "") -> bool:
    """
    Send a document to the configured Telegram chat.
    
    Args:
        document_bytes: Document data as bytes
        filename: Name for the file
        caption: Optional caption for the document
    
    Returns:
        True if document sent successfully, False otherwise
    """
    if not TELEGRAM_BOT_TOKEN:
        return False
    
    chat_id = TELEGRAM_CHAT_ID_CORRECT
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendDocument",
                data={"chat_id": chat_id, "caption": caption, "parse_mode": "HTML"},
                files={"document": (filename, document_bytes, "application/octet-stream")},
                timeout=30.0
            )
            return response.status_code == 200
    except Exception as e:
        logging.error(f"Failed to send Telegram document: {e}")
        return False
