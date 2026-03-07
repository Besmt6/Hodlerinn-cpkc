"""
Models Package
Contains all Pydantic models and schemas.
"""
from models.schemas import (
    # Employee
    Employee, EmployeeCreate, EmployeeUpdate,
    # Guest
    GuestRegistration, GuestRegistrationCreate, GuestRecord,
    # Check-in/out
    CheckIn, CheckInCreate, CheckOutCreate,
    # Room
    Room, RoomCreate, RoomUpdate,
    # Auth
    AdminLogin,
    # Settings
    PortalSettings, PortalSettingsUpdate,
    # Booking
    Booking,
    # CPKC
    ExpectedArrival, ExpectedCheckout,
    # Reservation
    Reservation,
    # Chat
    ChatMessage, ChatResponse,
    # Sync
    SyncRequest, SyncResult,
)

__all__ = [
    'Employee', 'EmployeeCreate', 'EmployeeUpdate',
    'GuestRegistration', 'GuestRegistrationCreate', 'GuestRecord',
    'CheckIn', 'CheckInCreate', 'CheckOutCreate',
    'Room', 'RoomCreate', 'RoomUpdate',
    'AdminLogin',
    'PortalSettings', 'PortalSettingsUpdate',
    'Booking',
    'ExpectedArrival', 'ExpectedCheckout',
    'Reservation',
    'ChatMessage', 'ChatResponse',
    'SyncRequest', 'SyncResult',
]
