"""
Pydantic Models Module
Contains all data models and schemas for the API.
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime, timezone
import uuid


# ==================== Employee Models ====================

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


# ==================== Guest Models ====================

class GuestRegistration(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    employee_number: str
    name: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class GuestRegistrationCreate(BaseModel):
    employee_number: str
    name: str


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


# ==================== Check-in/Check-out Models ====================

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


# ==================== Room Models ====================

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


# ==================== Auth Models ====================

class AdminLogin(BaseModel):
    password: str


# ==================== Settings Models ====================

class PortalSettings(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = "portal_settings"
    api_global_username: Optional[str] = None
    api_global_password: Optional[str] = None  # Will be encrypted
    alert_email: Optional[str] = None
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class PortalSettingsUpdate(BaseModel):
    api_global_username: Optional[str] = None
    api_global_password: Optional[str] = None
    alert_email: Optional[str] = None
    voice_enabled: Optional[bool] = None  # Enable/disable voice messages
    voice_volume: Optional[float] = None  # Voice volume 0.0 to 1.0
    voice_speed: Optional[float] = None  # Voice speed 0.5 to 1.5
    telegram_chat_id: Optional[str] = None  # Telegram group/chat ID for notifications
    public_api_key: Optional[str] = None  # API key for public endpoints
    nightly_rate: Optional[float] = None  # Nightly room rate for billing (railroad)
    # Chatbot pricing settings
    single_room_rate: Optional[float] = None  # Single bed rate for chatbot
    double_room_rate: Optional[float] = None  # Double bed rate for chatbot
    sales_tax_rate: Optional[float] = None  # Sales tax percentage (e.g., 8.5 for 8.5%)
    chatbot_max_rooms: Optional[int] = None  # Max rooms chatbot can sell per day
    guaranteed_rooms: Optional[int] = None  # Number of guaranteed railroad rooms
    # Email report settings
    email_reports_enabled: Optional[bool] = None
    email_smtp_host: Optional[str] = None
    email_smtp_port: Optional[int] = None
    email_sender: Optional[str] = None
    email_password: Optional[str] = None  # Will be encrypted
    email_recipient: Optional[str] = None
    email_report_time: Optional[str] = None  # Format: HH:MM (24hr)


# ==================== Booking Models ====================

class Booking(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    employee_number: str
    room_number: str
    check_in_date: str
    check_in_time: str
    check_out_date: Optional[str] = None
    check_out_time: Optional[str] = None
    status: str = "checked_in"  # checked_in, checked_out
    signature: Optional[str] = None
    total_hours: Optional[float] = None
    total_nights: Optional[int] = None
    nightly_rate: float = 85.00
    total_amount: Optional[float] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ==================== CPKC/Expected Arrivals Models ====================

class ExpectedArrival(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    booking_id: Optional[str] = None
    employee_id: Optional[str] = None
    employee_name: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    check_in_date: str
    check_in_time: Optional[str] = None
    check_out_date: Optional[str] = None
    room_number: Optional[str] = None
    status: str = "expected"  # expected, checked_in, cancelled
    source: str = "cpkc_email"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ExpectedCheckout(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    booking_id: Optional[str] = None
    employee_id: Optional[str] = None
    employee_name: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    check_in_date: Optional[str] = None
    check_in_time: Optional[str] = None
    check_out_date: str
    check_out_time: Optional[str] = None
    room_number: Optional[str] = None
    status: str = "expected"  # expected, completed
    source: str = "cpkc_email"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ==================== Reservation Models ====================

class Reservation(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    guest_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    check_in_date: str
    check_out_date: str
    room_type: str = "single"  # single, double
    num_guests: int = 1
    room_rate: float
    tax_amount: float
    total_amount: float
    status: str = "pending"  # pending, confirmed, checked_in, checked_out, cancelled
    payment_intent_id: Optional[str] = None
    notes: Optional[str] = None
    source: str = "chatbot"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ==================== Chat Models ====================

class ChatMessage(BaseModel):
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    session_id: str
    action: Optional[str] = None
    data: Optional[dict] = None


# ==================== Sync Models ====================

class SyncRequest(BaseModel):
    target_date: str  # Format: YYYY-MM-DD
    include_prev_day: bool = False


class SyncResult(BaseModel):
    verified: List[dict] = []
    no_bill: List[dict] = []
    missing_in_hodler: List[dict] = []
    errors: List[str] = []
    summary: Optional[dict] = None
