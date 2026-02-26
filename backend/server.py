from fastapi import FastAPI, APIRouter, HTTPException, Response
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
import uuid
from datetime import datetime, timezone
import io
import xlsxwriter
import math

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Admin password (simple protection)
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'hodlerinn2024')

# ==================== Models ====================

class GuestRegistration(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    employee_number: str
    name: str
    signature: str  # Base64 encoded signature image
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class GuestRegistrationCreate(BaseModel):
    employee_number: str
    name: str
    signature: str

class CheckIn(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    employee_number: str
    room_number: str
    check_in_date: str  # ISO format date
    check_in_time: str  # HH:MM format
    check_out_date: Optional[str] = None
    check_out_time: Optional[str] = None
    is_checked_out: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class CheckInCreate(BaseModel):
    employee_number: str
    room_number: str
    check_in_date: str
    check_in_time: str

class CheckOutCreate(BaseModel):
    room_number: str
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

# ==================== Helper Functions ====================

def calculate_stay_duration(check_in_date: str, check_in_time: str, check_out_date: str, check_out_time: str):
    """Calculate total hours and nights billed"""
    try:
        check_in_dt = datetime.strptime(f"{check_in_date} {check_in_time}", "%Y-%m-%d %H:%M")
        check_out_dt = datetime.strptime(f"{check_out_date} {check_out_time}", "%Y-%m-%d %H:%M")
        
        duration = check_out_dt - check_in_dt
        total_hours = duration.total_seconds() / 3600
        
        # Billing logic: anything over 24 hours = 2 nights, otherwise ceil
        if total_hours > 24:
            total_nights = math.ceil(total_hours / 24)
        else:
            total_nights = 1
        
        return round(total_hours, 2), total_nights
    except Exception:
        return None, None

# ==================== Routes ====================

@api_router.get("/")
async def root():
    return {"message": "Hodler Inn API - Welcome"}

# Guest Registration
@api_router.post("/guests/register", response_model=GuestRegistration)
async def register_guest(input: GuestRegistrationCreate):
    # Check if employee already registered
    existing = await db.guests.find_one({"employee_number": input.employee_number}, {"_id": 0})
    if existing:
        raise HTTPException(status_code=400, detail="Employee already registered")
    
    guest = GuestRegistration(**input.model_dump())
    doc = guest.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    
    await db.guests.insert_one(doc)
    return guest

@api_router.get("/guests/{employee_number}")
async def get_guest(employee_number: str):
    guest = await db.guests.find_one({"employee_number": employee_number}, {"_id": 0})
    if not guest:
        raise HTTPException(status_code=404, detail="Guest not found")
    return guest

# Check-In
@api_router.post("/checkin", response_model=CheckIn)
async def check_in(input: CheckInCreate):
    # Verify employee is registered
    guest = await db.guests.find_one({"employee_number": input.employee_number}, {"_id": 0})
    if not guest:
        raise HTTPException(status_code=404, detail="Employee not registered. Please register first.")
    
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
    
    await db.bookings.insert_one(doc)
    return checkin

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
    
    return {"message": "Check-out successful", "booking_id": booking['id']}

# Admin Login
@api_router.post("/admin/login")
async def admin_login(input: AdminLogin):
    if input.password == ADMIN_PASSWORD:
        return {"success": True, "message": "Login successful"}
    raise HTTPException(status_code=401, detail="Invalid password")

# Admin - Get all records
@api_router.get("/admin/records", response_model=List[GuestRecord])
async def get_all_records():
    bookings = await db.bookings.find({}, {"_id": 0}).to_list(1000)
    
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
            
            records.append(GuestRecord(
                id=booking['id'],
                employee_number=booking['employee_number'],
                employee_name=guest['name'],
                signature=guest['signature'],
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
        guest = await db.guests.find_one({"employee_number": booking['employee_number']}, {"_id": 0})
        if guest:
            has_signature = bool(guest.get('signature'))
            is_checked_out = booking.get('is_checked_out', False)
            
            worksheet.write(row, 0, row_num, cell_format)
            worksheet.write(row, 1, "Single Stay", cell_format)
            worksheet.write(row, 2, guest['name'], cell_format)
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
        guest = await db.guests.find_one({"employee_number": booking['employee_number']}, {"_id": 0})
        if guest:
            hours, nights = calculate_stay_duration(
                booking['check_in_date'],
                booking['check_in_time'],
                booking['check_out_date'],
                booking['check_out_time']
            )
            
            has_signature = bool(guest.get('signature'))
            total_nights += nights if nights else 0
            
            worksheet.write(row, 0, row_num, cell_format)
            worksheet.write(row, 1, guest['name'], cell_format)
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

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
