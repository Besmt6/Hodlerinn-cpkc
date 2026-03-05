from fastapi import FastAPI, APIRouter, HTTPException, Response, Query, BackgroundTasks
from fastapi.responses import StreamingResponse, FileResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
import uuid
from datetime import datetime, timezone, timedelta
import io
import csv
import xlsxwriter
import math
import httpx
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from cryptography.fernet import Fernet
from PIL import Image, ImageDraw, ImageFont
import base64
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image as RLImage
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import asyncio

ROOT_DIR = Path(__file__).parent
AUDIO_DIR = ROOT_DIR / "audio"
AUDIO_DIR.mkdir(exist_ok=True)
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Telegram configuration
# Telegram configuration
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '')
# IMPORTANT: The correct chat ID for Hodler Inn group. Deployment secrets have wrong value.
TELEGRAM_CHAT_ID_CORRECT = "-1003798795772"
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID', '')

# Zoho WorkDrive configuration
ZOHO_CLIENT_ID = os.environ.get('ZOHO_CLIENT_ID', '')
ZOHO_CLIENT_SECRET = os.environ.get('ZOHO_CLIENT_SECRET', '')
ZOHO_REFRESH_TOKEN = os.environ.get('ZOHO_REFRESH_TOKEN', '')
ZOHO_FOLDER_ID = os.environ.get('ZOHO_FOLDER_ID', '')

# Encryption configuration
ENCRYPTION_KEY = os.environ.get('ENCRYPTION_KEY', '')
fernet = Fernet(ENCRYPTION_KEY.encode()) if ENCRYPTION_KEY else None

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Admin password (simple protection)
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'hodlerinn2024')

# ==================== Health Check Endpoint ====================

@api_router.get("/health")
async def health_check():
    """Health check endpoint for deployment monitoring"""
    try:
        # Quick MongoDB ping to verify DB connection
        await db.command('ping')
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        logging.error(f"Health check failed: {e}")
        return {"status": "unhealthy", "database": "disconnected", "error": str(e)}

# ==================== Encryption Functions ====================

def encrypt_data(data: str) -> str:
    """Encrypt sensitive data"""
    if not fernet or not data:
        return data
    try:
        return fernet.encrypt(data.encode()).decode()
    except Exception as e:
        logging.error(f"Encryption error: {e}")
        return data

def decrypt_data(encrypted_data: str) -> str:
    """Decrypt sensitive data"""
    if not fernet or not encrypted_data:
        return encrypted_data
    try:
        return fernet.decrypt(encrypted_data.encode()).decode()
    except Exception as e:
        # If decryption fails, data might not be encrypted (old data)
        return encrypted_data

# ==================== Zoho WorkDrive Functions ====================

async def get_zoho_access_token():
    """Get fresh access token using refresh token"""
    if not ZOHO_CLIENT_ID or not ZOHO_CLIENT_SECRET or not ZOHO_REFRESH_TOKEN:
        logging.error("Zoho credentials not configured")
        return None
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://accounts.zoho.com/oauth/v2/token",
                data={
                    "grant_type": "refresh_token",
                    "client_id": ZOHO_CLIENT_ID,
                    "client_secret": ZOHO_CLIENT_SECRET,
                    "refresh_token": ZOHO_REFRESH_TOKEN
                }
            )
            data = response.json()
            return data.get("access_token")
    except Exception as e:
        logging.error(f"Failed to get Zoho access token: {e}")
        return None

async def get_zoho_team_id(access_token):
    """Get the team ID for WorkDrive"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://www.zohoapis.com/workdrive/api/v1/users/me",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            data = response.json()
            # Team ID is in preferred_team_id
            return data.get("data", {}).get("attributes", {}).get("preferred_team_id")
    except Exception as e:
        logging.error(f"Failed to get Zoho team ID: {e}")
        return None

async def get_zoho_root_folder_id(access_token, team_id):
    """Get the root folder ID (My Folders) for WorkDrive"""
    try:
        async with httpx.AsyncClient() as client:
            # Get privatespace (My Folders)
            response = await client.get(
                f"https://www.zohoapis.com/workdrive/api/v1/users/me/privatespace",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            data = response.json()
            return data.get("data", {}).get("id")
    except Exception as e:
        logging.error(f"Failed to get Zoho root folder: {e}")
        return None

async def upload_to_zoho_drive(file_bytes: bytes, filename: str, folder_id: str = None):
    """Upload a file to Zoho WorkDrive"""
    access_token = await get_zoho_access_token()
    if not access_token:
        return {"success": False, "error": "Failed to get access token"}
    
    try:
        # Use configured folder if not specified
        if not folder_id:
            folder_id = ZOHO_FOLDER_ID
        
        if not folder_id:
            return {"success": False, "error": "Zoho folder ID not configured"}
        
        # Upload file
        async with httpx.AsyncClient() as client:
            files = {"content": (filename, file_bytes, "application/octet-stream")}
            response = await client.post(
                f"https://www.zohoapis.com/workdrive/api/v1/upload?parent_id={folder_id}&override-name-exist=true",
                headers={"Authorization": f"Bearer {access_token}"},
                files=files
            )
            
            if response.status_code == 200:
                data = response.json()
                return {"success": True, "data": data}
            else:
                logging.error(f"Zoho upload failed: {response.status_code} - {response.text}")
                return {"success": False, "error": f"Upload failed: {response.status_code}"}
                
    except Exception as e:
        logging.error(f"Failed to upload to Zoho Drive: {e}")
        return {"success": False, "error": str(e)}

# ==================== Scheduler for Monthly Reset & Auto-Sync ====================

scheduler = AsyncIOScheduler()

# Auto-sync job ID for managing the scheduled task
AUTO_SYNC_JOB_ID = "auto_sync_daily"

async def monthly_data_reset():
    """Reset all guest and booking data on 1st of each month"""
    try:
        bookings_result = await db.bookings.delete_many({})
        guests_result = await db.guests.delete_many({})
        
        logging.info(f"Monthly reset: Deleted {bookings_result.deleted_count} bookings and {guests_result.deleted_count} guests")
        
        # Send Telegram notification about reset
        await send_telegram_notification(
            f"🔄 <b>MONTHLY DATA RESET</b>\n"
            f"━━━━━━━━━━━━━━━\n"
            f"📅 Date: {datetime.now().strftime('%Y-%m-%d')}\n"
            f"🗑️ Bookings cleared: {bookings_result.deleted_count}\n"
            f"🗑️ Guests cleared: {guests_result.deleted_count}\n"
            f"━━━━━━━━━━━━━━━\n"
            f"✅ System ready for new month!"
        )
    except Exception as e:
        logging.error(f"Monthly reset failed: {e}")

async def auto_sync_task():
    """Automated daily sync at 3 PM - verifies previous day's records"""
    logging.info("Auto-sync task triggered at 3 PM")
    try:
        # Check if auto-sync is still enabled
        settings = await db.settings.find_one({"id": "portal_settings"}, {"_id": 0})
        if not settings or not settings.get("auto_sync_enabled"):
            logging.info("Auto-sync is disabled, skipping")
            return
        
        if not settings.get("api_global_username") or not settings.get("api_global_password_encrypted"):
            logging.warning("Auto-sync: Portal credentials not configured")
            return
        
        # Get yesterday's date for sync
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        
        # Get Hodler Inn records for yesterday
        bookings = await db.bookings.find({"check_in_date": yesterday}, {"_id": 0}).to_list(1000)
        
        # Get guest names
        employee_numbers = [b['employee_number'] for b in bookings]
        guests_list = await db.guests.find({"employee_number": {"$in": employee_numbers}}, {"_id": 0}).to_list(1000)
        guests_dict = {g['employee_number']: g for g in guests_list}
        
        # Build records for sync agent
        hodler_records = []
        for booking in bookings:
            guest = guests_dict.get(booking['employee_number'])
            if guest:
                # Handle both encrypted and non-encrypted names
                name_encrypted = guest.get('name_encrypted')
                if name_encrypted:
                    decrypted_name = decrypt_data(name_encrypted)
                else:
                    decrypted_name = guest.get('name', '')
                    
                hodler_records.append({
                    "employee_name": decrypted_name,
                    "employee_number": booking['employee_number'],
                    "room_number": booking['room_number']
                })
        
        logging.info(f"Auto-sync: Processing {len(hodler_records)} Hodler Inn records for {yesterday}")
        
        # Run the sync
        from sync_agent import APIGlobalSyncAgent
        username = settings.get("api_global_username")
        password = decrypt_data(settings.get("api_global_password_encrypted"))
        
        agent = APIGlobalSyncAgent(username, password)
        results = await agent.run_sync(hodler_records)
        
        # Auto-update employee names to match portal format
        names_updated = 0
        if results.get("verified"):
            for verified in results["verified"]:
                if verified.get("update_name") and verified.get("portal_name") and verified.get("employee_id"):
                    portal_name = verified["portal_name"]
                    employee_id = verified["employee_id"]
                    
                    await db.employees.update_one(
                        {"employee_number": employee_id},
                        {"$set": {"name": portal_name, "portal_name_synced": True}}
                    )
                    await db.guests.update_one(
                        {"employee_number": employee_id},
                        {"$set": {"name": portal_name}}
                    )
                    names_updated += 1
                    logging.info(f"Auto-sync: Updated employee name to portal format: {employee_id} -> {portal_name}")
        
        # Store sync history
        await db.sync_history.insert_one({
            "id": str(uuid.uuid4()),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "target_date": yesterday,
            "results": results,
            "auto_triggered": True,
            "names_updated": names_updated
        })
        
        # Update sync status
        global sync_status
        sync_status["last_run"] = datetime.now(timezone.utc).isoformat()
        sync_status["last_results"] = results
        sync_status["progress"] = "Auto-sync completed"
        
        logging.info(f"Auto-sync completed: Verified={len(results.get('verified', []))}, No Bill={len(results.get('no_bill', []))}")
        
        # Send Telegram notification about sync results
        await send_telegram_notification(
            f"🤖 <b>AUTO-SYNC COMPLETED</b>\n"
            f"━━━━━━━━━━━━━━━\n"
            f"📅 Date Synced: {yesterday}\n"
            f"✅ Verified: {len(results.get('verified', []))}\n"
            f"❌ No Bill: {len(results.get('no_bill', []))}\n"
            f"⚠️ Missing: {len(results.get('missing_in_hodler', []))}\n"
            f"🔴 Errors: {len(results.get('errors', []))}\n"
            f"━━━━━━━━━━━━━━━"
        )
        
    except Exception as e:
        logging.error(f"Auto-sync failed: {e}")
        await send_telegram_notification(
            f"🚨 <b>AUTO-SYNC FAILED</b>\n"
            f"━━━━━━━━━━━━━━━\n"
            f"❌ Error: {str(e)[:200]}\n"
            f"━━━━━━━━━━━━━━━"
        )

def update_auto_sync_schedule(enabled: bool, start_date: str = None):
    """Add or remove the auto-sync scheduled job"""
    try:
        # Remove existing job if present
        if scheduler.get_job(AUTO_SYNC_JOB_ID):
            scheduler.remove_job(AUTO_SYNC_JOB_ID)
            logging.info("Removed existing auto-sync job")
        
        if enabled:
            # Parse start date if provided
            trigger_start = None
            if start_date:
                trigger_start = datetime.strptime(start_date, "%Y-%m-%d").replace(hour=15, minute=0)
            
            # Schedule for 3 PM Central Time (America/Chicago) every day
            from pytz import timezone
            central_tz = timezone('America/Chicago')
            scheduler.add_job(
                lambda: asyncio.create_task(auto_sync_task()),
                CronTrigger(hour=15, minute=0, start_date=trigger_start, timezone=central_tz),
                id=AUTO_SYNC_JOB_ID,
                replace_existing=True
            )
            if start_date:
                logging.info(f"Auto-sync scheduled for 3 PM Central Time daily, starting from {start_date}")
            else:
                logging.info("Auto-sync scheduled for 3 PM Central Time daily")
        else:
            logging.info("Auto-sync disabled")
    except Exception as e:
        logging.error(f"Error updating auto-sync schedule: {e}")

@app.on_event("startup")
async def start_scheduler():
    # Run on 1st of every month at 00:00 (midnight)
    scheduler.add_job(monthly_data_reset, CronTrigger(day=1, hour=0, minute=0))
    scheduler.start()
    logging.info("Monthly reset scheduler started - will reset data on 1st of each month")
    
    # Check if auto-sync was enabled and restore the schedule
    try:
        settings = await db.settings.find_one({"id": "portal_settings"}, {"_id": 0})
        if settings and settings.get("auto_sync_enabled"):
            start_date = settings.get("auto_sync_start_date")
            update_auto_sync_schedule(True, start_date)
            logging.info(f"Auto-sync restored from settings (enabled, start: {start_date or 'immediate'})")
    except Exception as e:
        logging.error(f"Failed to restore auto-sync settings: {e}")

@app.on_event("shutdown")
async def shutdown_scheduler():
    scheduler.shutdown()

# ==================== Telegram Notification ====================

async def get_telegram_chat_id():
    """Get Telegram Chat ID from database settings, fallback to hardcoded correct value"""
    # First try database settings
    settings = await db.settings.find_one({"id": "portal_settings"}, {"_id": 0})
    if settings and settings.get("telegram_chat_id"):
        db_chat_id = settings.get("telegram_chat_id")
        logging.info(f"Using Telegram chat ID from database: {db_chat_id}")
        return db_chat_id
    
    # IMPORTANT: The deployment secrets have wrong value (6372960197)
    # Always use the correct hardcoded value as fallback instead of env variable
    logging.info(f"Using hardcoded correct Telegram chat ID: {TELEGRAM_CHAT_ID_CORRECT}")
    return TELEGRAM_CHAT_ID_CORRECT

async def send_telegram_notification(message: str):
    """Send notification to Telegram (supports multiple chat IDs separated by comma)"""
    chat_id = await get_telegram_chat_id()
    
    if not TELEGRAM_BOT_TOKEN:
        logging.warning("Telegram notification skipped: No bot token configured")
        return
    if not chat_id:
        logging.warning("Telegram notification skipped: No chat ID configured")
        return
    
    # Support multiple chat IDs separated by comma
    chat_ids = [cid.strip() for cid in chat_id.split(',') if cid.strip()]
    
    logging.info(f"Sending Telegram notification to {len(chat_ids)} chat(s): {chat_ids}")
    
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        async with httpx.AsyncClient() as client:
            for cid in chat_ids:
                response = await client.post(url, json={
                    "chat_id": cid,
                    "text": message,
                    "parse_mode": "HTML"
                })
                if response.status_code != 200:
                    logging.error(f"Telegram API error for chat {cid}: {response.text}")
                else:
                    logging.info(f"Telegram notification sent successfully to {cid}")
    except Exception as e:
        logging.error(f"Failed to send Telegram notification: {e}")

# ==================== Models ====================

class Employee(BaseModel):
    """Pre-registered employee - only these IDs can check in"""
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    employee_number: str
    name: str
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class EmployeeCreate(BaseModel):
    employee_number: str
    name: str

class EmployeeUpdate(BaseModel):
    employee_number: Optional[str] = None
    name: Optional[str] = None
    is_active: Optional[bool] = None

class GuestRegistration(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    employee_number: str
    name: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class GuestRegistrationCreate(BaseModel):
    employee_number: str
    name: str

class CheckIn(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    employee_number: str
    room_number: str
    check_in_date: str  # ISO format date
    check_in_time: str  # HH:MM format
    check_out_date: Optional[str] = None
    check_out_time: Optional[str] = None
    signature: Optional[str] = None  # Signature captured at check-in
    is_checked_out: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class CheckInCreate(BaseModel):
    employee_number: str
    room_number: str
    check_in_date: str
    check_in_time: str
    signature: str  # Required at check-in

class CheckOutCreate(BaseModel):
    room_number: str
    employee_number: Optional[str] = None  # For verification
    check_out_date: str
    check_out_time: str

class AdminLogin(BaseModel):
    password: str

class GuestRecord(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    employee_number: str
    employee_name: str
    signature: str
    room_number: str
    check_in_date: str
    check_in_time: str
    check_out_date: Optional[str] = None
    check_out_time: Optional[str] = None
    total_hours: Optional[float] = None
    total_nights: Optional[int] = None
    is_checked_out: bool

# Room Management Models
class Room(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    room_number: str
    room_type: str = "Standard"  # Standard, Deluxe, Suite
    floor: str = "1"
    status: str = "available"  # available, occupied, maintenance
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class RoomCreate(BaseModel):
    room_number: str
    room_type: str = "Standard"
    floor: str = "1"
    notes: Optional[str] = None

class RoomUpdate(BaseModel):
    room_number: Optional[str] = None
    room_type: Optional[str] = None
    floor: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None

# Settings Models for API Global Integration
class PortalSettings(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = "portal_settings"
    api_global_username: Optional[str] = None
    api_global_password: Optional[str] = None  # Will be encrypted
    alert_email: Optional[str] = None
    auto_sync_enabled: bool = False
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class PortalSettingsUpdate(BaseModel):
    api_global_username: Optional[str] = None
    api_global_password: Optional[str] = None
    alert_email: Optional[str] = None
    auto_sync_enabled: Optional[bool] = None
    auto_sync_start_date: Optional[str] = None  # Format: YYYY-MM-DD
    voice_enabled: Optional[bool] = None  # Enable/disable voice messages
    voice_volume: Optional[float] = None  # Voice volume 0.0 to 1.0
    voice_speed: Optional[float] = None  # Voice speed 0.5 to 1.5
    telegram_chat_id: Optional[str] = None  # Telegram group/chat ID for notifications
    public_api_key: Optional[str] = None  # API key for public endpoints
    nightly_rate: Optional[float] = None  # Nightly room rate for billing
    # Email report settings
    email_reports_enabled: Optional[bool] = None
    email_smtp_host: Optional[str] = None
    email_smtp_port: Optional[int] = None
    email_sender: Optional[str] = None
    email_password: Optional[str] = None  # Will be encrypted
    email_recipient: Optional[str] = None
    email_report_time: Optional[str] = None  # Format: HH:MM (24hr)

# ==================== Helper Functions ====================

def calculate_stay_duration(check_in_date: str, check_in_time: str, check_out_date: str, check_out_time: str):
    """Calculate total hours and nights billed based on calendar days"""
    try:
        check_in_dt = datetime.strptime(f"{check_in_date} {check_in_time}", "%Y-%m-%d %H:%M")
        check_out_dt = datetime.strptime(f"{check_out_date} {check_out_time}", "%Y-%m-%d %H:%M")
        
        duration = check_out_dt - check_in_dt
        total_hours = duration.total_seconds() / 3600
        
        # Billing logic: Count calendar nights (not hours)
        # Check-in Day 1, Check-out Day 2 = 1 night (regardless of time)
        # Check-in Day 1, Check-out Day 3 = 2 nights
        check_in_day = datetime.strptime(check_in_date, "%Y-%m-%d").date()
        check_out_day = datetime.strptime(check_out_date, "%Y-%m-%d").date()
        total_nights = (check_out_day - check_in_day).days
        
        # Minimum 1 night if they checked in and out on different calendar days
        # or if checkout is after noon on the same day
        if total_nights < 1:
            total_nights = 1
        
        return round(total_hours, 2), total_nights
    except Exception:
        return None, None

# ==================== Routes ====================

@api_router.get("/")
async def root():
    return {"message": "Hodler Inn API - Welcome"}

# Guest Registration (no signature - signature is captured at check-in)
@api_router.post("/guests/register", response_model=GuestRegistration)
async def register_guest(input: GuestRegistrationCreate):
    # Verify employee ID is in the admin's approved list
    valid_employee = await db.employees.find_one({
        "employee_number": input.employee_number,
        "is_active": True
    }, {"_id": 0})
    
    if not valid_employee:
        raise HTTPException(
            status_code=400, 
            detail="Employee ID not found in approved list. Please contact admin."
        )
    
    # Check if employee already registered as guest
    existing = await db.guests.find_one({"employee_number": input.employee_number}, {"_id": 0})
    if existing:
        raise HTTPException(status_code=400, detail="Employee already registered")
    
    # Use name from the admin's approved list (not user input)
    guest = GuestRegistration(
        employee_number=input.employee_number,
        name=valid_employee["name"]
    )
    doc = guest.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    doc['is_verified'] = True  # Auto-verified since they're in admin employee list
    doc['verified_at'] = datetime.now(timezone.utc).isoformat()
    
    # Encrypt sensitive data before storing
    doc['name_encrypted'] = encrypt_data(doc['name'])
    
    await db.guests.insert_one(doc)
    
    # No notification needed - employee was pre-approved by being in admin list
    # Silent registration since admin already added them
    
    return guest


@api_router.post("/guests/register-pending")
async def register_guest_pending(input: GuestRegistrationCreate):
    """Register a guest as pending verification - allows check-in without admin approval.
    Admin can verify later through bulk verification."""
    
    # Check if employee already registered as guest
    existing = await db.guests.find_one({"employee_number": input.employee_number}, {"_id": 0})
    if existing:
        # If already registered, just return success
        return {"message": "Guest already registered", "employee_number": input.employee_number}
    
    # Create guest with pending verification status
    guest = GuestRegistration(
        employee_number=input.employee_number,
        name=input.name
    )
    doc = guest.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    doc['is_verified'] = False  # Pending verification
    doc['verified_at'] = None
    doc['pending_verification'] = True
    
    # Encrypt sensitive data before storing
    doc['name_encrypted'] = encrypt_data(doc['name'])
    
    await db.guests.insert_one(doc)
    
    # Also add to employees list as unverified
    await db.employees.update_one(
        {"employee_number": input.employee_number},
        {"$set": {
            "employee_number": input.employee_number,
            "name": input.name,
            "is_active": True,
            "is_verified": False,
            "pending_verification": True,
            "added_at": datetime.now(timezone.utc).isoformat()
        }},
        upsert=True
    )
    
    # Send Telegram notification about new unverified employee
    chat_id = await get_telegram_chat_id()
    if TELEGRAM_BOT_TOKEN and chat_id:
        try:
            bot = Bot(token=TELEGRAM_BOT_TOKEN)
            message = (
                f"⚠️ *New Unverified Employee Check-In*\n\n"
                f"Employee ID: `{input.employee_number}`\n"
                f"Name: {input.name}\n\n"
                f"_Employee checked in but needs verification in Admin Dashboard._"
            )
            await bot.send_message(chat_id=chat_id, text=message, parse_mode="Markdown")
        except Exception as e:
            logger.error(f"Failed to send Telegram notification: {e}")
    
    return {"message": "Guest registered pending verification", "employee_number": input.employee_number}

# Track if sold-out notification was already sent today
sold_out_notification_sent_date = None
# Track if heads-up notice was already sent today
heads_up_notification_sent_date = None

# CPKC Email Recipients
CPKC_EMAIL_RECIPIENTS = ["crewtravel@cpkcr.com", "crewmanagers@cpkcr.com"]


async def get_notification_state():
    """Get notification state from database (persists across server restarts)."""
    state = await db.notification_state.find_one({"id": "email_notifications"}, {"_id": 0})
    if not state:
        state = {
            "id": "email_notifications",
            "sold_out_date": None,
            "heads_up_date": None,
            "was_sold_out": False
        }
    return state


async def set_sold_out_state(date: str, was_sold_out: bool):
    """Set sold-out state in database."""
    await db.notification_state.update_one(
        {"id": "email_notifications"},
        {"$set": {"sold_out_date": date, "was_sold_out": was_sold_out}},
        upsert=True
    )


async def set_heads_up_state(date: str):
    """Set heads-up notification date in database."""
    await db.notification_state.update_one(
        {"id": "email_notifications"},
        {"$set": {"heads_up_date": date}},
        upsert=True
    )


async def get_room_availability_details():
    """Get detailed room availability information for notifications."""
    # Get total rooms count
    total_rooms = await db.rooms.count_documents({})
    if total_rooms == 0:
        total_rooms = 28  # Default to 28 if rooms not configured
    
    # Get occupied rooms count (railroad guests in-house)
    occupied_by_railroad = await db.bookings.count_documents({"is_checked_out": False})
    
    # Get blocked rooms count (other guests)
    blocked_rooms = await db.blocked_rooms.count_documents({"is_active": True})
    
    # Total occupied = railroad guests + other guests
    total_occupied = occupied_by_railroad + blocked_rooms
    
    # Get available rooms
    available_rooms = total_rooms - total_occupied
    
    # Get dirty rooms count (rooms needing cleaning)
    dirty_rooms = await db.rooms.count_documents({"status": "dirty"})
    
    # Get rooms in maintenance
    maintenance_rooms = await db.rooms.count_documents({"status": "maintenance"})
    
    # Clean available rooms (ready to use)
    clean_available = available_rooms - dirty_rooms - maintenance_rooms
    if clean_available < 0:
        clean_available = 0
    
    return {
        "total_rooms": total_rooms,
        "occupied_by_railroad": occupied_by_railroad,
        "blocked_rooms": blocked_rooms,
        "total_occupied": total_occupied,
        "available_rooms": available_rooms,
        "dirty_rooms": dirty_rooms,
        "maintenance_rooms": maintenance_rooms,
        "clean_available": clean_available
    }


async def send_email_notification(subject: str, body: str):
    """Send email notification to CPKC using configured SMTP settings."""
    settings = await db.settings.find_one({"id": "portal_settings"}, {"_id": 0})
    
    if not settings or not settings.get("email_sender") or not settings.get("email_password_encrypted"):
        logging.warning("Email settings not configured - cannot send notification")
        return False
    
    try:
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        
        smtp_host = settings.get("email_smtp_host", "smtp.zoho.com")
        smtp_port = settings.get("email_smtp_port", 587)
        sender = settings.get("email_sender")
        password = decrypt_data(settings.get("email_password_encrypted"))
        
        # Create email
        msg = MIMEMultipart()
        msg['From'] = sender
        msg['To'] = ", ".join(CPKC_EMAIL_RECIPIENTS)
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))
        
        # Send email
        server = smtplib.SMTP(smtp_host, smtp_port)
        server.starttls()
        server.login(sender, password)
        server.sendmail(sender, CPKC_EMAIL_RECIPIENTS, msg.as_string())
        server.quit()
        
        logging.info(f"Email notification sent: {subject}")
        return True
        
    except Exception as e:
        logging.error(f"Failed to send email notification: {e}")
        return False


async def send_room_available_notification():
    """Send notification when rooms become available after being sold out."""
    today = datetime.now().strftime("%Y-%m-%d")
    
    # Check if we were sold out (from database - persists across restarts)
    state = await get_notification_state()
    if not state.get("was_sold_out"):
        logging.info("Room available check: Not in sold-out state, skipping notification")
        return  # We weren't sold out, no need to notify
    
    room_info = await get_room_availability_details()
    
    # Don't send if still sold out
    if room_info["available_rooms"] <= 0:
        logging.info(f"Room available check: Still at 0 available rooms")
        return
    
    logging.info(f"Room available check: Was sold out, now have {room_info['available_rooms']} rooms available - sending notification")
    
    subject = f"Hodler Inn - Rooms Now Available ({today})"
    
    body = f"""Hello,

This is an automated notification from Hodler Inn.

GOOD NEWS! Rooms are now available after being at 100% capacity.

ROOM AVAILABILITY:
- Total Rooms Available: {room_info['available_rooms']}
- Clean & Ready: {room_info['clean_available']}
- Being Cleaned: {room_info['dirty_rooms']}

CURRENT OCCUPANCY:
- Railroad Crew In-House: {room_info['occupied_by_railroad']}
- Other Guests: {room_info['blocked_rooms']}
- Total Occupied: {room_info['total_occupied']}/{room_info['total_rooms']}

Thank you,
Hodler Inn

---
This is an automated message. Please do not reply to this email.
"""
    
    if await send_email_notification(subject, body):
        # Reset sold-out flag so we can send it again if we hit 100% again
        await set_sold_out_state(None, False)
        logging.info("Room available notification sent successfully, reset sold-out state")
        
        # Also send Telegram notification
        await send_telegram_notification(
            f"📧 <b>ROOM AVAILABLE ALERT SENT</b>\n"
            f"━━━━━━━━━━━━━━━\n"
            f"✅ Email sent to CPKC\n"
            f"━━━━━━━━━━━━━━━\n"
            f"🏨 Available: {room_info['available_rooms']} rooms\n"
            f"✨ Clean & Ready: {room_info['clean_available']}\n"
            f"🧹 Being Cleaned: {room_info['dirty_rooms']}\n"
            f"━━━━━━━━━━━━━━━\n"
            f"🚂 Railroad: {room_info['occupied_by_railroad']}\n"
            f"👤 Other: {room_info['blocked_rooms']}"
        )
    else:
        logging.error("Failed to send room available notification email")


async def check_and_send_heads_up_notification():
    """Send heads-up notice when only 4 rooms are available."""
    today = datetime.now().strftime("%Y-%m-%d")
    
    # Check if already sent today (from database - persists across restarts)
    state = await get_notification_state()
    if state.get("heads_up_date") == today:
        return  # Already sent today
    
    room_info = await get_room_availability_details()
    
    # Send heads-up when exactly 4 or fewer rooms available (but more than 0)
    if room_info["available_rooms"] > 4 or room_info["available_rooms"] <= 0:
        return
    
    logging.info(f"Heads-up check: Only {room_info['available_rooms']} rooms available - sending notification")
    
    subject = f"Hodler Inn - HEADS UP: Low Room Availability ({today})"
    
    body = f"""Hello,

This is a HEADS UP notice from Hodler Inn.

We have limited room availability. Please prepare for incoming crews.

ROOM STATUS:
- Rooms Available: {room_info['available_rooms']}
- Clean & Ready: {room_info['clean_available']}
- Being Cleaned: {room_info['dirty_rooms']}

CURRENT OCCUPANCY:
- Railroad Crew In-House: {room_info['occupied_by_railroad']}
- Other Guests (Blocked Rooms): {room_info['blocked_rooms']}
- Total Occupied: {room_info['total_occupied']}/{room_info['total_rooms']}

Please plan accordingly for any additional crew arrivals.

Thank you,
Hodler Inn

---
This is an automated message. Please do not reply to this email.
"""
    
    if await send_email_notification(subject, body):
        await set_heads_up_state(today)
        logging.info("Heads-up notification sent successfully")
        
        # Also send Telegram notification
        await send_telegram_notification(
            f"📧 <b>HEADS UP NOTICE SENT</b>\n"
            f"━━━━━━━━━━━━━━━\n"
            f"⚠️ Low Room Availability\n"
            f"✅ Email sent to CPKC\n"
            f"━━━━━━━━━━━━━━━\n"
            f"🏨 Available: {room_info['available_rooms']} rooms\n"
            f"✨ Clean & Ready: {room_info['clean_available']}\n"
            f"🧹 Being Cleaned: {room_info['dirty_rooms']}\n"
            f"━━━━━━━━━━━━━━━\n"
            f"🚂 Railroad In-House: {room_info['occupied_by_railroad']}\n"
            f"👤 Other Guests: {room_info['blocked_rooms']}"
        )


async def check_and_send_sold_out_notification():
    """Check if all rooms are occupied and send notification to railroad company"""
    today = datetime.now().strftime("%Y-%m-%d")
    
    # Get total rooms count
    total_rooms = await db.rooms.count_documents({})
    if total_rooms == 0:
        total_rooms = 28  # Default to 28 if rooms not configured
    
    # Get occupied rooms count (railroad guests)
    occupied_by_railroad = await db.bookings.count_documents({"is_checked_out": False})
    
    # Get blocked rooms count (other guests)
    blocked_rooms = await db.blocked_rooms.count_documents({"is_active": True})
    
    # Total occupied = railroad guests + other guests
    total_occupied = occupied_by_railroad + blocked_rooms
    
    # Check if we're at 100% capacity
    if total_occupied >= total_rooms:
        # Check if already sent today (from database - persists across restarts)
        state = await get_notification_state()
        if state.get("sold_out_date") == today:
            return  # Already sent today
        
        # Get email settings
        settings = await db.settings.find_one({"id": "portal_settings"}, {"_id": 0})
        
        if settings and settings.get("email_sender") and settings.get("email_password_encrypted"):
            try:
                import smtplib
                from email.mime.text import MIMEText
                from email.mime.multipart import MIMEMultipart
                
                smtp_host = settings.get("email_smtp_host", "smtp.zoho.com")
                smtp_port = settings.get("email_smtp_port", 587)
                sender = settings.get("email_sender")
                password = decrypt_data(settings.get("email_password_encrypted"))
                
                # Railroad company emails
                recipients = ["crewtravel@cpkcr.com", "crewmanagers@cpkcr.com"]
                
                # Create email
                msg = MIMEMultipart()
                msg['From'] = sender
                msg['To'] = ", ".join(recipients)
                msg['Subject'] = f"Hodler Inn - 100% Occupied ({today})"
                
                body = f"""Hello,

This is an automated notification from Hodler Inn.

We are currently 100% occupied with {total_occupied} rooms in house.

More rooms will become available as crew gets called out from the hotel.

Thank you,
Hodler Inn

---
This is an automated message. Please do not reply to this email.
"""
                msg.attach(MIMEText(body, 'plain'))
                
                # Send email
                server = smtplib.SMTP(smtp_host, smtp_port)
                server.starttls()
                server.login(sender, password)
                server.sendmail(sender, recipients, msg.as_string())
                server.quit()
                
                # Set sold-out state in database (persists across restarts)
                await set_sold_out_state(today, True)
                logging.info(f"Sold-out notification sent to railroad company: {recipients}")
                
                # Also send Telegram notification
                await send_telegram_notification(
                    f"📧 <b>SOLD OUT NOTIFICATION SENT</b>\n"
                    f"━━━━━━━━━━━━━━━\n"
                    f"✅ Email sent to:\n"
                    f"• crewtravel@cpkcr.com\n"
                    f"• crewmanagers@cpkcr.com\n"
                    f"━━━━━━━━━━━━━━━\n"
                    f"🏨 {total_occupied}/{total_rooms} rooms occupied\n"
                    f"🚂 Railroad: {occupied_by_railroad}\n"
                    f"👤 Other: {blocked_rooms}"
                )
                
            except Exception as e:
                logging.error(f"Failed to send sold-out notification: {e}")
        else:
            logging.warning("Email settings not configured - cannot send sold-out notification")

@api_router.get("/guests/{employee_number}")
async def get_guest(employee_number: str):
    guest = await db.guests.find_one({"employee_number": employee_number}, {"_id": 0})
    if not guest:
        raise HTTPException(status_code=404, detail="Guest not found")
    
    # Decrypt data before returning
    if 'name_encrypted' in guest:
        guest['name'] = decrypt_data(guest['name_encrypted'])
    
    # IMPORTANT: Check if employee name has been updated in the employees collection
    # This ensures the Guest Portal always shows the latest name (e.g., after admin updates to match portal format)
    employee = await db.employees.find_one({"employee_number": employee_number}, {"_id": 0})
    if employee and employee.get("name"):
        employee_name = employee.get("name")
        guest_name = guest.get("name", "")
        
        # If names differ, use the employee name (which is the authoritative source)
        if employee_name != guest_name:
            logging.info(f"Guest name sync: Using employee name '{employee_name}' instead of stored guest name '{guest_name}' for employee {employee_number}")
            guest['name'] = employee_name
            
            # Also update the guest record in the background so it stays in sync
            await db.guests.update_one(
                {"employee_number": employee_number},
                {"$set": {"name": employee_name, "name_encrypted": encrypt_data(employee_name)}}
            )
    
    return guest


# Request employee access - sends Telegram notification to admin with approval buttons
class AccessRequest(BaseModel):
    employee_number: str
    name: str

@api_router.post("/request-employee-access")
async def request_employee_access(request: AccessRequest):
    """Guest requests access when their Employee ID is not in the system.
    Sends a Telegram notification to admin with Approve/Reject buttons."""
    
    # Check if already in system
    existing_employee = await db.employees.find_one({"employee_number": request.employee_number})
    if existing_employee:
        raise HTTPException(status_code=400, detail="Employee ID already exists in system")
    
    existing_guest = await db.guests.find_one({"employee_number": request.employee_number})
    if existing_guest:
        raise HTTPException(status_code=400, detail="Guest already registered")
    
    # Check if there's already a pending request for this employee
    existing_request = await db.pending_access_requests.find_one({"employee_number": request.employee_number})
    if existing_request:
        raise HTTPException(status_code=400, detail="Access request already pending for this employee")
    
    # Store the request in MongoDB
    request_id = str(uuid.uuid4())[:8]
    request_doc = {
        "request_id": request_id,
        "employee_number": request.employee_number,
        "name": request.name,
        "status": "pending",
        "requested_at": datetime.now(timezone.utc).isoformat()
    }
    await db.pending_access_requests.insert_one(request_doc)
    
    # Send Telegram notification with inline buttons
    chat_id = await get_telegram_chat_id()
    if TELEGRAM_BOT_TOKEN and chat_id:
        try:
            message = (
                f"🆕 *NEW ACCESS REQUEST*\n\n"
                f"👤 Name: *{request.name}*\n"
                f"📋 Employee ID: `{request.employee_number}`\n"
                f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
                f"Tap below to approve or reject:"
            )
            
            # Inline keyboard with Approve and Reject buttons
            inline_keyboard = {
                "inline_keyboard": [[
                    {"text": "✅ Approve", "callback_data": f"approve_{request_id}"},
                    {"text": "❌ Reject", "callback_data": f"reject_{request_id}"}
                ]]
            }
            
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
            async with httpx.AsyncClient() as http_client:
                await http_client.post(url, json={
                    "chat_id": chat_id,
                    "text": message,
                    "parse_mode": "Markdown",
                    "reply_markup": inline_keyboard
                })
        except Exception as e:
            logging.error(f"Failed to send Telegram notification: {e}")
    
    return {"message": "Access request sent to admin", "employee_number": request.employee_number}


@api_router.post("/telegram-webhook")
async def telegram_webhook(request_data: dict):
    """Handle Telegram callback queries (button clicks) for access approvals."""
    
    if "callback_query" not in request_data:
        return {"ok": True}
    
    callback = request_data["callback_query"]
    callback_id = callback.get("id")
    data = callback.get("data", "")
    message = callback.get("message", {})
    chat_id = message.get("chat", {}).get("id")
    message_id = message.get("message_id")
    
    # Parse the callback data
    if data.startswith("approve_"):
        request_id = data.replace("approve_", "")
        
        # Find the pending request in MongoDB
        request_info = await db.pending_access_requests.find_one({"request_id": request_id, "status": "pending"})
        
        if request_info:
            # Add employee to the system
            employee_doc = {
                "id": str(uuid.uuid4()),
                "employee_number": request_info["employee_number"],
                "name": request_info["name"],
                "source": "telegram_approval",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "is_active": True
            }
            await db.employees.insert_one(employee_doc)
            
            # Update request status in MongoDB
            await db.pending_access_requests.update_one(
                {"request_id": request_id},
                {"$set": {"status": "approved", "processed_at": datetime.now(timezone.utc).isoformat()}}
            )
            
            response_text = f"✅ *APPROVED*\n\n{request_info['name']} ({request_info['employee_number']}) has been added to the system."
        else:
            response_text = "⚠️ Request expired or already processed."
            
    elif data.startswith("reject_"):
        request_id = data.replace("reject_", "")
        
        # Find the pending request in MongoDB
        request_info = await db.pending_access_requests.find_one({"request_id": request_id, "status": "pending"})
        
        if request_info:
            # Update request status to rejected
            await db.pending_access_requests.update_one(
                {"request_id": request_id},
                {"$set": {"status": "rejected", "processed_at": datetime.now(timezone.utc).isoformat()}}
            )
            response_text = f"❌ *REJECTED*\n\n{request_info['name']} ({request_info['employee_number']}) was not added."
        else:
            response_text = "⚠️ Request expired or already processed."
    else:
        response_text = "Unknown action"
    
    # Answer the callback query
    if TELEGRAM_BOT_TOKEN:
        try:
            # Answer callback to remove loading state
            answer_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/answerCallbackQuery"
            async with httpx.AsyncClient() as http_client:
                await http_client.post(answer_url, json={
                    "callback_query_id": callback_id,
                    "text": "Processed!"
                })
                
                # Edit the message to show result
                edit_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/editMessageText"
                await http_client.post(edit_url, json={
                    "chat_id": chat_id,
                    "message_id": message_id,
                    "text": response_text,
                    "parse_mode": "Markdown"
                })
        except Exception as e:
            logging.error(f"Failed to respond to Telegram callback: {e}")
    
    return {"ok": True}


@api_router.get("/pending-access-requests")
async def get_pending_requests():
    """Get all pending access requests (for admin dashboard)."""
    requests = await db.pending_access_requests.find(
        {"status": "pending"}, 
        {"_id": 0}
    ).sort("requested_at", -1).to_list(100)
    return requests



# Admin: Get all registered guests with verification status
@api_router.get("/admin/guests")
async def get_all_guests():
    """Get all registered guests for admin review"""
    guests = await db.guests.find({}, {"_id": 0}).sort("created_at", -1).to_list(500)
    
    # Decrypt names and add check-in count
    for guest in guests:
        if 'name_encrypted' in guest:
            guest['name'] = decrypt_data(guest['name_encrypted'])
            del guest['name_encrypted']
        
        # Get check-in count for this guest
        check_in_count = await db.bookings.count_documents({"employee_number": guest["employee_number"]})
        guest['check_in_count'] = check_in_count
    
    return guests

# Admin: Verify a guest
@api_router.post("/admin/guests/{employee_number}/verify")
async def verify_guest(employee_number: str):
    """Mark a guest as verified by admin"""
    guest = await db.guests.find_one({"employee_number": employee_number}, {"_id": 0})
    if not guest:
        raise HTTPException(status_code=404, detail="Guest not found")
    
    await db.guests.update_one(
        {"employee_number": employee_number},
        {"$set": {
            "is_verified": True,
            "verified_at": datetime.now(timezone.utc).isoformat(),
            "pending_verification": False
        }}
    )
    
    # Also update employee record
    await db.employees.update_one(
        {"employee_number": employee_number},
        {"$set": {
            "is_verified": True,
            "pending_verification": False
        }}
    )
    
    # Decrypt name for notification
    name = decrypt_data(guest.get('name_encrypted', guest.get('name', 'Unknown')))
    
    await send_telegram_notification(
        f"✅ <b>GUEST VERIFIED</b>\n"
        f"━━━━━━━━━━━━━━━\n"
        f"👤 {name}\n"
        f"🆔 {employee_number}\n"
        f"━━━━━━━━━━━━━━━"
    )
    
    return {"message": f"Guest {name} verified successfully"}


class BulkVerifyRequest(BaseModel):
    employee_numbers: List[str]


@api_router.post("/admin/guests/bulk-verify")
async def bulk_verify_guests(request: BulkVerifyRequest):
    """Bulk verify multiple guests at once"""
    verified_count = 0
    verified_names = []
    
    for employee_number in request.employee_numbers:
        guest = await db.guests.find_one({"employee_number": employee_number}, {"_id": 0})
        if guest:
            await db.guests.update_one(
                {"employee_number": employee_number},
                {"$set": {
                    "is_verified": True,
                    "verified_at": datetime.now(timezone.utc).isoformat(),
                    "pending_verification": False
                }}
            )
            
            # Also update employee record
            await db.employees.update_one(
                {"employee_number": employee_number},
                {"$set": {
                    "is_verified": True,
                    "pending_verification": False
                }}
            )
            
            name = decrypt_data(guest.get('name_encrypted', guest.get('name', 'Unknown')))
            verified_names.append(name)
            verified_count += 1
    
    if verified_count > 0:
        await send_telegram_notification(
            f"✅ <b>BULK VERIFICATION</b>\n"
            f"━━━━━━━━━━━━━━━\n"
            f"Verified {verified_count} guests\n"
            f"━━━━━━━━━━━━━━━"
        )
    
    return {"message": f"Verified {verified_count} guests", "verified": verified_names}


@api_router.get("/admin/guests/pending-verification")
async def get_pending_verification_guests():
    """Get all guests pending verification"""
    guests = await db.guests.find(
        {"$or": [{"pending_verification": True}, {"is_verified": False}]},
        {"_id": 0}
    ).to_list(1000)
    
    # Decrypt names
    for guest in guests:
        if 'name_encrypted' in guest:
            guest['name'] = decrypt_data(guest['name_encrypted'])
    
    return guests

# Admin: Flag a guest (unverify/block)
@api_router.post("/admin/guests/{employee_number}/flag")
async def flag_guest(employee_number: str):
    """Flag a guest for review (unverify)"""
    guest = await db.guests.find_one({"employee_number": employee_number}, {"_id": 0})
    if not guest:
        raise HTTPException(status_code=404, detail="Guest not found")
    
    await db.guests.update_one(
        {"employee_number": employee_number},
        {"$set": {"is_verified": False, "is_flagged": True}}
    )
    
    name = decrypt_data(guest.get('name_encrypted', guest.get('name', 'Unknown')))
    
    await send_telegram_notification(
        f"🚩 <b>GUEST FLAGGED</b>\n"
        f"━━━━━━━━━━━━━━━\n"
        f"👤 {name}\n"
        f"🆔 {employee_number}\n"
        f"━━━━━━━━━━━━━━━\n"
        f"⚠️ Please review in Admin Dashboard"
    )
    
    return {"message": f"Guest {name} flagged for review"}


@api_router.post("/admin/guests/{employee_number}/block")
async def block_guest(employee_number: str):
    """Block a guest from checking in again"""
    guest = await db.guests.find_one({"employee_number": employee_number}, {"_id": 0})
    if not guest:
        raise HTTPException(status_code=404, detail="Guest not found")
    
    await db.guests.update_one(
        {"employee_number": employee_number},
        {"$set": {"is_blocked": True, "blocked_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    # Also mark in employees collection
    await db.employees.update_one(
        {"employee_number": employee_number},
        {"$set": {"is_blocked": True}}
    )
    
    name = decrypt_data(guest.get('name_encrypted', guest.get('name', 'Unknown')))
    
    await send_telegram_notification(
        f"🚫 <b>GUEST BLOCKED</b>\n"
        f"━━━━━━━━━━━━━━━\n"
        f"👤 {name}\n"
        f"🆔 {employee_number}\n"
        f"━━━━━━━━━━━━━━━\n"
        f"❌ Cannot check in again"
    )
    
    return {"message": f"Guest {name} has been blocked"}


@api_router.post("/admin/guests/{employee_number}/unblock")
async def unblock_guest(employee_number: str):
    """Unblock a previously blocked guest"""
    guest = await db.guests.find_one({"employee_number": employee_number}, {"_id": 0})
    if not guest:
        raise HTTPException(status_code=404, detail="Guest not found")
    
    await db.guests.update_one(
        {"employee_number": employee_number},
        {"$set": {"is_blocked": False, "unblocked_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    # Also update in employees collection
    await db.employees.update_one(
        {"employee_number": employee_number},
        {"$set": {"is_blocked": False}}
    )
    
    name = decrypt_data(guest.get('name_encrypted', guest.get('name', 'Unknown')))
    
    return {"message": f"Guest {name} has been unblocked"}


@api_router.delete("/admin/guests/{employee_number}")
async def remove_guest(employee_number: str):
    """Remove an unverified guest from the system"""
    guest = await db.guests.find_one({"employee_number": employee_number}, {"_id": 0})
    if not guest:
        raise HTTPException(status_code=404, detail="Guest not found")
    
    name = decrypt_data(guest.get('name_encrypted', guest.get('name', 'Unknown')))
    
    # Check if guest has any bookings
    booking_count = await db.bookings.count_documents({"employee_number": employee_number})
    
    # Remove from guests collection
    await db.guests.delete_one({"employee_number": employee_number})
    
    # Remove from employees collection if pending verification
    await db.employees.delete_one({
        "employee_number": employee_number,
        "pending_verification": True
    })
    
    await send_telegram_notification(
        f"🗑️ <b>GUEST REMOVED</b>\n"
        f"━━━━━━━━━━━━━━━\n"
        f"👤 {name}\n"
        f"🆔 {employee_number}\n"
        f"📋 Had {booking_count} booking(s)"
    )
    
    return {"message": f"Guest {name} removed from system", "had_bookings": booking_count}


# Check-In (signature captured here)
@api_router.post("/checkin", response_model=CheckIn)
async def check_in(input: CheckInCreate):
    # Verify employee is registered
    guest = await db.guests.find_one({"employee_number": input.employee_number}, {"_id": 0})
    if not guest:
        raise HTTPException(status_code=404, detail="Employee not registered. Please register first.")
    
    # Check if guest is blocked
    if guest.get('is_blocked'):
        raise HTTPException(status_code=403, detail="This employee has been blocked. Please contact front desk.")
    
    # Check if this is a returning unverified guest (not allowed for 2nd check-in)
    previous_checkins = await db.bookings.count_documents({"employee_number": input.employee_number})
    is_unverified = guest.get('pending_verification') or not guest.get('is_verified', True)
    
    if previous_checkins > 0 and is_unverified:
        raise HTTPException(
            status_code=403, 
            detail="Cannot check in again until verified by admin. Please contact front desk."
        )
    
    # Decrypt guest name for notification
    guest_name = decrypt_data(guest.get('name_encrypted', guest.get('name', 'Unknown')))
    
    # Check if room is already occupied
    active_booking = await db.bookings.find_one({
        "room_number": input.room_number,
        "is_checked_out": False
    }, {"_id": 0})
    if active_booking:
        raise HTTPException(status_code=400, detail="Room is already occupied")
    
    # Check if employee already has an active check-in
    active_employee = await db.bookings.find_one({
        "employee_number": input.employee_number,
        "is_checked_out": False
    }, {"_id": 0})
    if active_employee:
        raise HTTPException(status_code=400, detail="Employee already has an active check-in")
    
    checkin = CheckIn(**input.model_dump())
    doc = checkin.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    
    # Encrypt signature before storing
    if doc.get('signature'):
        doc['signature_encrypted'] = encrypt_data(doc['signature'])
        del doc['signature']  # Don't store unencrypted
    
    await db.bookings.insert_one(doc)
    
    # Update room status to occupied (regardless of previous status - dirty, maintenance, etc.)
    await db.rooms.update_one(
        {"room_number": input.room_number},
        {"$set": {"status": "occupied"}}
    )
    
    # Also remove any "other guest" block on this room if it exists
    await db.blocked_rooms.update_one(
        {"room_number": input.room_number, "is_active": True},
        {"$set": {"is_active": False, "unblocked_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    # Check if this is a first-time check-in
    check_in_count = await db.bookings.count_documents({"employee_number": input.employee_number})
    is_first_time = check_in_count == 1
    
    # Check if employee is in admin's pre-approved list
    employee_in_list = await db.employees.find_one({"employee_number": input.employee_number})
    is_pre_approved = employee_in_list is not None
    
    # Send Telegram notification for check-in
    if is_first_time and not is_pre_approved:
        # First time guest NOT in admin list - needs verification
        await send_telegram_notification(
            f"🆕🆕🆕 <b>NEW GUEST CHECK-IN</b> 🆕🆕🆕\n"
            f"━━━━━━━━━━━━━━━\n"
            f"⚠️ <b>FIRST TIME - PLEASE VERIFY</b>\n"
            f"━━━━━━━━━━━━━━━\n"
            f"👤 <b>Name:</b> {guest_name}\n"
            f"🆔 <b>Employee ID:</b> {input.employee_number}\n"
            f"🚪 <b>Room:</b> {input.room_number}\n"
            f"📅 <b>Date:</b> {input.check_in_date}\n"
            f"🕐 <b>Time:</b> {input.check_in_time}\n"
            f"━━━━━━━━━━━━━━━\n"
            f"✅ Verify this person in Admin Dashboard"
        )
    else:
        # Pre-approved employee or returning guest - simple notification
        await send_telegram_notification(
            f"🟢 <b>CHECK-IN</b>\n"
            f"━━━━━━━━━━━━━━━\n"
            f"👤 <b>Guest:</b> {guest_name}\n"
            f"🆔 <b>ID:</b> {input.employee_number}\n"
            f"🚪 <b>Room:</b> {input.room_number}\n"
            f"📅 {input.check_in_date} @ {input.check_in_time}"
        )
    
    # Check if we're now at 100% capacity and send notification to railroad company
    await check_and_send_sold_out_notification()
    
    # Check if we're low on rooms (4 or fewer) and send heads-up notice
    await check_and_send_heads_up_notification()
    
    return checkin

# Verify Check-Out - Verify room and employee number match before checkout
@api_router.get("/verify-checkout/{room_number}/{employee_number}")
async def verify_checkout(room_number: str, employee_number: str):
    """Verify that room number and employee number match an active booking"""
    # Find active booking for room
    booking = await db.bookings.find_one({
        "room_number": room_number,
        "is_checked_out": False
    }, {"_id": 0})
    
    if not booking:
        raise HTTPException(status_code=404, detail=f"No active check-in found for Room {room_number}")
    
    # Verify employee number matches
    if booking['employee_number'] != employee_number:
        raise HTTPException(
            status_code=400, 
            detail=f"Employee number does not match the check-in record for Room {room_number}. Please verify your employee ID."
        )
    
    # Get guest info
    guest = await db.guests.find_one({"employee_number": employee_number}, {"_id": 0})
    if not guest:
        raise HTTPException(status_code=404, detail="Guest record not found")
    
    # Decrypt guest name
    guest_name = decrypt_data(guest.get('name_encrypted', guest.get('name', '')))
    
    return {
        "verified": True,
        "employee_name": guest_name,
        "employee_number": employee_number,
        "room_number": room_number,
        "check_in_date": booking['check_in_date'],
        "check_in_time": booking['check_in_time'],
        "booking_id": booking['id']
    }

# Lookup booking by room number only (for auto-fill employee number)
@api_router.get("/lookup-room/{room_number}")
async def lookup_room_booking(room_number: str):
    """Lookup active booking by room number - returns guest info for auto-fill"""
    # Find active booking for room
    booking = await db.bookings.find_one({
        "room_number": room_number,
        "is_checked_out": False
    }, {"_id": 0})
    
    if not booking:
        raise HTTPException(status_code=404, detail=f"No active check-in found for Room {room_number}")
    
    # Get guest info
    guest = await db.guests.find_one({"employee_number": booking['employee_number']}, {"_id": 0})
    if not guest:
        raise HTTPException(status_code=404, detail="Guest record not found")
    
    # Decrypt guest name
    guest_name = decrypt_data(guest.get('name_encrypted', guest.get('name', '')))
    
    return {
        "found": True,
        "employee_name": guest_name,
        "employee_number": booking['employee_number'],
        "room_number": room_number,
        "check_in_date": booking['check_in_date'],
        "check_in_time": booking['check_in_time'],
        "booking_id": booking['id']
    }

# Check-Out
@api_router.post("/checkout")
async def check_out(input: CheckOutCreate):
    # Find active booking for room
    booking = await db.bookings.find_one({
        "room_number": input.room_number,
        "is_checked_out": False
    }, {"_id": 0})
    
    if not booking:
        raise HTTPException(status_code=404, detail="No active booking found for this room")
    
    # Verify employee number if provided
    if input.employee_number and booking['employee_number'] != input.employee_number:
        raise HTTPException(
            status_code=400, 
            detail="Employee number does not match the check-in record. Please verify your employee ID."
        )
    
    # Get guest info for notification
    guest = await db.guests.find_one({"employee_number": booking['employee_number']}, {"_id": 0})
    
    # Calculate stay duration
    total_hours, total_nights = calculate_stay_duration(
        booking['check_in_date'],
        booking['check_in_time'],
        input.check_out_date,
        input.check_out_time
    )
    
    # Update booking with checkout info
    await db.bookings.update_one(
        {"id": booking['id']},
        {
            "$set": {
                "check_out_date": input.check_out_date,
                "check_out_time": input.check_out_time,
                "is_checked_out": True
            }
        }
    )
    
    # Send Telegram notification for check-out
    guest_name = decrypt_data(guest.get('name_encrypted', guest.get('name', 'Unknown'))) if guest else "Unknown"
    await send_telegram_notification(
        f"🔴🔴🔴 <b>CHECK-OUT</b> 🔴🔴🔴\n"
        f"━━━━━━━━━━━━━━━\n"
        f"🚪 <b>Guest:</b> {guest_name}\n"
        f"🚪 <b>Employee ID:</b> {booking['employee_number']}\n"
        f"🚪 <b>Room:</b> {input.room_number}\n"
        f"🚪 <b>Date:</b> {input.check_out_date}\n"
        f"🚪 <b>Time:</b> {input.check_out_time}\n"
        f"⏱️ <b>Duration:</b> {total_hours}h\n"
        f"🌙 <b>Nights Billed:</b> {total_nights}\n"
        f"━━━━━━━━━━━━━━━"
    )
    
    # Mark room as dirty (needs cleaning) after checkout
    await db.rooms.update_one(
        {"room_number": input.room_number},
        {"$set": {"status": "dirty"}}
    )
    
    # Check if rooms are now available after being sold out (send notification to CPKC)
    await send_room_available_notification()
    
    return {"message": "Check-out successful", "booking_id": booking['id']}

# ==================== Edit/Delete Bookings ====================

class BookingUpdate(BaseModel):
    room_number: Optional[str] = None
    check_in_date: Optional[str] = None
    check_in_time: Optional[str] = None
    check_out_date: Optional[str] = None
    check_out_time: Optional[str] = None

# Edit a booking
@api_router.put("/admin/bookings/{booking_id}")
async def update_booking(booking_id: str, input: BookingUpdate):
    booking = await db.bookings.find_one({"id": booking_id}, {"_id": 0})
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    update_data = {k: v for k, v in input.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No data to update")
    
    await db.bookings.update_one({"id": booking_id}, {"$set": update_data})
    
    return {"message": "Booking updated successfully"}

# Delete a booking
@api_router.delete("/admin/bookings/{booking_id}")
async def delete_booking(booking_id: str):
    booking = await db.bookings.find_one({"id": booking_id}, {"_id": 0})
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    await db.bookings.delete_one({"id": booking_id})
    
    return {"message": "Booking deleted successfully"}

# Admin Login
@api_router.post("/admin/login")
async def admin_login(input: AdminLogin):
    if input.password == ADMIN_PASSWORD:
        return {"success": True, "message": "Login successful"}
    raise HTTPException(status_code=401, detail="Invalid password")

# Admin - Get all records (with optional date filtering)
@api_router.get("/admin/records", response_model=List[GuestRecord])
async def get_all_records(
    start_date: Optional[str] = Query(None, description="Filter from date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="Filter to date (YYYY-MM-DD)")
):
    # Build query with optional date filters
    query = {}
    if start_date or end_date:
        date_filter = {}
        if start_date:
            date_filter["$gte"] = start_date
        if end_date:
            date_filter["$lte"] = end_date
        if date_filter:
            query["check_in_date"] = date_filter
    
    # Sort by check_in_date and check_in_time
    bookings = await db.bookings.find(query, {"_id": 0}).sort([
        ("check_in_date", 1),  # Ascending by date
        ("check_in_time", 1)   # Then by time
    ]).to_list(1000)
    
    # Batch fetch all guests to avoid N+1 query
    employee_numbers = [b['employee_number'] for b in bookings]
    guests_list = await db.guests.find({"employee_number": {"$in": employee_numbers}}, {"_id": 0}).to_list(1000)
    guests_dict = {g['employee_number']: g for g in guests_list}
    
    records = []
    for booking in bookings:
        guest = guests_dict.get(booking['employee_number'])
        if guest:
            total_hours = None
            total_nights = None
            
            if booking.get('is_checked_out') and booking.get('check_out_date'):
                total_hours, total_nights = calculate_stay_duration(
                    booking['check_in_date'],
                    booking['check_in_time'],
                    booking['check_out_date'],
                    booking['check_out_time']
                )
            
            # Decrypt sensitive data
            decrypted_name = decrypt_data(guest.get('name_encrypted', guest.get('name', '')))
            # Signature is now stored in booking, not guest
            decrypted_signature = decrypt_data(booking.get('signature_encrypted', ''))
            
            records.append(GuestRecord(
                id=booking['id'],
                employee_number=booking['employee_number'],
                employee_name=decrypted_name,
                signature=decrypted_signature,
                room_number=booking['room_number'],
                check_in_date=booking['check_in_date'],
                check_in_time=booking['check_in_time'],
                check_out_date=booking.get('check_out_date'),
                check_out_time=booking.get('check_out_time'),
                total_hours=total_hours,
                total_nights=total_nights,
                is_checked_out=booking['is_checked_out']
            ))
    
    return records

# Admin - Dashboard stats
@api_router.get("/admin/stats")
async def get_dashboard_stats():
    total_guests = await db.guests.count_documents({})
    total_checkins = await db.bookings.count_documents({})
    active_stays = await db.bookings.count_documents({"is_checked_out": False})
    completed_stays = await db.bookings.count_documents({"is_checked_out": True})
    
    return {
        "total_guests": total_guests,
        "total_checkins": total_checkins,
        "active_stays": active_stays,
        "completed_stays": completed_stays
    }

# Admin - Export to Excel (Sign-In Sheet Format)
@api_router.get("/admin/export")
async def export_to_excel():
    bookings = await db.bookings.find({}, {"_id": 0}).sort([("check_in_date", 1), ("check_in_time", 1)]).to_list(1000)
    
    # Batch fetch all guests to avoid N+1 query
    employee_numbers = [b['employee_number'] for b in bookings]
    guests_list = await db.guests.find({"employee_number": {"$in": employee_numbers}}, {"_id": 0}).to_list(1000)
    guests_dict = {g['employee_number']: g for g in guests_list}
    
    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output, {'in_memory': True})
    worksheet = workbook.add_worksheet("Sign-In Sheet")
    
    # Styles
    title_format = workbook.add_format({
        'bold': True,
        'font_size': 14,
        'align': 'center',
        'valign': 'vcenter'
    })
    subtitle_format = workbook.add_format({
        'font_size': 10,
        'align': 'center',
        'valign': 'vcenter'
    })
    header_format = workbook.add_format({
        'bold': True,
        'bg_color': '#fbbf24',
        'border': 1,
        'align': 'center',
        'valign': 'vcenter',
        'text_wrap': True
    })
    cell_format = workbook.add_format({
        'border': 1,
        'align': 'center',
        'valign': 'vcenter'
    })
    signed_format = workbook.add_format({
        'border': 1,
        'align': 'center',
        'valign': 'vcenter',
        'font_color': '#10b981'
    })
    
    # Company Header
    worksheet.merge_range('A1:K1', 'Hodler Inn', title_format)
    worksheet.merge_range('A2:K2', '820 Hwy 59 N Heavener, OK, 74937', subtitle_format)
    worksheet.merge_range('A3:K3', 'Phone: 918-653-7801', subtitle_format)
    worksheet.set_row(0, 25)
    worksheet.set_row(1, 18)
    worksheet.set_row(2, 18)
    
    # Column Headers (Row 5, index 4)
    headers = [
        "#", "Stay Type", "Name", "Employee ID", 
        "Signature In", "Signature Out",
        "Date In", "Time In", "Date Out", "Time Out", "Room #"
    ]
    
    col_widths = [5, 12, 20, 12, 12, 12, 12, 10, 12, 10, 8]
    for col, (header, width) in enumerate(zip(headers, col_widths)):
        worksheet.write(4, col, header, header_format)
        worksheet.set_column(col, col, width)
    
    # Data rows starting from row 6 (index 5)
    row = 5
    row_num = 1
    for booking in bookings:
        guest = guests_dict.get(booking['employee_number'])
        if guest:
            # Decrypt data
            decrypted_name = decrypt_data(guest.get('name_encrypted', guest.get('name', '')))
            # Signature is now in booking, not guest
            has_signature = bool(booking.get('signature_encrypted'))
            is_checked_out = booking.get('is_checked_out', False)
            
            worksheet.write(row, 0, row_num, cell_format)
            worksheet.write(row, 1, "Single Stay", cell_format)
            worksheet.write(row, 2, decrypted_name, cell_format)
            worksheet.write(row, 3, booking['employee_number'], cell_format)
            worksheet.write(row, 4, "Signed" if has_signature else "", signed_format if has_signature else cell_format)
            worksheet.write(row, 5, "Signed" if (has_signature and is_checked_out) else "", signed_format if (has_signature and is_checked_out) else cell_format)
            worksheet.write(row, 6, booking['check_in_date'], cell_format)
            worksheet.write(row, 7, booking['check_in_time'], cell_format)
            worksheet.write(row, 8, booking.get('check_out_date', ''), cell_format)
            worksheet.write(row, 9, booking.get('check_out_time', ''), cell_format)
            worksheet.write(row, 10, booking['room_number'], cell_format)
            row += 1
            row_num += 1
    
    # Add empty rows for manual entries (like the paper form)
    for i in range(row_num, 17):
        worksheet.write(row, 0, i, cell_format)
        worksheet.write(row, 1, "Single Stay", cell_format)
        for col in range(2, 11):
            worksheet.write(row, col, "", cell_format)
        row += 1
    
    workbook.close()
    output.seek(0)
    
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=hodler_inn_sign_in_sheet.xlsx"}
    )

# Guarantee Report - Track CPKC room usage vs guaranteed rooms
@api_router.get("/admin/guarantee-report")
async def get_guarantee_report(start_date: str = None, end_date: str = None):
    """Get report showing CPKC room usage vs guaranteed 25 rooms"""
    GUARANTEED_ROOMS = 25
    
    # Get settings for nightly rate
    settings = await db.settings.find_one({"id": "portal_settings"}, {"_id": 0})
    nightly_rate = settings.get("nightly_rate", 75.0) if settings else 75.0
    
    # Build query
    query = {"is_checked_out": True}
    if start_date and end_date:
        query["check_in_date"] = {"$gte": start_date, "$lte": end_date}
    elif start_date:
        query["check_in_date"] = {"$gte": start_date}
    elif end_date:
        query["check_in_date"] = {"$lte": end_date}
    
    # Get all bookings (railroad guests)
    bookings = await db.bookings.find(query, {"_id": 0}).to_list(10000)
    
    # Get blocked rooms history (other guests) - Note: These are not billed to railroad
    blocked_history = await db.blocked_rooms.find({}, {"_id": 0}).to_list(10000)
    
    # Group bookings by date
    daily_data = {}
    for booking in bookings:
        date = booking.get('check_in_date')
        if date:
            if date not in daily_data:
                daily_data[date] = {
                    'date': date,
                    'cpkc_rooms_used': 0,
                    'other_guests': 0,
                    'guaranteed_rooms': GUARANTEED_ROOMS,
                    'unused_guaranteed': 0,
                    'goodwill_amount': 0.0
                }
            daily_data[date]['cpkc_rooms_used'] += 1
    
    # Calculate unused guaranteed rooms and goodwill for each day
    total_goodwill = 0.0
    total_unused = 0
    for date, data in daily_data.items():
        cpkc_used = data['cpkc_rooms_used']
        if cpkc_used < GUARANTEED_ROOMS:
            unused = GUARANTEED_ROOMS - cpkc_used
            data['unused_guaranteed'] = unused
            data['goodwill_amount'] = unused * nightly_rate
            total_unused += unused
            total_goodwill += data['goodwill_amount']
    
    # Sort by date descending
    sorted_data = sorted(daily_data.values(), key=lambda x: x['date'], reverse=True)
    
    # Get turned away guests count
    turned_away_count = await db.turned_away_guests.count_documents({})
    turned_away_in_range = 0
    if start_date or end_date:
        ta_query = {}
        if start_date and end_date:
            ta_query["date"] = {"$gte": start_date, "$lte": end_date}
        elif start_date:
            ta_query["date"] = {"$gte": start_date}
        elif end_date:
            ta_query["date"] = {"$lte": end_date}
        turned_away_in_range = await db.turned_away_guests.count_documents(ta_query)
    else:
        turned_away_in_range = turned_away_count
    
    return {
        "guaranteed_rooms": GUARANTEED_ROOMS,
        "nightly_rate": nightly_rate,
        "total_days": len(sorted_data),
        "total_unused_rooms": total_unused,
        "total_goodwill_amount": total_goodwill,
        "turned_away_count": turned_away_in_range,
        "daily_data": sorted_data
    }


# ==================== Turned Away Guests (Guarantee Goodwill) ====================

class TurnedAwayGuestInput(BaseModel):
    date: str  # YYYY-MM-DD
    guest_name: Optional[str] = "Walk-in Guest"
    bed_type: str = "single"  # "single" or "double"
    room_price: float = 0.0  # Price for the room (higher than CPKC rate)
    reason: Optional[str] = "Holding rooms for CPKC"
    notes: Optional[str] = ""


@api_router.post("/admin/turned-away")
async def log_turned_away_guest(input: TurnedAwayGuestInput):
    """Log a guest that was turned away to hold rooms for CPKC - shows goodwill commitment."""
    doc = {
        "id": str(uuid.uuid4()),
        "date": input.date,
        "guest_name": input.guest_name,
        "bed_type": input.bed_type,
        "room_price": input.room_price,
        "reason": input.reason,
        "notes": input.notes,
        "logged_at": datetime.now(timezone.utc).isoformat()
    }
    await db.turned_away_guests.insert_one(doc)
    
    # Remove _id before returning
    doc.pop('_id', None)
    return {"message": "Turned away guest logged successfully", "record": doc}


@api_router.get("/admin/turned-away")
async def get_turned_away_guests(start_date: str = None, end_date: str = None):
    """Get all turned away guests, optionally filtered by date range."""
    query = {}
    if start_date and end_date:
        query["date"] = {"$gte": start_date, "$lte": end_date}
    elif start_date:
        query["date"] = {"$gte": start_date}
    elif end_date:
        query["date"] = {"$lte": end_date}
    
    guests = await db.turned_away_guests.find(query, {"_id": 0}).sort("date", -1).to_list(1000)
    
    # Group by date for summary
    by_date = {}
    total_lost_revenue = 0.0
    single_bed_count = 0
    double_bed_count = 0
    
    for g in guests:
        date = g.get('date')
        if date not in by_date:
            by_date[date] = 0
        by_date[date] += 1
        total_lost_revenue += g.get('room_price', 0)
        if g.get('bed_type') == 'single':
            single_bed_count += 1
        else:
            double_bed_count += 1
    
    return {
        "total_count": len(guests),
        "total_lost_revenue": total_lost_revenue,
        "single_bed_count": single_bed_count,
        "double_bed_count": double_bed_count,
        "by_date": by_date,
        "records": guests
    }


@api_router.delete("/admin/turned-away/{record_id}")
async def delete_turned_away_guest(record_id: str):
    """Delete a turned away guest record."""
    result = await db.turned_away_guests.delete_one({"id": record_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Record not found")
    return {"message": "Record deleted successfully"}


@api_router.get("/admin/export-guarantee-report")
async def export_guarantee_report(start_date: str = None, end_date: str = None):
    """Export guarantee report as Excel"""
    # Get report data
    report = await get_guarantee_report(start_date, end_date)
    
    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output, {'in_memory': True})
    worksheet = workbook.add_worksheet("Guarantee Report")
    
    # Styles
    title_format = workbook.add_format({
        'bold': True, 'font_size': 16, 'align': 'center', 'valign': 'vcenter'
    })
    subtitle_format = workbook.add_format({
        'font_size': 11, 'align': 'center', 'valign': 'vcenter', 'italic': True
    })
    header_format = workbook.add_format({
        'bold': True, 'bg_color': '#fbbf24', 'border': 1, 'align': 'center', 'valign': 'vcenter'
    })
    cell_format = workbook.add_format({
        'border': 1, 'align': 'center', 'valign': 'vcenter'
    })
    money_format = workbook.add_format({
        'border': 1, 'align': 'center', 'valign': 'vcenter', 'num_format': '$#,##0.00'
    })
    total_format = workbook.add_format({
        'bold': True, 'bg_color': '#fef3c7', 'border': 1, 'align': 'center', 'valign': 'vcenter'
    })
    total_money_format = workbook.add_format({
        'bold': True, 'bg_color': '#fef3c7', 'border': 1, 'align': 'center', 'valign': 'vcenter', 'num_format': '$#,##0.00'
    })
    
    # Set column widths
    worksheet.set_column('A:A', 15)  # Date
    worksheet.set_column('B:B', 18)  # CPKC Rooms Used
    worksheet.set_column('C:C', 18)  # Guaranteed Rooms
    worksheet.set_column('D:D', 18)  # Unused Rooms
    worksheet.set_column('E:E', 18)  # Goodwill Amount
    
    # Title
    worksheet.merge_range('A1:E1', 'HODLER INN - CPKC GUARANTEE REPORT', title_format)
    worksheet.merge_range('A2:E2', f'Guaranteed Rooms: {report["guaranteed_rooms"]} | Nightly Rate: ${report["nightly_rate"]:.2f}', subtitle_format)
    worksheet.merge_range('A3:E3', f'Report Period: {start_date or "All"} to {end_date or "Present"}', subtitle_format)
    
    # Headers
    headers = ['Date', 'CPKC Rooms Used', 'Guaranteed Rooms', 'Unused Rooms', 'Goodwill Amount']
    for col, header in enumerate(headers):
        worksheet.write(4, col, header, header_format)
    
    # Data rows
    row = 5
    for day in report['daily_data']:
        worksheet.write(row, 0, day['date'], cell_format)
        worksheet.write(row, 1, day['cpkc_rooms_used'], cell_format)
        worksheet.write(row, 2, day['guaranteed_rooms'], cell_format)
        worksheet.write(row, 3, day['unused_guaranteed'], cell_format)
        worksheet.write(row, 4, day['goodwill_amount'], money_format)
        row += 1
    
    # Totals row
    worksheet.write(row, 0, 'TOTAL', total_format)
    worksheet.write(row, 1, sum(d['cpkc_rooms_used'] for d in report['daily_data']), total_format)
    worksheet.write(row, 2, '', total_format)
    worksheet.write(row, 3, report['total_unused_rooms'], total_format)
    worksheet.write(row, 4, report['total_goodwill_amount'], total_money_format)
    
    # Summary section
    row += 3
    worksheet.write(row, 0, 'SUMMARY', title_format)
    row += 1
    worksheet.write(row, 0, 'Total Days:', cell_format)
    worksheet.write(row, 1, report['total_days'], cell_format)
    row += 1
    worksheet.write(row, 0, 'Total Unused Rooms:', cell_format)
    worksheet.write(row, 1, report['total_unused_rooms'], cell_format)
    row += 1
    worksheet.write(row, 0, 'Total Goodwill Given:', cell_format)
    worksheet.write(row, 1, report['total_goodwill_amount'], money_format)
    row += 1
    worksheet.write(row, 0, 'Note:', subtitle_format)
    worksheet.merge_range(row, 1, row, 4, 'Goodwill = Unused guaranteed rooms that could have been billed but were not, for business relations.', subtitle_format)
    
    workbook.close()
    output.seek(0)
    
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=hodler_inn_guarantee_report.xlsx"}
    )

# Admin - Export Billing Report
@api_router.get("/admin/export-billing")
async def export_billing_report(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None)
):
    """Export billing report as Excel with optional date filtering"""
    query = {"is_checked_out": True}
    if start_date or end_date:
        date_filter = {}
        if start_date:
            date_filter["$gte"] = start_date
        if end_date:
            date_filter["$lte"] = end_date
        if date_filter:
            query["check_in_date"] = date_filter
    
    bookings = await db.bookings.find(query, {"_id": 0}).sort("check_in_date", 1).to_list(1000)
    
    # Batch fetch all guests to avoid N+1 query
    employee_numbers = [b['employee_number'] for b in bookings]
    guests_list = await db.guests.find({"employee_number": {"$in": employee_numbers}}, {"_id": 0}).to_list(1000)
    guests_dict = {g['employee_number']: g for g in guests_list}
    
    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output, {'in_memory': True})
    worksheet = workbook.add_worksheet("Billing Report")
    
    # Styles
    title_format = workbook.add_format({
        'bold': True,
        'font_size': 14,
        'align': 'center',
        'valign': 'vcenter'
    })
    subtitle_format = workbook.add_format({
        'font_size': 10,
        'align': 'center',
        'valign': 'vcenter'
    })
    header_format = workbook.add_format({
        'bold': True,
        'bg_color': '#fbbf24',
        'border': 1,
        'align': 'center',
        'valign': 'vcenter',
        'text_wrap': True
    })
    cell_format = workbook.add_format({
        'border': 1,
        'align': 'center',
        'valign': 'vcenter'
    })
    number_format = workbook.add_format({
        'border': 1,
        'align': 'center',
        'valign': 'vcenter',
        'num_format': '0.00'
    })
    total_format = workbook.add_format({
        'bold': True,
        'border': 1,
        'align': 'center',
        'valign': 'vcenter',
        'bg_color': '#e5e7eb'
    })
    
    # Company Header
    worksheet.merge_range('A1:K1', 'Hodler Inn - Billing Report', title_format)
    date_range_text = '820 Hwy 59 N Heavener, OK, 74937 | Phone: 918-653-7801'
    if start_date or end_date:
        date_range_text = f"Date Range: {start_date or 'Start'} to {end_date or 'Present'}"
    worksheet.merge_range('A2:K2', date_range_text, subtitle_format)
    worksheet.set_row(0, 25)
    worksheet.set_row(1, 18)
    
    # Column Headers
    headers = [
        "#", "Name", "Employee ID", "Room #",
        "Check-In Date", "Check-In Time", "Check-Out Date", "Check-Out Time", "Total Hours", "Nights Billed", "Signed"
    ]
    
    col_widths = [5, 18, 12, 8, 12, 10, 12, 10, 10, 10, 8]
    for col, (header, width) in enumerate(zip(headers, col_widths)):
        worksheet.write(3, col, header, header_format)
        worksheet.set_column(col, col, width)
    
    # Data rows
    row = 4
    row_num = 1
    total_nights = 0
    
    for booking in bookings:
        guest = guests_dict.get(booking['employee_number'])
        if guest:
            hours, nights = calculate_stay_duration(
                booking['check_in_date'],
                booking['check_in_time'],
                booking['check_out_date'],
                booking['check_out_time']
            )
            
            # Decrypt data
            decrypted_name = decrypt_data(guest.get('name_encrypted', guest.get('name', '')))
            # Signature is now in booking
            has_signature = bool(booking.get('signature_encrypted'))
            total_nights += nights if nights else 0
            
            worksheet.write(row, 0, row_num, cell_format)
            worksheet.write(row, 1, decrypted_name, cell_format)
            worksheet.write(row, 2, booking['employee_number'], cell_format)
            worksheet.write(row, 3, booking['room_number'], cell_format)
            worksheet.write(row, 4, booking['check_in_date'], cell_format)
            worksheet.write(row, 5, booking['check_in_time'], cell_format)
            worksheet.write(row, 6, booking['check_out_date'], cell_format)
            worksheet.write(row, 7, booking['check_out_time'], cell_format)
            worksheet.write(row, 8, hours if hours else 0, number_format)
            worksheet.write(row, 9, nights if nights else 0, cell_format)
            worksheet.write(row, 10, "Yes" if has_signature else "No", cell_format)
            row += 1
            row_num += 1
    
    # Total row
    worksheet.write(row, 0, "", total_format)
    worksheet.merge_range(row, 1, row, 8, "TOTAL NIGHTS BILLED", total_format)
    worksheet.write(row, 9, total_nights, total_format)
    worksheet.write(row, 10, "", total_format)
    
    workbook.close()
    output.seek(0)
    
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=hodler_inn_billing_report.xlsx"}
    )

# Admin - Export Sign-In Sheet as PNG
@api_router.get("/admin/export-png")
async def export_signin_png():
    bookings = await db.bookings.find({}, {"_id": 0}).to_list(1000)
    
    # Batch fetch all guests
    employee_numbers = [b['employee_number'] for b in bookings]
    guests_list = await db.guests.find({"employee_number": {"$in": employee_numbers}}, {"_id": 0}).to_list(1000)
    guests_dict = {g['employee_number']: g for g in guests_list}
    
    # Image dimensions
    row_height = 60
    header_height = 150
    sig_width = 80
    sig_height = 40
    col_widths = [40, 100, 180, 100, sig_width+20, sig_width+20, 100, 80, 100, 80, 80]
    total_width = sum(col_widths) + 20
    total_height = header_height + (len(bookings) + 1) * row_height + 50
    
    # Create image
    img = Image.new('RGB', (total_width, max(total_height, 400)), color='white')
    draw = ImageDraw.Draw(img)
    
    # Try to use a font, fallback to default
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
        font_bold = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 16)
        font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
    except:
        font = ImageFont.load_default()
        font_bold = font
        font_title = font
    
    # Header
    draw.rectangle([0, 0, total_width, 120], fill='#fbbf24')
    draw.text((total_width//2 - 80, 20), "Hodler Inn", fill='black', font=font_title)
    draw.text((total_width//2 - 140, 55), "820 Hwy 59 N Heavener, OK, 74937", fill='black', font=font)
    draw.text((total_width//2 - 80, 80), "Phone: 918-653-7801", fill='black', font=font)
    
    # Column headers
    headers = ["#", "Stay Type", "Name", "Emp ID", "Sign In", "Sign Out", "Date In", "Time In", "Date Out", "Time Out", "Room"]
    y = header_height
    x = 10
    draw.rectangle([0, y, total_width, y + row_height], fill='#f0f0f0')
    for i, header in enumerate(headers):
        draw.text((x + 5, y + 20), header, fill='black', font=font_bold)
        x += col_widths[i]
    
    # Data rows
    y += row_height
    for idx, booking in enumerate(bookings):
        guest = guests_dict.get(booking['employee_number'])
        if guest:
            decrypted_name = decrypt_data(guest.get('name_encrypted', guest.get('name', '')))
            # Signature is now in booking
            decrypted_sig = decrypt_data(booking.get('signature_encrypted', ''))
            has_sig = bool(decrypted_sig)
            is_checked_out = booking.get('is_checked_out', False)
            
            # Alternating row color
            if idx % 2 == 0:
                draw.rectangle([0, y, total_width, y + row_height], fill='#fafafa')
            
            x = 10
            # Row data
            data = [
                str(idx + 1),
                "Single Stay",
                decrypted_name[:18],
                booking['employee_number'],
                "",  # Signature In placeholder
                "",  # Signature Out placeholder
                booking['check_in_date'],
                booking['check_in_time'],
                booking.get('check_out_date', '-'),
                booking.get('check_out_time', '-'),
                booking['room_number']
            ]
            
            for i, val in enumerate(data):
                if i == 4 and has_sig and decrypted_sig:  # Signature In
                    try:
                        sig_data = decrypted_sig.split(',')[1] if ',' in decrypted_sig else decrypted_sig
                        sig_bytes = base64.b64decode(sig_data)
                        sig_img = Image.open(io.BytesIO(sig_bytes)).convert('RGBA')
                        sig_img = sig_img.resize((sig_width, sig_height))
                        img.paste(sig_img, (x + 5, y + 10), sig_img)
                    except:
                        draw.text((x + 5, y + 20), "Signed", fill='green', font=font)
                elif i == 5 and has_sig and is_checked_out and decrypted_sig:  # Signature Out
                    try:
                        sig_data = decrypted_sig.split(',')[1] if ',' in decrypted_sig else decrypted_sig
                        sig_bytes = base64.b64decode(sig_data)
                        sig_img = Image.open(io.BytesIO(sig_bytes)).convert('RGBA')
                        sig_img = sig_img.resize((sig_width, sig_height))
                        img.paste(sig_img, (x + 5, y + 10), sig_img)
                    except:
                        draw.text((x + 5, y + 20), "Signed", fill='green', font=font)
                else:
                    draw.text((x + 5, y + 20), str(val), fill='black', font=font)
                x += col_widths[i]
            
            y += row_height
    
    # Draw grid lines
    y = header_height
    for i in range(len(bookings) + 2):
        draw.line([(0, y), (total_width, y)], fill='#cccccc', width=1)
        y += row_height
    
    # Save to bytes
    output = io.BytesIO()
    img.save(output, format='PNG')
    output.seek(0)
    
    return StreamingResponse(
        output,
        media_type="image/png",
        headers={"Content-Disposition": "attachment; filename=hodler_inn_sign_in_sheet.png"}
    )

# Admin - Export Billing Report as PNG
@api_router.get("/admin/export-billing-png")
async def export_billing_png(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None)
):
    """Export billing report as PNG with optional date filtering"""
    query = {"is_checked_out": True}
    if start_date or end_date:
        date_filter = {}
        if start_date:
            date_filter["$gte"] = start_date
        if end_date:
            date_filter["$lte"] = end_date
        if date_filter:
            query["check_in_date"] = date_filter
    
    bookings = await db.bookings.find(query, {"_id": 0}).sort("check_in_date", 1).to_list(1000)
    
    # Batch fetch all guests
    employee_numbers = [b['employee_number'] for b in bookings]
    guests_list = await db.guests.find({"employee_number": {"$in": employee_numbers}}, {"_id": 0}).to_list(1000)
    guests_dict = {g['employee_number']: g for g in guests_list}
    
    # Image dimensions
    row_height = 60
    header_height = 150
    sig_width = 80
    sig_height = 40
    col_widths = [40, 180, 100, 80, 150, 150, 80, 80, sig_width+20]
    total_width = sum(col_widths) + 20
    total_height = header_height + (len(bookings) + 2) * row_height + 50
    
    # Create image
    img = Image.new('RGB', (total_width, max(total_height, 400)), color='white')
    draw = ImageDraw.Draw(img)
    
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
        font_bold = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 16)
        font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
    except:
        font = ImageFont.load_default()
        font_bold = font
        font_title = font
    
    # Header
    draw.rectangle([0, 0, total_width, 120], fill='#fbbf24')
    draw.text((total_width//2 - 120, 20), "Hodler Inn - Billing Report", fill='black', font=font_title)
    draw.text((total_width//2 - 140, 55), "820 Hwy 59 N Heavener, OK, 74937", fill='black', font=font)
    draw.text((total_width//2 - 80, 80), "Phone: 918-653-7801", fill='black', font=font)
    
    # Column headers
    headers = ["#", "Name", "Emp ID", "Room", "Check-In", "Check-Out", "Hours", "Nights", "Signature"]
    y = header_height
    x = 10
    draw.rectangle([0, y, total_width, y + row_height], fill='#f0f0f0')
    for i, header in enumerate(headers):
        draw.text((x + 5, y + 20), header, fill='black', font=font_bold)
        x += col_widths[i]
    
    # Data rows
    y += row_height
    total_nights = 0
    for idx, booking in enumerate(bookings):
        guest = guests_dict.get(booking['employee_number'])
        if guest:
            decrypted_name = decrypt_data(guest.get('name_encrypted', guest.get('name', '')))
            # Signature is now in booking
            decrypted_sig = decrypt_data(booking.get('signature_encrypted', ''))
            has_sig = bool(decrypted_sig)
            
            hours, nights = calculate_stay_duration(
                booking['check_in_date'],
                booking['check_in_time'],
                booking['check_out_date'],
                booking['check_out_time']
            )
            total_nights += nights if nights else 0
            
            if idx % 2 == 0:
                draw.rectangle([0, y, total_width, y + row_height], fill='#fafafa')
            
            x = 10
            data = [
                str(idx + 1),
                decrypted_name[:20],
                booking['employee_number'],
                booking['room_number'],
                f"{booking['check_in_date']} {booking['check_in_time']}",
                f"{booking['check_out_date']} {booking['check_out_time']}",
                f"{hours}h" if hours else "-",
                str(nights) if nights else "-",
                ""  # Signature placeholder
            ]
            
            for i, val in enumerate(data):
                if i == 8 and has_sig and decrypted_sig:  # Signature
                    try:
                        sig_data = decrypted_sig.split(',')[1] if ',' in decrypted_sig else decrypted_sig
                        sig_bytes = base64.b64decode(sig_data)
                        sig_img = Image.open(io.BytesIO(sig_bytes)).convert('RGBA')
                        sig_img = sig_img.resize((sig_width, sig_height))
                        img.paste(sig_img, (x + 5, y + 10), sig_img)
                    except:
                        draw.text((x + 5, y + 20), "Yes", fill='green', font=font)
                else:
                    draw.text((x + 5, y + 20), str(val), fill='black', font=font)
                x += col_widths[i]
            
            y += row_height
    
    # Total row
    draw.rectangle([0, y, total_width, y + row_height], fill='#e0e0e0')
    draw.text((200, y + 20), f"TOTAL NIGHTS BILLED: {total_nights}", fill='black', font=font_bold)
    
    output = io.BytesIO()
    img.save(output, format='PNG')
    output.seek(0)
    
    return StreamingResponse(
        output,
        media_type="image/png",
        headers={"Content-Disposition": "attachment; filename=hodler_inn_billing_report.png"}
    )

# ==================== Room Management ====================

@api_router.get("/rooms")
async def get_rooms_public():
    """Public endpoint for guest portal - returns room list for dropdown"""
    rooms = await db.rooms.find({}, {"_id": 0, "room_number": 1, "room_type": 1, "floor": 1}).to_list(1000)
    return rooms

@api_router.get("/voice-settings")
async def get_voice_settings():
    """Public endpoint for guest portal - returns voice settings"""
    settings = await db.settings.find_one({"id": "portal_settings"}, {"_id": 0})
    return {
        "voice_enabled": settings.get("voice_enabled", True) if settings else True,
        "voice_volume": settings.get("voice_volume", 1.0) if settings else 1.0,
        "voice_speed": settings.get("voice_speed", 0.85) if settings else 0.85
    }

# Pre-defined voice messages
VOICE_MESSAGES = {
    # Register welcome
    "register_welcome": "Welcome to Hodler Inn. If you are first time here, please register your employee number and name, then go to check in.",
    
    # Check-in welcome with full instructions (when employee is verified)
    "checkin_instructions_morning": "Good morning. Welcome back to Hodler Inn. Please enter room number, time, sign your name, and click Complete Check-In.",
    "checkin_instructions_afternoon": "Good afternoon. Welcome back to Hodler Inn. Please enter room number, time, sign your name, and click Complete Check-In.",
    "checkin_instructions_evening": "Good evening. Welcome back to Hodler Inn. Please enter room number, time, sign your name, and click Complete Check-In.",
    "checkin_instructions_night": "Good night. Welcome back to Hodler Inn. Please enter room number, time, sign your name, and click Complete Check-In.",
    
    # New employee instructions
    "new_employee_instructions": "Please enter your full name and company name, then click Continue to Check-In.",
    
    # Help phone message (after wrong company name attempts)
    "help_phone_message": "Please call Help Phone from outside office phone so we know someone need help.",
    
    # Check-in welcome (when clicking check-in button - short version)
    "checkin_welcome_morning": "Good morning. Welcome back to Hodler Inn.",
    "checkin_welcome_afternoon": "Good afternoon. Welcome back to Hodler Inn.",
    "checkin_welcome_evening": "Good evening. Welcome back to Hodler Inn.",
    "checkin_welcome_night": "Good night. Welcome back to Hodler Inn.",
    
    # Check-in complete (after completing check-in)
    "checkin_complete": "Have a good rest.",
    
    # Check-out messages
    "checkout_morning": "Good morning! Thank you for staying at Hodler Inn. Have a safe journey. Please drop your room key in the key drop box in the lounge.",
    "checkout_afternoon": "Good afternoon! Thank you for staying at Hodler Inn. Have a safe journey. Please drop your room key in the key drop box in the lounge.",
    "checkout_evening": "Good evening! Thank you for staying at Hodler Inn. Have a safe journey. Please drop your room key in the key drop box in the lounge.",
    "checkout_night": "Good night! Thank you for staying at Hodler Inn. Have a safe journey. Please drop your room key in the key drop box in the lounge.",
    
    # Check-out found with on duty time instruction
    "checkout_found": "Booking found. Please enter your on duty time and press Complete check out.",
    
    # Other reminders
    "signature_reminder": "Please sign your full name legibly. A simple line or X will not be accepted.",
    "room_reminder": "Please select the room number from key on desk. Print your name and room number on yellow card."
}

@api_router.get("/voice/{message_id}")
async def get_voice_message(message_id: str):
    """Get pre-generated voice message audio file"""
    audio_file = AUDIO_DIR / f"{message_id}.mp3"
    
    if audio_file.exists():
        return FileResponse(audio_file, media_type="audio/mpeg")
    
    # Generate the audio if it doesn't exist
    if message_id not in VOICE_MESSAGES:
        raise HTTPException(status_code=404, detail="Voice message not found")
    
    try:
        from emergentintegrations.llm.openai import OpenAITextToSpeech
        
        tts = OpenAITextToSpeech(api_key=os.getenv("EMERGENT_LLM_KEY"))
        audio_bytes = await tts.generate_speech(
            text=VOICE_MESSAGES[message_id],
            model="tts-1",
            voice="nova",  # Friendly, upbeat voice
            speed=0.95
        )
        
        # Save to file for caching
        with open(audio_file, "wb") as f:
            f.write(audio_bytes)
        
        return FileResponse(audio_file, media_type="audio/mpeg")
        
    except Exception as e:
        logging.error(f"Failed to generate voice: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate voice message")

@api_router.post("/generate-all-voices")
async def generate_all_voice_messages():
    """Pre-generate all voice messages (admin only)"""
    try:
        from emergentintegrations.llm.openai import OpenAITextToSpeech
        
        tts = OpenAITextToSpeech(api_key=os.getenv("EMERGENT_LLM_KEY"))
        generated = []
        
        for message_id, text in VOICE_MESSAGES.items():
            audio_file = AUDIO_DIR / f"{message_id}.mp3"
            if not audio_file.exists():
                audio_bytes = await tts.generate_speech(
                    text=text,
                    model="tts-1",
                    voice="nova",
                    speed=0.95
                )
                with open(audio_file, "wb") as f:
                    f.write(audio_bytes)
                generated.append(message_id)
        
        return {"message": "Voice messages generated", "generated": generated}
        
    except Exception as e:
        logging.error(f"Failed to generate voices: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def format_name_for_speech(name: str) -> str:
    """
    Convert portal-style names to natural speech format.
    Examples:
    - "BAKER,(AUSTIN) E" -> "Austin Baker"
    - "SMITH,JOHN BHW" -> "John Smith"
    - "DOE,(JANE)" -> "Jane Doe"
    - "JOHNSON, MICHAEL E" -> "Michael Johnson"
    """
    if not name:
        return "Guest"
    
    name = name.strip()
    
    # Remove common suffixes like E, BHW, etc. at the end
    import re
    # Remove trailing single letters or abbreviations (E, BHW, JR, SR, etc.)
    name = re.sub(r'\s+[A-Z]{1,4}$', '', name)
    
    # Handle format: "LASTNAME,(FIRSTNAME)" or "LASTNAME, (FIRSTNAME)"
    match = re.match(r'^([A-Z]+)[,\s]+\(([A-Z]+)\)$', name, re.IGNORECASE)
    if match:
        last_name = match.group(1).strip()
        first_name = match.group(2).strip()
        formatted = f"{first_name.title()} {last_name.title()}"
    elif ',' in name:
        # Handle format: "LASTNAME,FIRSTNAME" or "LASTNAME, FIRSTNAME"
        parts = name.split(',', 1)
        last_name = parts[0].strip()
        first_name = parts[1].strip() if len(parts) > 1 else ""
        # Remove parentheses if present
        first_name = re.sub(r'[()]', '', first_name).strip()
        if first_name and last_name:
            formatted = f"{first_name.title()} {last_name.title()}"
        elif last_name:
            formatted = last_name.title()
        else:
            formatted = name.title()
    else:
        # If no comma, assume it's already in normal format
        formatted = name.title()
    
    # Fix common TTS pronunciation issues
    formatted = fix_pronunciation(formatted)
    
    return formatted

def fix_pronunciation(name: str) -> str:
    """
    Fix common TTS mispronunciations by replacing names with phonetic versions.
    """
    # Dictionary of names that TTS commonly mispronounces
    # Key: lowercase name, Value: phonetically-friendly spelling
    pronunciation_fixes = {
        # First names
        'brian': 'Bryan',      # Prevents "brain" pronunciation
        'Brain': 'Bryan',      # In case it's already capitalized wrong
        'gerald': 'Jerald',    # Prevents "gayr-ad" pronunciation, should be "jer-ald"
        'gerard': 'Jerard',    # Similar issue
        'shawn': 'Shaun',      # Some TTS struggle with Shawn
        'sean': 'Shaun',       # Irish spelling
        'siobhan': 'Shivawn',  # Irish name
        'niamh': 'Neev',       # Irish name
        'caoimhe': 'Keeva',    # Irish name
        'saoirse': 'Seersha',  # Irish name
        'deidre': 'Deedra',    # Can be mispronounced
        'leigh': 'Lee',        # Silent gh
        'geoff': 'Jeff',       # Silent o
        'geoffrey': 'Jeffrey', # Silent o
        'george': 'Jorj',      # Hard G issue
        'jorge': 'Horhay',     # Spanish pronunciation
        'jose': 'Hosay',       # Spanish pronunciation
        'jesus': 'Heysoos',    # Spanish pronunciation
        'nguyen': 'Win',       # Vietnamese name
        'phoebe': 'Feebee',    # Greek spelling
        'chloe': 'Klowee',     # Greek spelling
        'zoe': 'Zowee',        # Greek spelling
        'megan': 'Meggan',     # Can be mispronounced as "meegan"
        'colin': 'Collin',     # Can be mispronounced
        'stephen': 'Steven',   # ph = v sound
        'ralph': 'Ralf',       # Silent l for some
        # Add more as needed
    }
    
    words = name.split()
    fixed_words = []
    
    for word in words:
        word_lower = word.lower()
        if word_lower in pronunciation_fixes:
            # Preserve the original capitalization style
            fixed = pronunciation_fixes[word_lower]
            if word.isupper():
                fixed = fixed.upper()
            elif word[0].isupper():
                fixed = fixed.capitalize()
            fixed_words.append(fixed)
        else:
            fixed_words.append(word)
    
    return ' '.join(fixed_words)

@api_router.get("/voice-dynamic/{message_type}/{name}")
async def get_dynamic_voice(message_type: str, name: str, greeting: str = None):
    """Generate voice message with dynamic name (for Fully Kiosk compatibility)"""
    try:
        from emergentintegrations.llm.openai import OpenAITextToSpeech
        
        # Format name for natural speech (convert "BAKER,(AUSTIN) E" to "Austin Baker")
        spoken_name = format_name_for_speech(name)
        
        # Use greeting from frontend (user's local time) or fallback to server time
        if not greeting:
            hour = datetime.now().hour
            if 5 <= hour < 12:
                greeting = "Good morning"
            elif 12 <= hour < 17:
                greeting = "Good afternoon"
            elif 17 <= hour < 21:
                greeting = "Good evening"
            else:
                greeting = "Good night"
        
        # Build message based on type
        if message_type == "checkin":
            text = f"{greeting}, {spoken_name}. Welcome back to Hodler Inn. Please enter room number, time, sign your name, and click Complete Check-In."
        elif message_type == "checkin_new":
            text = f"{greeting}, {spoken_name}. Welcome to Hodler Inn. Please enter room number, time, sign your name, and click Complete Check-In."
        elif message_type == "checkout_found":
            text = f"Booking found for {spoken_name}. Please enter your on duty time and press Complete check out."
        else:
            raise HTTPException(status_code=400, detail="Invalid message type")
        
        tts = OpenAITextToSpeech(api_key=os.getenv("EMERGENT_LLM_KEY"))
        audio_bytes = await tts.generate_speech(
            text=text,
            model="tts-1",
            voice="nova",
            speed=1.0  # Slightly faster for quicker response
        )
        
        # Return audio directly (don't cache - names are dynamic)
        return Response(content=audio_bytes, media_type="audio/mpeg")
        
    except Exception as e:
        logging.error(f"Failed to generate dynamic voice: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate voice")

@api_router.get("/admin/rooms")
async def get_all_rooms():
    rooms = await db.rooms.find({}, {"_id": 0}).to_list(1000)
    
    # Update room status based on active bookings
    active_bookings = await db.bookings.find({"is_checked_out": False}, {"_id": 0}).to_list(1000)
    occupied_rooms = {b['room_number'] for b in active_bookings}
    
    for room in rooms:
        if room['room_number'] in occupied_rooms:
            room['status'] = 'occupied'
        elif room.get('status') != 'maintenance':
            room['status'] = 'available'
    
    return rooms

@api_router.post("/admin/rooms")
async def create_room(input: RoomCreate):
    # Check if room already exists
    existing = await db.rooms.find_one({"room_number": input.room_number}, {"_id": 0})
    if existing:
        raise HTTPException(status_code=400, detail="Room already exists")
    
    room = Room(**input.model_dump())
    doc = room.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    
    await db.rooms.insert_one(doc)
    # Remove _id before returning (MongoDB adds it during insert)
    doc.pop('_id', None)
    return {"message": "Room created successfully", "room": doc}

@api_router.put("/admin/rooms/{room_id}")
async def update_room(room_id: str, input: RoomUpdate):
    room = await db.rooms.find_one({"id": room_id}, {"_id": 0})
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    
    update_data = {k: v for k, v in input.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No data to update")
    
    await db.rooms.update_one({"id": room_id}, {"$set": update_data})
    return {"message": "Room updated successfully"}

@api_router.delete("/admin/rooms/{room_id}")
async def delete_room(room_id: str):
    room = await db.rooms.find_one({"id": room_id}, {"_id": 0})
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    
    # Check if room has active booking
    active_booking = await db.bookings.find_one({
        "room_number": room['room_number'],
        "is_checked_out": False
    }, {"_id": 0})
    if active_booking:
        raise HTTPException(status_code=400, detail="Cannot delete room with active booking")
    
    await db.rooms.delete_one({"id": room_id})
    return {"message": "Room deleted successfully"}

@api_router.post("/admin/rooms/{room_number}/mark-dirty")
async def mark_room_dirty(room_number: str):
    """Mark a room as dirty (needs cleaning)"""
    room = await db.rooms.find_one({"room_number": room_number}, {"_id": 0})
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    
    await db.rooms.update_one({"room_number": room_number}, {"$set": {"status": "dirty"}})
    return {"message": f"Room {room_number} marked as dirty"}

@api_router.post("/admin/rooms/{room_number}/mark-clean")
async def mark_room_clean(room_number: str):
    """Mark a room as clean (available)"""
    room = await db.rooms.find_one({"room_number": room_number}, {"_id": 0})
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    
    await db.rooms.update_one({"room_number": room_number}, {"$set": {"status": "available"}})
    return {"message": f"Room {room_number} marked as clean/available"}

# Block room for non-railroad guest (Other Guest)
class BlockRoomInput(BaseModel):
    room_number: str
    guest_name: Optional[str] = "Other Guest"
    notes: Optional[str] = ""

@api_router.post("/admin/rooms/block")
async def block_room_other_guest(input: BlockRoomInput):
    """Block a room for non-railroad guest. Counts toward occupancy but not billed to railroad."""
    # Check if room exists
    room = await db.rooms.find_one({"room_number": input.room_number}, {"_id": 0})
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    
    # Check if room is already occupied
    active_booking = await db.bookings.find_one({
        "room_number": input.room_number,
        "is_checked_out": False
    }, {"_id": 0})
    if active_booking:
        raise HTTPException(status_code=400, detail="Room is already occupied")
    
    # Check if room is already blocked
    existing_block = await db.blocked_rooms.find_one({
        "room_number": input.room_number,
        "is_active": True
    }, {"_id": 0})
    if existing_block:
        raise HTTPException(status_code=400, detail="Room is already blocked")
    
    # Create blocked room record
    block_doc = {
        "id": str(uuid.uuid4()),
        "room_number": input.room_number,
        "guest_name": input.guest_name,
        "notes": input.notes,
        "is_active": True,
        "blocked_at": datetime.now(timezone.utc).isoformat()
    }
    await db.blocked_rooms.insert_one(block_doc)
    
    # Check if we're now at 100% capacity
    await check_and_send_sold_out_notification()
    
    # Check if we're low on rooms (4 or fewer) and send heads-up notice
    await check_and_send_heads_up_notification()
    
    return {"message": f"Room {input.room_number} blocked for other guest", "block": block_doc}

@api_router.post("/admin/rooms/unblock/{room_number}")
async def unblock_room(room_number: str):
    """Release a blocked room (other guest checked out)"""
    block = await db.blocked_rooms.find_one({
        "room_number": room_number,
        "is_active": True
    }, {"_id": 0})
    
    if not block:
        raise HTTPException(status_code=404, detail="No active block found for this room")
    
    await db.blocked_rooms.update_one(
        {"room_number": room_number, "is_active": True},
        {"$set": {"is_active": False, "unblocked_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    # Check if rooms are now available after being sold out
    await send_room_available_notification()
    
    return {"message": f"Room {room_number} unblocked"}

@api_router.get("/admin/rooms/blocked")
async def get_blocked_rooms():
    """Get all currently blocked rooms (other guests)"""
    blocked = await db.blocked_rooms.find({"is_active": True}, {"_id": 0}).to_list(100)
    return blocked

# ==================== Employee Management ====================

@api_router.get("/admin/employees")
async def get_employees():
    """Get all pre-registered employees"""
    employees = await db.employees.find({}, {"_id": 0}).sort("name", 1).to_list(1000)
    return employees

@api_router.post("/admin/employees")
async def create_employee(input: EmployeeCreate):
    """Add a new employee to the allowed list"""
    # Check if employee number already exists
    existing = await db.employees.find_one({"employee_number": input.employee_number}, {"_id": 0})
    if existing:
        raise HTTPException(status_code=400, detail="Employee number already exists")
    
    employee = Employee(
        employee_number=input.employee_number,
        name=input.name
    )
    doc = employee.model_dump()
    await db.employees.insert_one(doc)
    doc.pop('_id', None)
    return {"message": "Employee added successfully", "employee": doc}

@api_router.post("/admin/employees/bulk")
async def bulk_import_employees(employees: List[EmployeeCreate]):
    """Bulk import employees"""
    added = 0
    skipped = 0
    
    for emp in employees:
        existing = await db.employees.find_one({"employee_number": emp.employee_number}, {"_id": 0})
        if existing:
            skipped += 1
            continue
        
        employee = Employee(
            employee_number=emp.employee_number,
            name=emp.name
        )
        await db.employees.insert_one(employee.model_dump())
        added += 1
    
    return {"message": f"Imported {added} employees, skipped {skipped} duplicates"}

@api_router.put("/admin/employees/{employee_id}")
async def update_employee(employee_id: str, input: EmployeeUpdate):
    """Update an employee"""
    # Try to find by id first, then by employee_number (for legacy records)
    employee = await db.employees.find_one({"id": employee_id}, {"_id": 0})
    query_field = "id"
    
    if not employee:
        # Fallback: try finding by employee_number
        employee = await db.employees.find_one({"employee_number": employee_id}, {"_id": 0})
        query_field = "employee_number"
    
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    update_data = {k: v for k, v in input.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No data to update")
    
    # If updating employee_number to a DIFFERENT value, check for duplicates
    if "employee_number" in update_data and update_data["employee_number"] != employee.get("employee_number"):
        existing = await db.employees.find_one({
            "employee_number": update_data["employee_number"]
        }, {"_id": 0})
        if existing:
            raise HTTPException(status_code=400, detail="Employee number already exists")
    
    # Get the current employee_number for syncing to guests collection
    current_employee_number = employee.get("employee_number")
    
    # Update employees collection
    await db.employees.update_one({query_field: employee_id}, {"$set": update_data})
    
    # Also sync updated name to guests collection (so Guest Portal shows updated name)
    if "name" in update_data:
        guest_update = {
            "name": update_data["name"],
            "name_encrypted": encrypt_data(update_data["name"])
        }
        # Update ALL guest records with this employee_number (not just one)
        await db.guests.update_many(
            {"employee_number": current_employee_number},
            {"$set": guest_update}
        )
    
    # If employee_number changed, also update in guests collection
    if "employee_number" in update_data and update_data["employee_number"] != current_employee_number:
        await db.guests.update_one(
            {"employee_number": current_employee_number},
            {"$set": {"employee_number": update_data["employee_number"]}}
        )
    
    return {"message": "Employee updated successfully"}

@api_router.delete("/admin/employees/{employee_id}")
async def delete_employee(employee_id: str):
    """Delete an employee"""
    # Try to find by id first, then by employee_number (for legacy records)
    employee = await db.employees.find_one({"id": employee_id}, {"_id": 0})
    query_field = "id"
    
    if not employee:
        # Fallback: try finding by employee_number
        employee = await db.employees.find_one({"employee_number": employee_id}, {"_id": 0})
        query_field = "employee_number"
    
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    await db.employees.delete_one({query_field: employee_id})
    return {"message": "Employee deleted successfully"}


@api_router.post("/admin/employees/sync-names-to-guests")
async def sync_employee_names_to_guests():
    """
    Bulk sync all employee names to the guests collection.
    Use this after updating employee names to match portal format.
    This makes the sync agent work with current in-house guests immediately.
    """
    # Get all employees
    employees = await db.employees.find({}, {"_id": 0}).to_list(1000)
    
    updated_count = 0
    for emp in employees:
        employee_number = emp.get("employee_number")
        employee_name = emp.get("name")
        
        if not employee_number or not employee_name:
            continue
        
        # Update ALL guest records with this employee number (not just one)
        result = await db.guests.update_many(
            {"employee_number": employee_number},
            {"$set": {
                "name": employee_name,
                "name_encrypted": encrypt_data(employee_name)
            }}
        )
        
        if result.modified_count > 0:
            updated_count += result.modified_count
    
    return {
        "message": f"Synced {updated_count} guest records with updated employee names",
        "updated_count": updated_count,
        "total_employees": len(employees)
    }


@api_router.get("/employees/verify/{employee_number}")
async def verify_employee_exists(employee_number: str):
    """Check if an employee number is in the allowed list (public endpoint for check-in)"""
    employee = await db.employees.find_one({"employee_number": employee_number, "is_active": True}, {"_id": 0})
    if not employee:
        raise HTTPException(status_code=404, detail="Employee ID not found in system. Please contact admin.")
    return {"valid": True, "name": employee["name"], "employee_number": employee["employee_number"]}

# ==================== Portal Settings ====================

@api_router.get("/admin/settings")
async def get_portal_settings():
    """Get portal settings (password is masked)"""
    settings = await db.settings.find_one({"id": "portal_settings"}, {"_id": 0})
    if not settings:
        return {
            "id": "portal_settings",
            "api_global_username": "",
            "api_global_password_set": False,
            "alert_email": "",
            "auto_sync_enabled": False,
            "auto_sync_start_date": None,
            "voice_enabled": True,
            "voice_volume": 1.0,
            "voice_speed": 0.85,
            "telegram_chat_id": TELEGRAM_CHAT_ID or "",
            "public_api_key": "",
            "public_api_key_set": False,
            "nightly_rate": 75.0,
            "email_reports_enabled": False,
            "email_smtp_host": "smtp.zoho.com",
            "email_smtp_port": 587,
            "email_sender": "",
            "email_password_set": False,
            "email_recipient": "",
            "email_report_time": "00:00"
        }
    
    # Mask password - only indicate if it's set
    return {
        "id": settings.get("id"),
        "api_global_username": settings.get("api_global_username", ""),
        "api_global_password_set": bool(settings.get("api_global_password_encrypted")),
        "alert_email": settings.get("alert_email", ""),
        "auto_sync_enabled": settings.get("auto_sync_enabled", False),
        "auto_sync_start_date": settings.get("auto_sync_start_date"),
        "voice_enabled": settings.get("voice_enabled", True),
        "voice_volume": settings.get("voice_volume", 1.0),
        "voice_speed": settings.get("voice_speed", 0.85),
        "telegram_chat_id": settings.get("telegram_chat_id", "") or TELEGRAM_CHAT_ID or "",
        "public_api_key": settings.get("public_api_key", ""),
        "public_api_key_set": bool(settings.get("public_api_key")),
        "nightly_rate": settings.get("nightly_rate", 75.0),
        "email_reports_enabled": settings.get("email_reports_enabled", False),
        "email_smtp_host": settings.get("email_smtp_host", "smtp.zoho.com"),
        "email_smtp_port": settings.get("email_smtp_port", 587),
        "email_sender": settings.get("email_sender", ""),
        "email_password_set": bool(settings.get("email_password_encrypted")),
        "email_recipient": settings.get("email_recipient", ""),
        "email_report_time": settings.get("email_report_time", "00:00")
    }

@api_router.post("/admin/settings")
async def update_portal_settings(input: PortalSettingsUpdate):
    """Update portal settings"""
    existing = await db.settings.find_one({"id": "portal_settings"}, {"_id": 0})
    
    update_data = {}
    
    if input.api_global_username is not None:
        update_data["api_global_username"] = input.api_global_username
    
    if input.api_global_password is not None and input.api_global_password != "":
        # Encrypt password before storing
        encrypted_password = encrypt_data(input.api_global_password)
        update_data["api_global_password_encrypted"] = encrypted_password
    
    if input.alert_email is not None:
        update_data["alert_email"] = input.alert_email
    
    if input.auto_sync_enabled is not None:
        update_data["auto_sync_enabled"] = input.auto_sync_enabled
    
    if input.auto_sync_start_date is not None:
        update_data["auto_sync_start_date"] = input.auto_sync_start_date
    
    if input.voice_enabled is not None:
        update_data["voice_enabled"] = input.voice_enabled
    
    if input.voice_volume is not None:
        update_data["voice_volume"] = max(0.0, min(1.0, input.voice_volume))  # Clamp 0-1
    
    if input.voice_speed is not None:
        update_data["voice_speed"] = max(0.5, min(1.5, input.voice_speed))  # Clamp 0.5-1.5
    
    if input.telegram_chat_id is not None:
        update_data["telegram_chat_id"] = input.telegram_chat_id
    
    if input.public_api_key is not None:
        update_data["public_api_key"] = input.public_api_key
    
    if input.nightly_rate is not None:
        update_data["nightly_rate"] = max(0.0, input.nightly_rate)
    
    # Email report settings
    if input.email_reports_enabled is not None:
        update_data["email_reports_enabled"] = input.email_reports_enabled
    
    if input.email_smtp_host is not None:
        update_data["email_smtp_host"] = input.email_smtp_host
    
    if input.email_smtp_port is not None:
        update_data["email_smtp_port"] = input.email_smtp_port
    
    if input.email_sender is not None:
        update_data["email_sender"] = input.email_sender
    
    if input.email_password is not None and input.email_password != "":
        # Encrypt password before storing
        encrypted_password = encrypt_data(input.email_password)
        update_data["email_password_encrypted"] = encrypted_password
    
    if input.email_recipient is not None:
        update_data["email_recipient"] = input.email_recipient
    
    if input.email_report_time is not None:
        update_data["email_report_time"] = input.email_report_time
    
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    if existing:
        await db.settings.update_one({"id": "portal_settings"}, {"$set": update_data})
    else:
        update_data["id"] = "portal_settings"
        await db.settings.insert_one(update_data)
    
    # Update auto-sync schedule if the setting changed
    if input.auto_sync_enabled is not None:
        # Get the start date from input or existing settings
        start_date = input.auto_sync_start_date
        if start_date is None and existing:
            start_date = existing.get("auto_sync_start_date")
        update_auto_sync_schedule(input.auto_sync_enabled, start_date)
    
    return {"message": "Settings updated successfully"}

@api_router.post("/admin/settings/test-connection")
async def test_portal_connection():
    """Test connection to API Global portal"""
    settings = await db.settings.find_one({"id": "portal_settings"}, {"_id": 0})
    
    if not settings or not settings.get("api_global_username") or not settings.get("api_global_password_encrypted"):
        raise HTTPException(status_code=400, detail="Portal credentials not configured")
    
    try:
        from sync_agent import test_connection
        username = settings.get("api_global_username")
        password = decrypt_data(settings.get("api_global_password_encrypted"))
        result = await test_connection(username, password)
        return result
    except Exception as e:
        return {"success": False, "message": f"Test failed: {str(e)}"}

@api_router.post("/admin/settings/test-email")
async def test_email_connection():
    """Test email SMTP connection and send test email"""
    settings = await db.settings.find_one({"id": "portal_settings"}, {"_id": 0})
    
    if not settings or not settings.get("email_sender") or not settings.get("email_password_encrypted"):
        raise HTTPException(status_code=400, detail="Email credentials not configured")
    
    try:
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        
        smtp_host = settings.get("email_smtp_host", "smtp.zoho.com")
        smtp_port = settings.get("email_smtp_port", 587)
        sender = settings.get("email_sender")
        password = decrypt_data(settings.get("email_password_encrypted"))
        recipient = settings.get("email_recipient", sender)
        
        # Create test email
        msg = MIMEMultipart()
        msg['From'] = sender
        msg['To'] = recipient
        msg['Subject'] = "Hodler Inn - Email Test"
        body = "This is a test email from Hodler Inn. If you receive this, your email settings are configured correctly!"
        msg.attach(MIMEText(body, 'plain'))
        
        # Send email
        server = smtplib.SMTP(smtp_host, smtp_port)
        server.starttls()
        server.login(sender, password)
        server.send_message(msg)
        server.quit()
        
        return {"success": True, "message": f"Test email sent to {recipient}"}
    except Exception as e:
        logging.error(f"Email test failed: {e}")
        return {"success": False, "message": f"Email test failed: {str(e)}"}

@api_router.post("/admin/settings/test-telegram")
async def test_telegram_connection():
    """Test Telegram notification by sending a test message"""
    chat_id = await get_telegram_chat_id()
    
    if not TELEGRAM_BOT_TOKEN:
        return {"success": False, "message": "Telegram bot token not configured", "chat_id_used": None}
    
    if not chat_id:
        return {"success": False, "message": "Telegram chat ID not configured", "chat_id_used": None}
    
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json={
                "chat_id": chat_id,
                "text": "🔔 <b>Test Notification</b>\n\nThis is a test from Hodler Inn Admin Panel.\nIf you see this, Telegram notifications are working!",
                "parse_mode": "HTML"
            })
            
            result = response.json()
            
            if result.get("ok"):
                return {
                    "success": True, 
                    "message": f"Test notification sent to chat ID: {chat_id}",
                    "chat_id_used": chat_id
                }
            else:
                return {
                    "success": False, 
                    "message": f"Telegram API error: {result.get('description', 'Unknown error')}",
                    "chat_id_used": chat_id
                }
    except Exception as e:
        logging.error(f"Telegram test failed: {e}")
        return {"success": False, "message": f"Telegram test failed: {str(e)}", "chat_id_used": chat_id}


@api_router.post("/admin/settings/test-room-available")
async def test_room_available_notification():
    """Test Room Available email notification - simulates the notification that would be sent after a checkout"""
    room_info = await get_room_availability_details()
    
    today = datetime.now().strftime("%Y-%m-%d")
    subject = f"[TEST] Hodler Inn - Rooms Now Available ({today})"
    
    body = f"""Hello,

THIS IS A TEST NOTIFICATION from Hodler Inn Admin Panel.

GOOD NEWS! Rooms are now available after being at 100% capacity.

ROOM AVAILABILITY:
- Total Rooms Available: {room_info['available_rooms']}
- Clean & Ready: {room_info['clean_available']}
- Being Cleaned: {room_info['dirty_rooms']}

CURRENT OCCUPANCY:
- Railroad Crew In-House: {room_info['occupied_by_railroad']}
- Other Guests: {room_info['blocked_rooms']}
- Total Occupied: {room_info['total_occupied']}/{room_info['total_rooms']}

Thank you,
Hodler Inn

---
This is a TEST message. Please ignore.
"""
    
    result = await send_email_notification(subject, body)
    if result:
        return {"success": True, "message": "Room Available test email sent!", "room_info": room_info}
    else:
        return {"success": False, "message": "Failed to send test email. Check email settings."}


@api_router.post("/admin/settings/test-heads-up")
async def test_heads_up_notification():
    """Test Heads-Up email notification - simulates the low availability warning"""
    room_info = await get_room_availability_details()
    
    today = datetime.now().strftime("%Y-%m-%d")
    subject = f"[TEST] Hodler Inn - HEADS UP: Low Room Availability ({today})"
    
    body = f"""Hello,

THIS IS A TEST NOTIFICATION from Hodler Inn Admin Panel.

We have limited room availability. Please prepare for incoming crews.

ROOM STATUS:
- Rooms Available: {room_info['available_rooms']}
- Clean & Ready: {room_info['clean_available']}
- Being Cleaned: {room_info['dirty_rooms']}

CURRENT OCCUPANCY:
- Railroad Crew In-House: {room_info['occupied_by_railroad']}
- Other Guests (Blocked Rooms): {room_info['blocked_rooms']}
- Total Occupied: {room_info['total_occupied']}/{room_info['total_rooms']}

Please plan accordingly for any additional crew arrivals.

Thank you,
Hodler Inn

---
This is a TEST message. Please ignore.
"""
    
    result = await send_email_notification(subject, body)
    if result:
        return {"success": True, "message": "Heads-Up test email sent!", "room_info": room_info}
    else:
        return {"success": False, "message": "Failed to send test email. Check email settings."}


@api_router.get("/admin/notification-state")
async def get_notification_status():
    """Get current notification state (for debugging)"""
    state = await get_notification_state()
    room_info = await get_room_availability_details()
    return {
        "notification_state": state,
        "current_room_info": room_info
    }


@api_router.post("/admin/notification-state/reset")
async def reset_notification_state():
    """Reset notification state (for testing)"""
    await db.notification_state.update_one(
        {"id": "email_notifications"},
        {"$set": {"sold_out_date": None, "heads_up_date": None, "was_sold_out": False}},
        upsert=True
    )
    return {"message": "Notification state reset"}


@api_router.post("/admin/settings/test-zoho")
async def test_zoho_connection():
    """Test Zoho WorkDrive connection"""
    access_token = await get_zoho_access_token()
    if not access_token:
        return {"success": False, "message": "Failed to get Zoho access token. Check credentials."}
    
    if not ZOHO_FOLDER_ID:
        return {"success": False, "message": "Zoho folder ID not configured"}
    
    return {"success": True, "message": f"Zoho WorkDrive connected! Folder: {ZOHO_FOLDER_ID}"}

@api_router.post("/admin/upload-to-zoho")
async def upload_daily_reports_to_zoho(target_date: str = None):
    """Upload reports to Zoho Drive. If target_date provided, uploads for that date. Otherwise uploads today's."""
    report_date = target_date if target_date else datetime.now().strftime("%Y-%m-%d")
    results = []
    
    # Generate and upload sign-in sheet PDF with signatures
    try:
        # Get bookings for the specified date
        bookings = await db.bookings.find({
            "check_in_date": report_date
        }, {"_id": 0}).to_list(100)
        
        if bookings:
            # Get guests for name lookup
            employee_numbers = [b['employee_number'] for b in bookings]
            guests_list = await db.guests.find({"employee_number": {"$in": employee_numbers}}, {"_id": 0}).to_list(100)
            guests_dict = {g['employee_number']: g for g in guests_list}
            
            # Generate PDF with signatures
            output = io.BytesIO()
            doc = SimpleDocTemplate(output, pagesize=landscape(letter), 
                                   rightMargin=30, leftMargin=30, 
                                   topMargin=30, bottomMargin=30)
            elements = []
            styles = getSampleStyleSheet()
            
            # Title
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=18,
                alignment=TA_CENTER,
                spaceAfter=10
            )
            subtitle_style = ParagraphStyle(
                'Subtitle',
                parent=styles['Normal'],
                fontSize=10,
                alignment=TA_CENTER,
                textColor=colors.gray
            )
            elements.append(Paragraph(f"HODLER INN - SIGN IN SHEET", title_style))
            elements.append(Paragraph("820 Hwy 59 N Heavener, OK, 74937 | Phone: 918-653-7801", subtitle_style))
            elements.append(Paragraph(f"Date: {report_date}", styles['Normal']))
            elements.append(Spacer(1, 20))
            
            # Table data with signature images
            data = [["#", "Employee ID", "Name", "Room", "Check-In Date", "Check-In Time", "Check-Out Date", "Check-Out Time", "Signature"]]
            for i, booking in enumerate(bookings, 1):
                guest = guests_dict.get(booking['employee_number'])
                name = decrypt_data(guest.get('name_encrypted', guest.get('name', 'Unknown'))) if guest else "Unknown"
                
                # Get signature image
                sig_element = '-'
                if booking.get('signature_encrypted'):
                    try:
                        sig_data = decrypt_data(booking['signature_encrypted'])
                        if sig_data and sig_data.startswith('data:image'):
                            base64_data = sig_data.split(',')[1] if ',' in sig_data else sig_data
                            sig_bytes = base64.b64decode(base64_data)
                            sig_buffer = io.BytesIO(sig_bytes)
                            sig_img = RLImage(sig_buffer, width=60, height=25)
                            sig_element = sig_img
                    except Exception as e:
                        logging.warning(f"Could not decode signature: {e}")
                        sig_element = 'Signed'
                
                data.append([
                    str(i),
                    booking.get('employee_number', ''),
                    name[:20],
                    booking.get('room_number', ''),
                    booking.get('check_in_date', '-'),
                    booking.get('check_in_time', '-'),
                    booking.get('check_out_date', '-') if booking.get('is_checked_out') else '-',
                    booking.get('check_out_time', '-') if booking.get('is_checked_out') else '-',
                    sig_element
                ])
            
            table = Table(data, colWidths=[0.3*inch, 0.8*inch, 1.5*inch, 0.5*inch, 0.8*inch, 0.6*inch, 0.8*inch, 0.6*inch, 1.0*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#fbbf24')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('TOPPADDING', (0, 1), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ]))
            elements.append(table)
            
            # Add summary
            elements.append(Spacer(1, 20))
            checked_out = sum(1 for b in bookings if b.get('is_checked_out'))
            in_house = len(bookings) - checked_out
            summary_style = ParagraphStyle('Summary', parent=styles['Normal'], fontSize=10)
            elements.append(Paragraph(f"Total Check-Ins: {len(bookings)} | In-House: {in_house} | Checked Out: {checked_out}", summary_style))
            
            doc.build(elements)
            pdf_bytes = output.getvalue()
            
            # Upload to Zoho
            result = await upload_to_zoho_drive(pdf_bytes, f"SignInSheet_{report_date}.pdf")
            results.append({"file": f"Sign-In Sheet ({report_date})", "result": result})
        else:
            results.append({"file": f"Sign-In Sheet ({report_date})", "result": {"success": True, "message": f"No bookings for {report_date}"}})
            
    except Exception as e:
        logging.error(f"Failed to generate/upload sign-in sheet: {e}")
        results.append({"file": f"Sign-In Sheet ({report_date})", "result": {"success": False, "error": str(e)}})
    
    return {"results": results, "date": report_date}

# Sync status storage (in-memory for now)
sync_status = {
    "running": False,
    "last_run": None,
    "last_results": None,
    "progress": ""
}

@api_router.get("/admin/sync/status")
async def get_sync_status():
    """Get current sync status including next scheduled run"""
    # Get next scheduled run time if auto-sync is enabled
    next_run = None
    auto_sync_enabled = False
    
    try:
        job = scheduler.get_job(AUTO_SYNC_JOB_ID)
        if job:
            next_run = job.next_run_time.isoformat() if job.next_run_time else None
            auto_sync_enabled = True
    except:
        pass
    
    return {
        **sync_status,
        "auto_sync_enabled": auto_sync_enabled,
        "next_scheduled_run": next_run
    }

@api_router.post("/admin/sync/run")
async def run_sync(background_tasks: BackgroundTasks, target_date: Optional[str] = None):
    """Run sync with API Global portal"""
    global sync_status
    
    if sync_status["running"]:
        raise HTTPException(status_code=400, detail="Sync already in progress")
    
    settings = await db.settings.find_one({"id": "portal_settings"}, {"_id": 0})
    if not settings or not settings.get("api_global_username") or not settings.get("api_global_password_encrypted"):
        raise HTTPException(status_code=400, detail="Portal credentials not configured")
    
    # Get Hodler Inn records for the target date
    if target_date:
        query = {"check_in_date": target_date}
    else:
        # Default to yesterday or today based on time
        now = datetime.now()
        if now.hour >= 18:
            target = (now - timedelta(days=1)).strftime("%Y-%m-%d")
        else:
            target = now.strftime("%Y-%m-%d")
        query = {"check_in_date": target}
    
    bookings = await db.bookings.find(query, {"_id": 0}).sort([("check_in_date", 1), ("check_in_time", 1)]).to_list(1000)
    
    # Get employee names from EMPLOYEES collection (Admin updated names)
    # This ensures sync agent uses the portal-format names you've updated
    employee_numbers = [b['employee_number'] for b in bookings]
    employees_list = await db.employees.find({"employee_number": {"$in": employee_numbers}}, {"_id": 0}).to_list(1000)
    employees_dict = {e['employee_number']: e for e in employees_list}
    
    # Fallback to guests if employee not found
    guests_list = await db.guests.find({"employee_number": {"$in": employee_numbers}}, {"_id": 0}).to_list(1000)
    guests_dict = {g['employee_number']: g for g in guests_list}
    
    # Build records for sync agent - PRIORITIZE employee list names
    hodler_records = []
    for booking in bookings:
        employee = employees_dict.get(booking['employee_number'])
        guest = guests_dict.get(booking['employee_number'])
        
        # Use employee list name first (the one you updated to match portal)
        # Fallback to guest name if employee not in list
        if employee and employee.get('name'):
            name_to_use = employee.get('name')
            logging.info(f"Using EMPLOYEE name for {booking['employee_number']}: {name_to_use}")
        elif guest:
            # Handle both encrypted and non-encrypted names
            name_encrypted = guest.get('name_encrypted')
            if name_encrypted:
                name_to_use = decrypt_data(name_encrypted)
            else:
                name_to_use = guest.get('name', '')
            logging.info(f"Using GUEST name for {booking['employee_number']}: {name_to_use}")
        else:
            continue
        
        hodler_records.append({
            "employee_name": name_to_use,
            "employee_number": booking['employee_number'],
            "room_number": booking['room_number']
        })
    
    # Store sync params for background task
    sync_params = {
        "username": settings.get("api_global_username"),
        "password": decrypt_data(settings.get("api_global_password_encrypted")),
        "hodler_records": hodler_records,
        "target": target_date or target
    }
    
    # Get name aliases for matching
    name_aliases = await db.name_aliases.find({}, {"_id": 0}).to_list(100)
    
    # Run sync in background using asyncio.create_task
    async def run_sync_task_wrapper():
        global sync_status
        sync_status["running"] = True
        sync_status["progress"] = "Starting sync..."
        
        try:
            from sync_agent import APIGlobalSyncAgent
            
            agent = APIGlobalSyncAgent(sync_params["username"], sync_params["password"])
            results = await agent.run_sync(sync_params["hodler_records"], sync_params["target"], name_aliases)
            
            sync_status["last_results"] = results
            sync_status["last_run"] = datetime.now(timezone.utc).isoformat()
            sync_status["progress"] = "Sync completed"
            
            # Auto-update employee names to match portal format
            if results.get("verified"):
                names_updated = 0
                for verified in results["verified"]:
                    if verified.get("update_name") and verified.get("portal_name") and verified.get("employee_id"):
                        # Update employee name in database to match portal format
                        portal_name = verified["portal_name"]
                        employee_id = verified["employee_id"]
                        
                        await db.employees.update_one(
                            {"employee_number": employee_id},
                            {"$set": {"name": portal_name, "portal_name_synced": True}}
                        )
                        await db.guests.update_one(
                            {"employee_number": employee_id},
                            {"$set": {"name": portal_name}}
                        )
                        names_updated += 1
                        logging.info(f"Updated employee name to portal format: {employee_id} -> {portal_name}")
                
                if names_updated > 0:
                    logging.info(f"Synced {names_updated} employee name(s) to portal format")
            
            # Store sync history
            await db.sync_history.insert_one({
                "id": str(uuid.uuid4()),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "target_date": sync_params["target"],
                "results": results
            })
            
        except Exception as e:
            sync_status["progress"] = f"Sync failed: {str(e)}"
            sync_status["last_results"] = {"errors": [str(e)]}
        finally:
            sync_status["running"] = False
    
    # Start background task using asyncio.create_task directly
    asyncio.create_task(run_sync_task_wrapper())
    
    return {"message": "Sync started", "hodler_records_count": len(hodler_records)}


@api_router.get("/admin/sync/debug-records")
async def debug_sync_records(target_date: str = None):
    """Debug: Show what records the sync agent will use for matching."""
    today = datetime.now()
    if not target_date:
        target_date = (today - timedelta(days=1)).strftime("%Y-%m-%d")
    
    # Get bookings for target date (in-house)
    bookings = await db.bookings.find({
        "check_in_date": target_date,
        "is_checked_out": False
    }, {"_id": 0}).to_list(100)
    
    # Get employee names from EMPLOYEES collection (Admin updated names)
    employee_numbers = [b['employee_number'] for b in bookings]
    employees_list = await db.employees.find({"employee_number": {"$in": employee_numbers}}, {"_id": 0}).to_list(100)
    employees_dict = {e['employee_number']: e for e in employees_list}
    
    # Get guests for comparison
    guests_list = await db.guests.find({"employee_number": {"$in": employee_numbers}}, {"_id": 0}).to_list(100)
    guests_dict = {g['employee_number']: g for g in guests_list}
    
    # Build records showing both names
    from sync_agent import normalize_name
    
    hodler_records = []
    for booking in bookings:
        employee = employees_dict.get(booking['employee_number'])
        guest = guests_dict.get(booking['employee_number'])
        
        # Get employee list name
        employee_name = employee.get('name', '') if employee else ''
        
        # Get guest check-in name
        guest_name = ''
        if guest:
            name_encrypted = guest.get('name_encrypted')
            if name_encrypted:
                guest_name = decrypt_data(name_encrypted)
            else:
                guest_name = guest.get('name', '')
        
        # Name that will be used for matching (employee list takes priority)
        name_for_sync = employee_name if employee_name else guest_name
        normalized = normalize_name(name_for_sync)
        
        hodler_records.append({
            "employee_number": booking['employee_number'],
            "room_number": booking['room_number'],
            "employee_list_name": employee_name,
            "guest_checkin_name": guest_name,
            "name_used_for_sync": name_for_sync,
            "normalized": normalized
        })
    
    return {
        "target_date": target_date,
        "total_records": len(hodler_records),
        "note": "Sync agent now uses 'employee_list_name' if available (you updated these to match portal)",
        "records": hodler_records
    }


@api_router.get("/admin/sync/test-matching")
async def test_name_matching(portal_name: str, hodler_name: str):
    """Test if two names would match in the sync agent."""
    from sync_agent import normalize_name, match_names
    
    norm_portal = normalize_name(portal_name)
    norm_hodler = normalize_name(hodler_name)
    matches = match_names(portal_name, hodler_name)
    
    return {
        "portal_name": portal_name,
        "portal_normalized": norm_portal,
        "hodler_name": hodler_name,
        "hodler_normalized": norm_hodler,
        "would_match": matches
    }


@api_router.get("/admin/sync/history")
async def get_sync_history():
    """Get sync history"""
    history = await db.sync_history.find({}, {"_id": 0}).sort("timestamp", -1).to_list(20)
    return history


@api_router.get("/admin/sync/count-entries")
async def count_portal_entries(target_date: str = "2026-03-03"):
    """
    Diagnostic: Count how many entries the sync agent can see on the portal for a given date.
    This helps verify that scrolling/pagination is working correctly.
    """
    settings = await db.settings.find_one({"id": "portal_settings"}, {"_id": 0})
    
    if not settings or not settings.get("api_global_username") or not settings.get("api_global_password_encrypted"):
        raise HTTPException(status_code=400, detail="Portal credentials not configured")
    
    username = settings.get("api_global_username")
    password = decrypt_data(settings.get("api_global_password_encrypted"))
    
    try:
        from sync_agent import APIGlobalSyncAgent
        
        agent = APIGlobalSyncAgent(username, password)
        
        # Initialize browser
        await agent.start()
        
        # Login
        login_success = await agent.login()
        if not login_success:
            await agent.stop()
            return {"success": False, "error": "Failed to login to portal"}
        
        # Navigate to Sign-in Sheets page first (CRITICAL - was missing before!)
        nav_success = await agent.navigate_to_signin_sheets()
        if not nav_success:
            await agent.stop()
            return {"success": False, "error": "Failed to navigate to Sign-in Sheets page"}
        
        # Load sign-in sheet for target date
        load_success = await agent.load_signin_sheet(target_date)
        if not load_success:
            await agent.stop()
            return {"success": False, "error": f"Failed to load sign-in sheet for {target_date}"}
        
        # Get entries
        entries = await agent.get_signin_sheet_entries()
        
        # Count by status
        total = len(entries)
        verified_count = len([e for e in entries if e.get("verified") or e.get("has_blue_status")])
        red_count = len([e for e in entries if e.get("has_red_status") and not e.get("verified")])
        needs_verification = len([e for e in entries if not e.get("verified") and not e.get("has_blue_status")])
        
        # Get names for debugging
        entry_names = [{"name": e.get("name"), "verified": e.get("verified"), "red": e.get("has_red_status"), "blue": e.get("has_blue_status"), "emp_id": e.get("current_emp_id")} for e in entries]
        
        await agent.stop()
        
        return {
            "success": True,
            "target_date": target_date,
            "total_entries": total,
            "already_verified": verified_count,
            "red_status_unverified": red_count,
            "needs_verification": needs_verification,
            "entries": entry_names,
            "debug_note": "If all entries show verified=False but you see blue checkmarks on portal, the status detection needs fixing"
        }
        
    except Exception as e:
        logging.error(f"Count entries failed: {e}")
        import traceback
        return {"success": False, "error": str(e), "traceback": traceback.format_exc()}


@api_router.get("/admin/sync/test-date-picker")
async def test_date_picker(target_date: str = "2026-03-03"):
    """
    Diagnostic: Test only the date picker interaction without running full sync.
    Returns detailed info about what happened during date selection.
    
    Use this to verify the date picker fix is working before running full sync.
    """
    settings = await db.settings.find_one({"id": "portal_settings"}, {"_id": 0})
    
    if not settings or not settings.get("api_global_username") or not settings.get("api_global_password_encrypted"):
        raise HTTPException(status_code=400, detail="Portal credentials not configured")
    
    username = settings.get("api_global_username")
    password = decrypt_data(settings.get("api_global_password_encrypted"))
    
    try:
        from sync_agent import APIGlobalSyncAgent
        
        agent = APIGlobalSyncAgent(username, password)
        results = {
            "target_date": target_date,
            "steps": [],
            "final_status": "unknown"
        }
        
        # Step 1: Initialize browser
        results["steps"].append("1. Starting browser...")
        await agent.start()
        results["steps"].append("   Browser started successfully")
        
        # Step 2: Login
        results["steps"].append("2. Logging in...")
        login_success = await agent.login()
        if not login_success:
            results["steps"].append("   ❌ Login FAILED")
            results["final_status"] = "failed_login"
            await agent.stop()
            return {"success": False, "results": results}
        results["steps"].append("   ✓ Login successful")
        
        # Step 3: Navigate to Sign-in Sheets
        results["steps"].append("3. Navigating to Sign-in Sheets...")
        nav_success = await agent.navigate_to_signin_sheets()
        if not nav_success:
            results["steps"].append("   ❌ Navigation FAILED")
            results["final_status"] = "failed_navigation"
            await agent.stop()
            return {"success": False, "results": results}
        results["steps"].append("   ✓ Navigation successful")
        
        # Step 4: Load sign-in sheet with date
        results["steps"].append(f"4. Loading sign-in sheet for date: {target_date}...")
        try:
            load_success = await agent.load_signin_sheet(target_date)
            if load_success:
                results["steps"].append("   ✓ Load successful - 'Scheduled Arrivals' found")
            else:
                results["steps"].append("   ❌ Load returned False")
                results["final_status"] = "load_returned_false"
        except Exception as load_err:
            results["steps"].append(f"   ❌ Load raised exception: {str(load_err)}")
            results["final_status"] = "load_exception"
            results["error_details"] = str(load_err)
            await agent.stop()
            return {"success": False, "results": results}
        
        # Step 5: Count entries found
        results["steps"].append("5. Counting entries found on page...")
        entries = await agent.get_signin_sheet_entries()
        entry_count = len(entries)
        results["steps"].append(f"   Found {entry_count} entries")
        results["entry_count"] = entry_count
        
        # Get first few entry names for verification
        if entries:
            first_entries = [e.get("name") for e in entries[:5]]
            results["first_5_entries"] = first_entries
            results["steps"].append(f"   First entries: {first_entries}")
        
        await agent.stop()
        
        # Determine final status
        if entry_count > 0:
            results["final_status"] = "success"
            results["steps"].append(f"✅ SUCCESS: Date picker worked! Found {entry_count} entries for {target_date}")
            return {"success": True, "results": results}
        else:
            results["final_status"] = "no_entries"
            results["steps"].append(f"⚠️ WARNING: Date picker may have worked but no entries found for {target_date}")
            return {"success": True, "results": results, "warning": "No entries found - verify this date has data on portal"}
        
    except Exception as e:
        logging.error(f"Date picker test failed: {e}")
        import traceback
        return {"success": False, "error": str(e), "traceback": traceback.format_exc()}


# ==================== Name Alias/Mapping for Sync Agent ====================

class NameAliasInput(BaseModel):
    portal_name: str  # Name as it appears on API Global portal
    employee_number: str  # Employee number in Hodler Inn


@api_router.get("/admin/sync/name-aliases")
async def get_name_aliases():
    """Get all name aliases for sync agent matching."""
    aliases = await db.name_aliases.find({}, {"_id": 0}).to_list(100)
    return aliases


@api_router.post("/admin/sync/name-aliases")
async def add_name_alias(input: NameAliasInput):
    """Add a name alias so sync agent can match portal names to employees."""
    # Check if employee exists
    employee = await db.employees.find_one({"employee_number": input.employee_number}, {"_id": 0})
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found with that number")
    
    # Check if alias already exists
    existing = await db.name_aliases.find_one({"portal_name": input.portal_name.lower()}, {"_id": 0})
    if existing:
        # Update existing alias
        await db.name_aliases.update_one(
            {"portal_name": input.portal_name.lower()},
            {"$set": {"employee_number": input.employee_number, "employee_name": employee.get("name")}}
        )
        return {"message": f"Updated alias: '{input.portal_name}' → {employee.get('name')} ({input.employee_number})"}
    
    # Create new alias
    doc = {
        "id": str(uuid.uuid4()),
        "portal_name": input.portal_name.lower(),  # Normalized for matching
        "employee_number": input.employee_number,
        "employee_name": employee.get("name"),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.name_aliases.insert_one(doc)
    doc.pop('_id', None)
    
    return {"message": f"Added alias: '{input.portal_name}' → {employee.get('name')} ({input.employee_number})", "alias": doc}


@api_router.delete("/admin/sync/name-aliases/{alias_id}")
async def delete_name_alias(alias_id: str):
    """Delete a name alias."""
    result = await db.name_aliases.delete_one({"id": alias_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Alias not found")
    return {"message": "Alias deleted"}


@api_router.post("/admin/import-from-guests")
async def import_employees_from_guests():
    """Import employees from existing Hodler Inn guest records into the Employee List."""
    # Get all unique employee numbers from bookings
    bookings = await db.bookings.find({}).to_list(1000)
    
    logging.info(f"Import from guests: Found {len(bookings)} bookings")
    
    imported = 0
    skipped = 0
    
    seen_ids = set()
    for booking in bookings:
        employee_number = str(booking.get("employee_number", "")).strip()
        
        if not employee_number or employee_number in seen_ids:
            continue
        
        seen_ids.add(employee_number)
        
        # Check if already exists in employee list
        existing = await db.employees.find_one({"employee_number": employee_number})
        if existing:
            skipped += 1
            continue
        
        # Get name from the booking's employee_name field first
        name = str(booking.get("employee_name", "")).strip()
        
        # If no name in booking, look up from guests collection
        if not name:
            guest = await db.guests.find_one({"employee_number": employee_number})
            if guest:
                # Try to get decrypted name
                if guest.get('name_encrypted'):
                    try:
                        name = decrypt_data(guest['name_encrypted'])
                    except:
                        name = guest.get('name', '')
                else:
                    name = guest.get('name', '')
        
        if not name:
            logging.warning(f"No name found for employee {employee_number}, skipping")
            continue
        
        # Add to employee list
        employee = {
            "id": str(uuid.uuid4()),
            "employee_number": employee_number,
            "name": name,
            "is_active": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "source": "guest_import"
        }
        await db.employees.insert_one(employee)
        imported += 1
        logging.info(f"Imported employee: {employee_number} - {name}")
    
    return {
        "success": True,
        "message": f"Imported {imported} employees from guest records, skipped {skipped} duplicates.",
        "imported": imported,
        "skipped": skipped
    }

@api_router.post("/admin/collect-employees")
async def collect_employees_from_portal_endpoint():
    """Use AI agent to collect employee names and IDs from the railroad portal Sign-in Report."""
    settings = await db.settings.find_one({}, {"_id": 0}) or {}
    
    if not settings.get("api_global_username") or not settings.get("api_global_password_encrypted"):
        raise HTTPException(status_code=400, detail="Portal credentials not configured")
    
    try:
        from sync_agent import collect_employees_from_portal
        
        username = settings.get("api_global_username")
        password = decrypt_data(settings.get("api_global_password_encrypted"))
        
        logging.info(f"Starting portal import for username: {username}")
        result = await collect_employees_from_portal(username, password)
        logging.info(f"Portal import result: success={result.get('success')}, employees={len(result.get('employees', []))}")
        
        if result["success"] and result["employees"]:
            # Import employees with their actual IDs from the portal
            imported = 0
            skipped = 0
            
            for emp in result["employees"]:
                employee_number = emp.get("employee_number", "").strip()
                name = emp.get("name", "").strip()
                
                if not employee_number or not name:
                    skipped += 1
                    continue
                
                # Check if already exists
                existing = await db.employees.find_one({
                    "employee_number": employee_number
                }, {"_id": 0})
                
                if existing:
                    skipped += 1
                    continue
                
                employee = {
                    "id": str(uuid.uuid4()),
                    "employee_number": employee_number,
                    "name": name,
                    "is_active": True,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "source": "portal_import"
                }
                await db.employees.insert_one(employee)
                imported += 1
            
            result["imported"] = imported
            result["skipped"] = skipped
            result["message"] = f"Found {len(result['employees'])} employees. Imported {imported}, skipped {skipped} duplicates."
        
        return result
    except Exception as e:
        logging.error(f"Portal import error: {str(e)}")
        import traceback
        logging.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to collect employees: {str(e)}")

# ==================== PDF Export ====================

@api_router.get("/admin/export-pdf")
async def export_signin_pdf(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None)
):
    """Export Sign-In Sheet as PDF with signature images"""
    query = {}
    if start_date or end_date:
        date_filter = {}
        if start_date:
            date_filter["$gte"] = start_date
        if end_date:
            date_filter["$lte"] = end_date
        if date_filter:
            query["check_in_date"] = date_filter
    
    bookings = await db.bookings.find(query, {"_id": 0}).sort([("check_in_date", 1), ("check_in_time", 1)]).to_list(1000)
    
    employee_numbers = [b['employee_number'] for b in bookings]
    guests_list = await db.guests.find({"employee_number": {"$in": employee_numbers}}, {"_id": 0}).to_list(1000)
    guests_dict = {g['employee_number']: g for g in guests_list}
    
    output = io.BytesIO()
    doc = SimpleDocTemplate(output, pagesize=landscape(letter), topMargin=0.5*inch, bottomMargin=0.5*inch)
    elements = []
    styles = getSampleStyleSheet()
    
    # Title
    title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=20, alignment=TA_CENTER, textColor=colors.HexColor('#fbbf24'))
    subtitle_style = ParagraphStyle('Subtitle', parent=styles['Normal'], fontSize=10, alignment=TA_CENTER, textColor=colors.gray)
    
    elements.append(Paragraph("Hodler Inn - Sign-In Sheet", title_style))
    elements.append(Paragraph("820 Hwy 59 N Heavener, OK, 74937 | Phone: 918-653-7801", subtitle_style))
    if start_date or end_date:
        date_range = f"Date Range: {start_date or 'Start'} to {end_date or 'Present'}"
        elements.append(Paragraph(date_range, subtitle_style))
    elements.append(Spacer(1, 0.3*inch))
    
    # Table data with signature images
    table_data = [['#', 'Name', 'Employee ID', 'Signature', 'Date In', 'Time In', 'Date Out', 'Time Out', 'Room']]
    
    for idx, booking in enumerate(bookings):
        guest = guests_dict.get(booking['employee_number'])
        if guest:
            decrypted_name = decrypt_data(guest.get('name_encrypted', guest.get('name', '')))
            
            # Get signature image
            sig_element = '-'
            if booking.get('signature_encrypted'):
                try:
                    sig_data = decrypt_data(booking['signature_encrypted'])
                    if sig_data and sig_data.startswith('data:image'):
                        # Remove data URL prefix
                        base64_data = sig_data.split(',')[1] if ',' in sig_data else sig_data
                        sig_bytes = base64.b64decode(base64_data)
                        sig_buffer = io.BytesIO(sig_bytes)
                        sig_img = RLImage(sig_buffer, width=60, height=25)
                        sig_element = sig_img
                except Exception as e:
                    logging.warning(f"Could not decode signature for booking {booking.get('id')}: {e}")
                    sig_element = 'Yes'
            
            table_data.append([
                str(idx + 1),
                decrypted_name[:20],
                booking['employee_number'],
                sig_element,
                booking['check_in_date'],
                booking['check_in_time'],
                booking.get('check_out_date', '-'),
                booking.get('check_out_time', '-'),
                booking['room_number']
            ])
    
    if len(table_data) == 1:
        table_data.append(['-', 'No records found', '-', '-', '-', '-', '-', '-', '-'])
    
    # Adjust column widths to accommodate signature images
    col_widths = [0.4*inch, 1.3*inch, 0.9*inch, 1.0*inch, 0.8*inch, 0.6*inch, 0.8*inch, 0.6*inch, 0.5*inch]
    table = Table(table_data, colWidths=col_widths, repeatRows=1)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#fbbf24')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('TOPPADDING', (0, 1), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.gray),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),
    ]))
    elements.append(table)
    
    doc.build(elements)
    output.seek(0)
    
    return StreamingResponse(
        output,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=hodler_inn_sign_in_sheet.pdf"}
    )

@api_router.get("/admin/export-billing-pdf")
async def export_billing_pdf(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None)
):
    """Export Billing Report as PDF"""
    query = {"is_checked_out": True}
    if start_date or end_date:
        date_filter = {}
        if start_date:
            date_filter["$gte"] = start_date
        if end_date:
            date_filter["$lte"] = end_date
        if date_filter:
            query["check_in_date"] = date_filter
    
    bookings = await db.bookings.find(query, {"_id": 0}).sort([("check_in_date", 1), ("check_in_time", 1)]).to_list(1000)
    
    employee_numbers = [b['employee_number'] for b in bookings]
    guests_list = await db.guests.find({"employee_number": {"$in": employee_numbers}}, {"_id": 0}).to_list(1000)
    guests_dict = {g['employee_number']: g for g in guests_list}
    
    output = io.BytesIO()
    doc = SimpleDocTemplate(output, pagesize=landscape(letter), topMargin=0.5*inch, bottomMargin=0.5*inch)
    elements = []
    styles = getSampleStyleSheet()
    
    # Title
    title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=20, alignment=TA_CENTER, textColor=colors.HexColor('#fbbf24'))
    subtitle_style = ParagraphStyle('Subtitle', parent=styles['Normal'], fontSize=10, alignment=TA_CENTER, textColor=colors.gray)
    
    elements.append(Paragraph("Hodler Inn - Billing Report", title_style))
    elements.append(Paragraph("820 Hwy 59 N Heavener, OK, 74937 | Phone: 918-653-7801", subtitle_style))
    if start_date or end_date:
        date_range = f"Date Range: {start_date or 'Start'} to {end_date or 'Present'}"
        elements.append(Paragraph(date_range, subtitle_style))
    elements.append(Spacer(1, 0.3*inch))
    
    # Table data
    table_data = [['#', 'Name', 'Employee ID', 'Room', 'Check-In Date', 'Check-In Time', 'Check-Out Date', 'Check-Out Time', 'Hours', 'Nights', 'Signed']]
    total_nights = 0
    total_hours = 0
    
    for idx, booking in enumerate(bookings):
        guest = guests_dict.get(booking['employee_number'])
        if guest:
            decrypted_name = decrypt_data(guest.get('name_encrypted', guest.get('name', '')))
            # Signature is now in booking
            has_sig = bool(booking.get('signature_encrypted'))
            
            hours, nights = calculate_stay_duration(
                booking['check_in_date'],
                booking['check_in_time'],
                booking['check_out_date'],
                booking['check_out_time']
            )
            total_nights += nights if nights else 0
            total_hours += hours if hours else 0
            
            table_data.append([
                str(idx + 1),
                decrypted_name[:18],
                booking['employee_number'],
                booking['room_number'],
                booking['check_in_date'],
                booking['check_in_time'],
                booking['check_out_date'],
                booking['check_out_time'],
                f"{hours}h" if hours else '-',
                str(nights) if nights else '-',
                'Yes' if has_sig else 'No'
            ])
    
    if len(table_data) == 1:
        table_data.append(['-', 'No completed stays', '-', '-', '-', '-', '-', '-', '-', '-', '-'])
    else:
        # Add total row
        table_data.append(['', 'TOTAL', '', '', '', '', '', '', f'{total_hours:.1f}h', str(total_nights), ''])
    
    table = Table(table_data, repeatRows=1)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#fbbf24')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.gray),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#e0e0e0')),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
    ]))
    elements.append(table)
    
    doc.build(elements)
    output.seek(0)
    
    return StreamingResponse(
        output,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=hodler_inn_billing_report.pdf"}
    )

# CORS Configuration - Required for production deployment
cors_origins_env = os.environ.get('CORS_ORIGINS', '*')
cors_origins = ['*'] if cors_origins_env == '*' else cors_origins_env.split(',')
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Ensure Playwright browsers are installed on startup
@app.on_event("startup")
async def ensure_playwright_browsers():
    """Install Playwright browsers if not already installed"""
    try:
        import subprocess
        result = subprocess.run(
            ["playwright", "install", "chromium"],
            capture_output=True,
            text=True,
            timeout=120
        )
        if result.returncode == 0:
            logger.info("Playwright Chromium browser ready")
        else:
            logger.warning(f"Playwright install warning: {result.stderr}")
    except Exception as e:
        logger.warning(f"Could not install Playwright browsers: {e}")

# Root-level health check (required by some deployment systems)
@app.get("/health")
async def root_health_check():
    """Root-level health check for deployment monitoring"""
    try:
        await db.command('ping')
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "database": "disconnected", "error": str(e)}


# ==================== PUBLIC API ENDPOINTS (with API Key auth) ====================

async def verify_api_key(api_key: str = Query(..., description="API Key for authentication")):
    """Verify API key from database settings"""
    settings = await db.settings.find_one({}, {"_id": 0})
    stored_key = settings.get("public_api_key") if settings else None
    
    if not stored_key:
        raise HTTPException(status_code=403, detail="Public API not configured. Please set API key in Admin Settings.")
    
    if api_key != stored_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    return True


@api_router.get("/public/signin-sheets")
async def public_signin_sheets(
    api_key: str = Query(..., description="API Key for authentication"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    format: str = Query("json", description="Output format: json, csv")
):
    """
    Public API to access Sign-in Sheets data.
    
    Usage: GET /api/public/signin-sheets?api_key=YOUR_KEY&start_date=2026-03-01&end_date=2026-03-31
    """
    await verify_api_key(api_key)
    
    # Build query
    query = {}
    if start_date or end_date:
        date_filter = {}
        if start_date:
            date_filter["$gte"] = start_date
        if end_date:
            date_filter["$lte"] = end_date
        if date_filter:
            query["check_in_date"] = date_filter
    
    # Get bookings sorted by date
    bookings = await db.bookings.find(query, {"_id": 0}).sort([
        ("check_in_date", 1),
        ("check_in_time", 1)
    ]).to_list(1000)
    
    # Get guest names
    employee_numbers = list(set(b['employee_number'] for b in bookings))
    guests_list = await db.guests.find({"employee_number": {"$in": employee_numbers}}, {"_id": 0}).to_list(1000)
    guests_dict = {g['employee_number']: g for g in guests_list}
    
    # Build response data
    records = []
    for booking in bookings:
        guest = guests_dict.get(booking['employee_number'])
        name = ""
        if guest:
            if guest.get('name_encrypted'):
                try:
                    name = decrypt_data(guest['name_encrypted'])
                except:
                    name = guest.get('name', '')
            else:
                name = guest.get('name', '')
        
        records.append({
            "employee_number": booking['employee_number'],
            "employee_name": name,
            "room_number": booking['room_number'],
            "check_in_date": booking['check_in_date'],
            "check_in_time": booking['check_in_time'],
            "check_out_date": booking.get('check_out_date'),
            "check_out_time": booking.get('check_out_time'),
            "is_checked_out": booking.get('is_checked_out', False),
            "total_nights": booking.get('total_nights', 0)
        })
    
    if format == "csv":
        # Return CSV format
        output = io.StringIO()
        if records:
            writer = csv.DictWriter(output, fieldnames=records[0].keys())
            writer.writeheader()
            writer.writerows(records)
        
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=signin_sheets_{start_date or 'all'}_{end_date or 'present'}.csv"}
        )
    
    return {
        "success": True,
        "count": len(records),
        "date_range": {"start": start_date, "end": end_date},
        "records": records
    }


@api_router.get("/public/billing-report")
async def public_billing_report(
    api_key: str = Query(..., description="API Key for authentication"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    format: str = Query("json", description="Output format: json, csv")
):
    """
    Public API to access Billing Report data.
    Calculates billable nights based on calendar nights.
    
    Usage: GET /api/public/billing-report?api_key=YOUR_KEY&start_date=2026-03-01&end_date=2026-03-31
    """
    await verify_api_key(api_key)
    
    # Build query - only checked out bookings for billing
    query = {"is_checked_out": True}
    if start_date or end_date:
        date_filter = {}
        if start_date:
            date_filter["$gte"] = start_date
        if end_date:
            date_filter["$lte"] = end_date
        if date_filter:
            query["check_in_date"] = date_filter
    
    # Get bookings
    bookings = await db.bookings.find(query, {"_id": 0}).sort([
        ("check_in_date", 1)
    ]).to_list(1000)
    
    # Get guest names
    employee_numbers = list(set(b['employee_number'] for b in bookings))
    guests_list = await db.guests.find({"employee_number": {"$in": employee_numbers}}, {"_id": 0}).to_list(1000)
    guests_dict = {g['employee_number']: g for g in guests_list}
    
    # Build billing records
    billing_records = []
    total_nights = 0
    total_amount = 0
    
    # Get nightly rate from settings
    settings = await db.settings.find_one({}, {"_id": 0})
    nightly_rate = settings.get("nightly_rate", 75.0) if settings else 75.0
    
    for booking in bookings:
        guest = guests_dict.get(booking['employee_number'])
        name = ""
        if guest:
            if guest.get('name_encrypted'):
                try:
                    name = decrypt_data(guest['name_encrypted'])
                except:
                    name = guest.get('name', '')
            else:
                name = guest.get('name', '')
        
        nights = booking.get('total_nights', 0)
        is_no_bill = booking.get('is_no_bill', False)
        billable_nights = 0 if is_no_bill else nights
        amount = billable_nights * nightly_rate
        
        billing_records.append({
            "employee_number": booking['employee_number'],
            "employee_name": name,
            "room_number": booking['room_number'],
            "check_in_date": booking['check_in_date'],
            "check_out_date": booking.get('check_out_date'),
            "total_nights": nights,
            "is_no_bill": is_no_bill,
            "billable_nights": billable_nights,
            "nightly_rate": nightly_rate,
            "amount": amount
        })
        
        total_nights += billable_nights
        total_amount += amount
    
    if format == "csv":
        output = io.StringIO()
        if billing_records:
            writer = csv.DictWriter(output, fieldnames=billing_records[0].keys())
            writer.writeheader()
            writer.writerows(billing_records)
        
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=billing_report_{start_date or 'all'}_{end_date or 'present'}.csv"}
        )
    
    return {
        "success": True,
        "count": len(billing_records),
        "date_range": {"start": start_date, "end": end_date},
        "summary": {
            "total_billable_nights": total_nights,
            "nightly_rate": nightly_rate,
            "total_amount": total_amount
        },
        "records": billing_records
    }


# Include the router in the main app (MUST be after all route definitions)
app.include_router(api_router)


@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
