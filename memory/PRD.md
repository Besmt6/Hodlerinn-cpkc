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

### P1 (Future Integration - Saved for Later)
- **UnlockOS Smart Lock Integration**: Automatic digital key delivery to guests after check-in
  - **Website:** https://unlockos.io
  - **What it does:** Connects payments with access control, auto-issues keys when guest pays
  - **Supported locks:** Yale, Schlage, August, and other major brands
  - **Pricing:** $0 setup, $0 monthly, $0.17 per check-in
  - **API Status:** Full Developer API/SDK coming in 2026
  - **Current Option:** Can use payment links for simple integration now
  - **Status:** SAVED FOR LATER - revisit when ready

### P2 (Future)
- Email notifications on check-in/out
- Multi-admin support with roles
- Guest history/loyalty tracking
- Room availability calendar view

### P3 (Saved for Later - Advanced Features)
- **Blockchain Integration:**
  - Immutable guest records (tamper-proof audit trail)
  - Smart contract billing (automatic payment on check-out)
  - NFT room keys (digital keys as NFTs)
  - Transparent pricing (rate agreements on-chain)
  - Loyalty tokens (reward frequent guests)
  - Network options: Polygon (recommended), Ethereum, Solana, or Base
  
- **AI Phone Bot:**
  - 24/7 automated call answering
  - Provide info (rates, availability, directions)
  - Take reservation requests
  - Check booking status
  - Transfer to human staff when needed
  - Multi-language support
  - Provider options: Vapi.ai (recommended), Retell AI, Twilio + OpenAI

## AI Verification Agent (March 2026)
**Status:** FUNCTIONAL - Login working, navigation needs calibration to portal UI

### Features Implemented:
- Portal Settings page in Admin Dashboard to store API Global credentials
- Encrypted credential storage (username + password)
- **Test Connection** - Successfully logs into the third-party railroad portal
- **Run Sync Now** - Background task automation with Playwright browser
- Sync Status tracking with results history
- Name matching algorithm (fuzzy matching with SequenceMatcher)

### Technical Details:
- Uses Playwright for headless browser automation
- Chromium browser installed for ARM64 architecture
- Async background task execution
- Login URL: https://providerrail.apps-apiglobalsolutions.com/ACESSUPPLIER/faces/login.xhtml

### Known Limitations:
- Navigation selectors need calibration based on actual portal UI structure
- The third-party website UI may change, requiring selector updates
- Currently, the "Sign In Sheets" menu navigation fails due to different menu structure

### Next Steps for Full Automation:
1. User should capture screenshots of the portal's navigation flow after login
2. Update selectors in `/app/backend/sync_agent.py` to match actual UI elements
3. Test with real booking data matching the portal's date

## Access Credentials
- **Admin Dashboard**: /admin → Password: hodlerinn2024
- **Guest Sign-In Sheet**: Password: cpkc (or valid employee ID)
- **API Global Portal**: Credentials entered in Portal Settings (encrypted)

## API Endpoints
### Room Management
- GET /api/admin/rooms - List all rooms with status
- POST /api/admin/rooms - Create new room
- PUT /api/admin/rooms/{room_id} - Update room
- DELETE /api/admin/rooms/{room_id} - Delete room

### PDF Export
- GET /api/admin/export-pdf - Sign-In Sheet PDF (supports date filters)
- GET /api/admin/export-billing-pdf - Billing Report PDF (supports date filters)

### Portal Sync (AI Verification Agent)
- GET /api/admin/settings - Get portal settings
- POST /api/admin/settings - Update portal settings
- POST /api/admin/settings/test-connection - Test portal login
- POST /api/admin/sync/run - Start sync process
- GET /api/admin/sync/status - Get sync status
- GET /api/admin/sync/history - Get sync history

### Date Filtering
- GET /api/admin/records?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD

## Next Tasks
1. **Calibrate AI Sync Agent selectors** - User needs to provide portal UI screenshots after login
2. UnlockOS Smart Lock Integration (saved for later)
3. Email notifications on check-in/out
4. Room availability calendar view
5. Blockchain integration (saved for later)
6. AI Phone Bot (saved for later)
