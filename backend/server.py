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
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID', '')

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
                decrypted_name = decrypt_data(guest.get('name_encrypted', guest.get('name', '')))
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
        
        # Store sync history
        await db.sync_history.insert_one({
            "id": str(uuid.uuid4()),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "target_date": yesterday,
            "results": results,
            "auto_triggered": True
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
            
            # Schedule for 3 PM (15:00) every day, starting from start_date
            scheduler.add_job(
                lambda: asyncio.create_task(auto_sync_task()),
                CronTrigger(hour=15, minute=0, start_date=trigger_start),
                id=AUTO_SYNC_JOB_ID,
                replace_existing=True
            )
            if start_date:
                logging.info(f"Auto-sync scheduled for 3 PM daily, starting from {start_date}")
            else:
                logging.info("Auto-sync scheduled for 3 PM daily")
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
    """Get Telegram Chat ID from database settings, fallback to environment variable"""
    settings = await db.settings.find_one({}, {"_id": 0})
    if settings and settings.get("telegram_chat_id"):
        return settings.get("telegram_chat_id")
    return TELEGRAM_CHAT_ID

async def send_telegram_notification(message: str):
    """Send notification to Telegram (supports multiple chat IDs separated by comma)"""
    chat_id = await get_telegram_chat_id()
    
    if not TELEGRAM_BOT_TOKEN or not chat_id:
        return
    
    # Support multiple chat IDs separated by comma
    chat_ids = [cid.strip() for cid in chat_id.split(',') if cid.strip()]
    
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        async with httpx.AsyncClient() as client:
            for cid in chat_ids:
                await client.post(url, json={
                    "chat_id": cid,
                    "text": message,
                    "parse_mode": "HTML"
                })
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
    telegram_chat_id: Optional[str] = None  # Telegram group/chat ID for notifications

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

@api_router.get("/guests/{employee_number}")
async def get_guest(employee_number: str):
    guest = await db.guests.find_one({"employee_number": employee_number}, {"_id": 0})
    if not guest:
        raise HTTPException(status_code=404, detail="Guest not found")
    
    # Decrypt data before returning
    if 'name_encrypted' in guest:
        guest['name'] = decrypt_data(guest['name_encrypted'])
    
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
            "verified_at": datetime.now(timezone.utc).isoformat()
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

# Check-In (signature captured here)
@api_router.post("/checkin", response_model=CheckIn)
async def check_in(input: CheckInCreate):
    # Verify employee is registered
    guest = await db.guests.find_one({"employee_number": input.employee_number}, {"_id": 0})
    if not guest:
        raise HTTPException(status_code=404, detail="Employee not registered. Please register first.")
    
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
    
    bookings = await db.bookings.find(query, {"_id": 0}).to_list(1000)
    
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
    bookings = await db.bookings.find({}, {"_id": 0}).to_list(1000)
    
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

# Admin - Export Billing Report
@api_router.get("/admin/export-billing")
async def export_billing_report():
    bookings = await db.bookings.find({"is_checked_out": True}, {"_id": 0}).to_list(1000)
    
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
    worksheet.merge_range('A1:I1', 'Hodler Inn - Billing Report', title_format)
    worksheet.merge_range('A2:I2', '820 Hwy 59 N Heavener, OK, 74937 | Phone: 918-653-7801', subtitle_format)
    worksheet.set_row(0, 25)
    worksheet.set_row(1, 18)
    
    # Column Headers
    headers = [
        "#", "Name", "Employee ID", "Room #",
        "Check-In", "Check-Out", "Total Hours", "Nights Billed", "Signed"
    ]
    
    col_widths = [5, 20, 12, 8, 18, 18, 12, 12, 10]
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
            worksheet.write(row, 4, f"{booking['check_in_date']} {booking['check_in_time']}", cell_format)
            worksheet.write(row, 5, f"{booking['check_out_date']} {booking['check_out_time']}", cell_format)
            worksheet.write(row, 6, hours if hours else 0, number_format)
            worksheet.write(row, 7, nights if nights else 0, cell_format)
            worksheet.write(row, 8, "Yes" if has_signature else "No", cell_format)
            row += 1
            row_num += 1
    
    # Total row
    worksheet.write(row, 0, "", total_format)
    worksheet.merge_range(row, 1, row, 6, "TOTAL NIGHTS BILLED", total_format)
    worksheet.write(row, 7, total_nights, total_format)
    worksheet.write(row, 8, "", total_format)
    
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
async def export_billing_png():
    bookings = await db.bookings.find({"is_checked_out": True}, {"_id": 0}).to_list(1000)
    
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
        "voice_volume": settings.get("voice_volume", 1.0) if settings else 1.0
    }

# Pre-defined voice messages
VOICE_MESSAGES = {
    # Register welcome
    "register_welcome": "Welcome to Hodler Inn. If you are first time here, please register your employee number and name, then go to check in.",
    
    # Check-in welcome (when clicking check-in button)
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
    
    # Other reminders
    "signature_reminder": "Please sign your full name legibly. A simple line or X will not be accepted.",
    "room_reminder": "Please select the room number from key on desk. Print your name and room number on yellow card.",
    "checkout_found": "Booking found. Please verify and complete check out."
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
    employee = await db.employees.find_one({"id": employee_id}, {"_id": 0})
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    update_data = {k: v for k, v in input.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No data to update")
    
    # If updating employee_number, check for duplicates
    if "employee_number" in update_data:
        existing = await db.employees.find_one({
            "employee_number": update_data["employee_number"],
            "id": {"$ne": employee_id}
        }, {"_id": 0})
        if existing:
            raise HTTPException(status_code=400, detail="Employee number already exists")
    
    await db.employees.update_one({"id": employee_id}, {"$set": update_data})
    return {"message": "Employee updated successfully"}

@api_router.delete("/admin/employees/{employee_id}")
async def delete_employee(employee_id: str):
    """Delete an employee"""
    employee = await db.employees.find_one({"id": employee_id}, {"_id": 0})
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    await db.employees.delete_one({"id": employee_id})
    return {"message": "Employee deleted successfully"}

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
            "telegram_chat_id": TELEGRAM_CHAT_ID or ""
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
        "telegram_chat_id": settings.get("telegram_chat_id", "") or TELEGRAM_CHAT_ID or ""
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
    
    if input.telegram_chat_id is not None:
        update_data["telegram_chat_id"] = input.telegram_chat_id
    
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
    
    bookings = await db.bookings.find(query, {"_id": 0}).to_list(1000)
    
    # Get guest names
    employee_numbers = [b['employee_number'] for b in bookings]
    guests_list = await db.guests.find({"employee_number": {"$in": employee_numbers}}, {"_id": 0}).to_list(1000)
    guests_dict = {g['employee_number']: g for g in guests_list}
    
    # Build records for sync agent
    hodler_records = []
    for booking in bookings:
        guest = guests_dict.get(booking['employee_number'])
        if guest:
            decrypted_name = decrypt_data(guest.get('name_encrypted', guest.get('name', '')))
            hodler_records.append({
                "employee_name": decrypted_name,
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
    
    # Run sync in background using asyncio.create_task
    async def run_sync_task_wrapper():
        global sync_status
        sync_status["running"] = True
        sync_status["progress"] = "Starting sync..."
        
        try:
            from sync_agent import APIGlobalSyncAgent
            
            agent = APIGlobalSyncAgent(sync_params["username"], sync_params["password"])
            results = await agent.run_sync(sync_params["hodler_records"])
            
            sync_status["last_results"] = results
            sync_status["last_run"] = datetime.now(timezone.utc).isoformat()
            sync_status["progress"] = "Sync completed"
            
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

@api_router.get("/admin/sync/history")
async def get_sync_history():
    """Get sync history"""
    history = await db.sync_history.find({}, {"_id": 0}).sort("timestamp", -1).to_list(20)
    return history

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
    
    from sync_agent import collect_employees_from_portal
    
    username = settings.get("api_global_username")
    password = decrypt_data(settings.get("api_global_password_encrypted"))
    
    result = await collect_employees_from_portal(username, password)
    
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

# ==================== PDF Export ====================

@api_router.get("/admin/export-pdf")
async def export_signin_pdf(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None)
):
    """Export Sign-In Sheet as PDF"""
    query = {}
    if start_date or end_date:
        date_filter = {}
        if start_date:
            date_filter["$gte"] = start_date
        if end_date:
            date_filter["$lte"] = end_date
        if date_filter:
            query["check_in_date"] = date_filter
    
    bookings = await db.bookings.find(query, {"_id": 0}).to_list(1000)
    
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
    
    # Table data
    table_data = [['#', 'Stay Type', 'Name', 'Employee ID', 'Sig In', 'Sig Out', 'Date In', 'Time In', 'Date Out', 'Time Out', 'Room']]
    
    for idx, booking in enumerate(bookings):
        guest = guests_dict.get(booking['employee_number'])
        if guest:
            decrypted_name = decrypt_data(guest.get('name_encrypted', guest.get('name', '')))
            # Signature is now in booking
            has_sig = bool(booking.get('signature_encrypted'))
            is_out = booking.get('is_checked_out', False)
            
            table_data.append([
                str(idx + 1),
                'Single Stay',
                decrypted_name[:20],
                booking['employee_number'],
                'Yes' if has_sig else '-',
                'Yes' if (has_sig and is_out) else '-',
                booking['check_in_date'],
                booking['check_in_time'],
                booking.get('check_out_date', '-'),
                booking.get('check_out_time', '-'),
                booking['room_number']
            ])
    
    if len(table_data) == 1:
        table_data.append(['-', '-', 'No records found', '-', '-', '-', '-', '-', '-', '-', '-'])
    
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
    
    bookings = await db.bookings.find(query, {"_id": 0}).to_list(1000)
    
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
    table_data = [['#', 'Name', 'Employee ID', 'Room', 'Check-In', 'Check-Out', 'Hours', 'Nights', 'Signed']]
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
                decrypted_name[:20],
                booking['employee_number'],
                booking['room_number'],
                f"{booking['check_in_date']} {booking['check_in_time']}",
                f"{booking['check_out_date']} {booking['check_out_time']}",
                f"{hours}h" if hours else '-',
                str(nights) if nights else '-',
                'Yes' if has_sig else 'No'
            ])
    
    if len(table_data) == 1:
        table_data.append(['-', 'No completed stays', '-', '-', '-', '-', '-', '-', '-'])
    else:
        # Add total row
        table_data.append(['', 'TOTAL', '', '', '', '', f'{total_hours:.1f}h', str(total_nights), ''])
    
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

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Root-level health check (required by some deployment systems)
@app.get("/health")
async def root_health_check():
    """Root-level health check for deployment monitoring"""
    try:
        await db.command('ping')
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "database": "disconnected", "error": str(e)}

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
