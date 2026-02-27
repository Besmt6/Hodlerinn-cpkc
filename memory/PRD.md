# Hodler Inn - Guest Check-In Management System PRD

## Original Problem Statement
Build a two-part application for a hotel named "Hodler Inn":

**Guest Portal Requirements:**
1. Register: First-time users register with employee number, name, and digital signature
2. Check-In: Guests check in with employee number, check-in date/time, and room number
3. Check-Out: Guests check out by entering room number, check-out date/time

**Admin Backend Requirements:**
1. Dashboard showing all guest activities (check-in/out dates, times, employee info, signatures, rooms)
2. Billing calculation: >24 hours = 2 nights auto-billing
3. Excel-formatted reports for billing

## User Personas
- **Corporate Employees (Guests)**: Use kiosk-style interface for self-service check-in/out
- **Hotel Staff (Admin)**: Access dashboard to view all records and export billing reports

## Core Requirements
- [x] Guest Registration with employee details (no signature - captured at check-in)
- [x] Guest Check-In with date/time, room, and **signature** (captured at check-in)
- [x] Guest Check-Out with date/time (reuses check-in signature, no new signature needed)
- [x] Admin login with password protection (password: hodlerinn2024)
- [x] Dashboard with stats and detailed records table
- [x] Billing calculation: >24 hours = 2+ nights
- [x] Excel export for billing reports (Sign-In Sheet + Billing Report)
- [x] PNG export with embedded signatures
- [x] PDF export for Sign-In Sheet and Billing Report
- [x] Telegram notifications (green for check-in, red for check-out)
- [x] AES encryption for sensitive guest data (name, signature)
- [x] Monthly auto-reset scheduler (1st of each month)
- [x] Custom logo integration
- [x] Color-coded buttons (Gold=Register, Green=Check-In, Red=Check-Out)
- [x] Password protection for guest Sign-In Sheet view (password: "cpkc" or valid employee ID)
- [x] Room Management (add/edit/delete rooms with types, floors, status)
- [x] Date Range Filtering on Sign-In Sheet and Billing Report

## What's Been Implemented (Feb 2026)
- Full-stack app with React frontend + FastAPI backend + MongoDB
- Dark luxury "Vault" theme with gold accents (Hodler Inn branding)
- Digital signature canvas using react-signature-canvas
- Calendar date picker for check-in/out dates
- Admin dashboard with real-time stats, edit/delete functionality
- **Room Management** with CRUD operations and status tracking (Available/Occupied/Maintenance)
- **Date Range Filtering** on both Sign-In Sheet and Billing Report views
- **PDF Export** using ReportLab for professional report generation
- Excel export using xlsxwriter (Sign-In Sheet + Billing Report)
- PNG export with embedded signature images
- Room occupancy validation
- Employee verification step before check-in
- Telegram notifications for check-in/out events
- AES encryption for sensitive data at rest
- Monthly data reset scheduler (APScheduler)
- Guest sign-in sheet view with password/employee ID protection

## Technical Stack
- Frontend: React 19, Tailwind CSS, Framer Motion, Shadcn/UI
- Backend: FastAPI, Motor (MongoDB async driver), Cryptography (Fernet), ReportLab
- Database: MongoDB
- Scheduler: APScheduler
- Dependencies: react-signature-canvas, xlsx, xlsxwriter, pycryptodome, Pillow, reportlab

## Prioritized Backlog
### P0 (Completed)
- Guest registration, check-in, check-out flows
- Admin dashboard with billing calculation
- Excel/PNG/PDF exports with signatures
- Password protection for guest sign-in sheet view
- Telegram notifications
- Data encryption
- Room Management (add/edit/delete)
- Date Range Filtering

### P1 (Blocked)
- **Elox Smart Lock Integration**: Send digital keys to guest phones after check-in
  - Status: BLOCKED - waiting for user to provide Elox API documentation

### P2 (Future)
- Email notifications on check-in/out
- Multi-admin support with roles
- Guest history/loyalty tracking
- Room availability calendar view

## Access Credentials
- **Admin Dashboard**: /admin → Password: hodlerinn2024
- **Guest Sign-In Sheet**: Password: cpkc (or valid employee ID)

## API Endpoints
### Room Management
- GET /api/admin/rooms - List all rooms with status
- POST /api/admin/rooms - Create new room
- PUT /api/admin/rooms/{room_id} - Update room
- DELETE /api/admin/rooms/{room_id} - Delete room

### PDF Export
- GET /api/admin/export-pdf - Sign-In Sheet PDF (supports date filters)
- GET /api/admin/export-billing-pdf - Billing Report PDF (supports date filters)

### Date Filtering
- GET /api/admin/records?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD

## Next Tasks
1. Elox Smart Lock Integration (waiting for API docs from user)
2. Email notifications on check-in/out
3. Room availability calendar view
