"""
Webhooks Router
Handles external webhook endpoints for integrations like phone agents.
"""
from fastapi import APIRouter, HTTPException
from datetime import datetime, timezone
from database import db
from security import decrypt_data
import logging

router = APIRouter(prefix="/webhook", tags=["webhooks"])


@router.get("/guests")
async def webhook_get_registered_guests():
    """
    Webhook for phone agent: Returns all currently checked-in guests with room numbers.
    Used by external phone system to route calls to guest rooms.
    
    Returns:
        JSON with status, timestamp, total_guests count, and list of guests
        Each guest includes: room, guest_name, employee_id, check_in_date, check_in_time, type
    """
    try:
        # Get all checked-in bookings
        bookings = await db.bookings.find(
            {"status": "checked_in"},
            {"_id": 0}
        ).to_list(100)
        
        guests = []
        for booking in bookings:
            # Get guest info
            guest = await db.guests.find_one(
                {"employee_number": booking.get("employee_number")},
                {"_id": 0}
            )
            
            # Try to get name from various sources
            guest_name = None
            
            # First try from employee collection (most accurate for railroad)
            employee = await db.employees.find_one(
                {"employee_number": booking.get("employee_number")},
                {"_id": 0}
            )
            if employee:
                guest_name = employee.get("name")
            
            # Then try from guest record
            if not guest_name and guest:
                if guest.get("name_encrypted"):
                    try:
                        guest_name = decrypt_data(guest.get("name_encrypted"))
                    except:
                        pass
                if not guest_name:
                    guest_name = guest.get("name")
            
            # Fallback to employee number
            if not guest_name:
                guest_name = f"Guest {booking.get('employee_number', 'Unknown')}"
            
            guests.append({
                "room": booking.get("room_number"),
                "guest_name": guest_name,
                "employee_id": booking.get("employee_number"),
                "check_in_date": booking.get("check_in_date"),
                "check_in_time": booking.get("check_in_time"),
                "type": "railroad" if booking.get("employee_number") else "non_railroad"
            })
        
        # Sort by room number
        guests.sort(key=lambda x: x.get("room", ""))
        
        return {
            "status": "success",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total_guests": len(guests),
            "guests": guests
        }
        
    except Exception as e:
        logging.error(f"Webhook error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rooms/available")
async def webhook_get_available_rooms():
    """
    Webhook for checking available rooms.
    Can be used by external booking systems.
    
    Returns:
        JSON with available room count and list of available rooms
    """
    try:
        # Get all rooms
        rooms = await db.rooms.find({}, {"_id": 0}).to_list(100)
        
        # Get occupied room numbers
        occupied_bookings = await db.bookings.find(
            {"status": "checked_in"},
            {"room_number": 1, "_id": 0}
        ).to_list(100)
        occupied_rooms = {b["room_number"] for b in occupied_bookings}
        
        # Filter available rooms
        available_rooms = [
            r for r in rooms 
            if r.get("room_number") not in occupied_rooms 
            and r.get("status") != "maintenance"
        ]
        
        return {
            "status": "success",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total_available": len(available_rooms),
            "rooms": available_rooms
        }
        
    except Exception as e:
        logging.error(f"Webhook error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def webhook_health_check():
    """
    Simple health check for webhook monitoring.
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "service": "hodler-inn-webhooks"
    }
