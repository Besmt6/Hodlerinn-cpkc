"""
Security Module
Handles encryption, decryption, and authentication utilities.
"""
import logging
from cryptography.fernet import Fernet
from config import ENCRYPTION_KEY, ADMIN_PASSWORD

# Initialize Fernet cipher
fernet = Fernet(ENCRYPTION_KEY.encode()) if ENCRYPTION_KEY else None

def encrypt_data(data: str) -> str:
    """Encrypt sensitive data"""
    if not fernet:
        logging.warning("Encryption key not configured, storing data unencrypted")
        return data
    try:
        return fernet.encrypt(data.encode()).decode()
    except Exception as e:
        logging.error(f"Encryption error: {e}")
        return data

def decrypt_data(encrypted_data: str) -> str:
    """Decrypt sensitive data"""
    if not fernet:
        return encrypted_data
    try:
        return fernet.decrypt(encrypted_data.encode()).decode()
    except Exception as e:
        logging.error(f"Decryption error: {e}")
        return encrypted_data

def verify_admin_password(password: str) -> bool:
    """Verify admin password"""
    return password == ADMIN_PASSWORD

def mask_sensitive_data(data: str, visible_chars: int = 4) -> str:
    """Mask sensitive data for logging"""
    if not data or len(data) <= visible_chars:
        return "****"
    return data[:visible_chars] + "*" * (len(data) - visible_chars)
