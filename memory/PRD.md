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
**Status:** ✅ FULLY FUNCTIONAL with Auto-Sync!

### Features Implemented:
- Portal Settings page in Admin Dashboard to store API Global credentials
- Encrypted credential storage (username + password)
- **Test Connection** - Successfully logs into the third-party railroad portal
- **Run Sync Now** - Manual sync trigger
- **Auto-Sync Toggle** - Automatically runs daily at 3 PM
- Full automation with Playwright browser:
  1. Login to portal ✓
  2. Navigate to Sign-in Sheets menu ✓
  3. Click Online Sign-in Sheets ✓
  4. Click Load button ✓
  5. Extract employee entries from table ✓
  6. Match names against Hodler Inn records ✓
  7. Fill Employee ID + Room Number for matches ✓
  8. Mark "No Bill" for non-matches ✓ (Fixed March 1, 2026)
- Sync Status tracking with results history
- Telegram notifications for sync results
- Fuzzy name matching algorithm (handles LASTNAME/FIRSTNAME/SUFFIX format)

### No Bill Checkbox Fix (March 1, 2026):
- Updated selector logic to find "No Bill" checkbox using multiple strategies:
  1. Direct ID/name selector (`input[type="checkbox"][id*="noBill"]`)
  2. Cell text matching (looks for cell containing "No Bill" text)
  3. Positional fallback (second checkbox in row is typically "No Bill")
- Added click-based interaction instead of just `.check()` for better compatibility
- Added verification step to confirm checkbox was actually checked
- Improved logging for debugging

### Auto-Sync Feature:
- Toggle ON/OFF from Portal Settings
- Runs daily at **3 PM** (when portal shows previous day's records)
- Shows next scheduled sync time in UI
- Sends Telegram notification with results
- Persists setting across server restarts

### Technical Details:
- Uses Playwright for headless browser automation
- Chromium browser installed for ARM64 architecture
- APScheduler for scheduled tasks
- Async background task execution
- Login URL: https://providerrail.apps-apiglobalsolutions.com/ACESSUPPLIER/faces/login.xhtml
- Sign-in Sheet URL: /faces/views/viewSignInSheet.xhtml

### Business Logic:
- **Best time to run sync:** 3 PM daily (auto-sync default)
- Portal shows **previous day's records** by default
- Example: Running Feb 28 at 3 PM → Verifies Feb 27 guest stays

### Results Tracking:
- **Verified:** Records matched with Hodler Inn data (Employee ID + Room filled)
- **No Bill:** Portal records with no matching Hodler Inn guest (checkbox marked)
- **Missing:** Hodler Inn guests not found in portal (needs manual review)

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

## Updates (March 1, 2026)

### Auto-Sync Schedule
- Auto-sync starts **March 2nd, 2026 at 3 PM**
- Runs daily at 3 PM to verify previous day's records

### Room Number Validation
- Guests can only enter room numbers from Room Management list
- Invalid rooms rejected with error message

### Check-Out Verification
- Guests must verify Room + Employee ID before checkout
- Prevents accidental wrong checkout

### Voice Messages System
- Check-In: "Welcome to Hodler Inn. Have a good rest."
- Check-Out: "Thank you for staying. Have a safe journey. Please drop your room key in the key drop box in the lounge."
- Time-based greetings (morning/afternoon/evening/night)
- Uses pre-generated MP3 audio files for reliable playback on kiosk browsers

### Voice Control (Admin Settings)
- Enable/disable voice toggle
- Volume slider (0-100%)
- Test voice button

### Signature Requirement
- Visual warning about proper signature
- Voice reminder when guest starts signing
- No validation - easy check-in maintained

### Success Screens
- Animated checkmark
- Key drop reminder on checkout
- Auto-return to menu

### Auto-Navigation Feature (March 1, 2026) ✅ NEW
- **Clean UI:** All instructional text removed from guest portal (relies on voice prompts)
- **Auto-focus flow for Check-In:**
  1. After employee verification → Focus automatically moves to Room Number input
  2. After entering room number (3+ digits) → Focus moves to Time input
  3. After selecting time → Page scrolls to Signature canvas + voice reminder plays
- Uses `useRef` hooks for smooth focus transitions
- Enhances kiosk experience with minimal user effort

## Simplified Check-In Flow (March 2, 2026)
**Status:** ✅ IMPLEMENTED!

### Changes Made:
- **Single Page Check-In:** All fields visible on one page (no separate verify step)
- **Auto-Verify:** Name auto-populates as user types employee number (500ms debounce)
- **Visual Status Indicators:**
  - Green border: Employee found, "Welcome back!" message
  - Amber border: New guest (in admin list, not registered), "Register as [Name]" button
  - Red border: Employee not found, name input + "Request Access from Admin" button
- **Telegram Approval System:** Unknown employees can request access with inline Approve/Reject buttons
- **Removed Friction:** No separate "Verify" or "Continue" buttons needed

### Telegram Approval Flow:
1. Employee enters ID (not found) → Enters their name → Taps "Request Access"
2. Admin receives Telegram notification with:
   - Employee Name
   - Employee ID
   - **✅ Approve** and **❌ Reject** buttons
3. Admin taps **Approve** → Employee automatically added to system
4. Employee can now check in immediately!

### API Endpoints:
- `POST /api/request-employee-access` - Submit access request (name + ID)
- `POST /api/telegram-webhook` - Handle Telegram button clicks
- `GET /api/pending-access-requests` - View pending requests (for admin)

## Employee Collection AI Agent (March 2026)
**Status:** ✅ FULLY FUNCTIONAL!

### Features Implemented:
- **Import from Portal Button** in Admin Employee Management panel
- Navigates to Sign-in Report section (not Online Sign-in Sheets)
- Iterates through multiple billing periods (up to 6 months of historical data)
- Clicks "View Details" for each day to access individual employee records
- Extracts Crew ID and Crew Name from detail tables
- Formats names from portal format (LASTNAME/FIRSTNAME/SUFFIX) to readable format (Firstname Lastname)
- Imports unique employees to database with `source: "portal_import"` marker
- Successfully imported 63 employees in first run

### Technical Details:
- Located in `backend/sync_agent.py` → `collect_employees_from_portal()` function
- API Endpoint: POST `/api/admin/collect-employees`
- Uses Playwright for headless browser automation
- Handles navigation between billing periods with re-navigation to Sign-in Report page
- Robust column detection (finds CrewId and Crew Name columns dynamically)
- Validates employee IDs (alphanumeric, <=15 chars, no metadata like "Hotel:", "City:")

### Results:
- Total employees imported: 63 (from 6 months of data)
- Import time: ~2-3 minutes (depending on data volume)
- Duplicate detection: Skips employees already in database

## Public API Access (March 2, 2026)
**Status:** ✅ IMPLEMENTED!

### Features:
- **API Key Authentication:** Secure access via configurable API key in Admin Settings
- **Sign-in Sheets Endpoint:** `GET /api/public/signin-sheets?api_key=YOUR_KEY`
- **Billing Report Endpoint:** `GET /api/public/billing-report?api_key=YOUR_KEY`
- **Date Range Filtering:** Optional `start_date` and `end_date` query parameters
- **Multiple Formats:** JSON (default) or CSV (`format=csv`)
- **Generate Secure Key Button:** Creates random 32-character keys with `hinn_` prefix
- **API Documentation Panel:** Shows full URLs, copy buttons, and quick test links in Admin Dashboard

### Admin Dashboard Features:
- API Key field with "Generate" button for secure random keys
- "Copy All" button - copies complete API documentation text
- Clickable endpoints - copies full URL with API key
- Quick Test Links - opens JSON/CSV directly in browser
- Copy buttons for Base URL and API Key

### API Usage Examples:
```bash
# JSON format
curl "https://your-domain/api/public/signin-sheets?api_key=YOUR_KEY"
curl "https://your-domain/api/public/billing-report?api_key=YOUR_KEY"

# CSV format
curl "https://your-domain/api/public/signin-sheets?api_key=YOUR_KEY&format=csv"

# With date filtering
curl "https://your-domain/api/public/billing-report?api_key=YOUR_KEY&start_date=2026-03-01&end_date=2026-03-31"
```

### Security:
- API key stored in settings, manageable from Admin Dashboard
- Invalid/missing API key returns 401/403 errors
- All endpoints require valid API key
- Generated keys use cryptographically secure random characters

## Next Tasks
1. ~~**AI Verification Agent Selector Fix**~~ ✅ Completed - Updated CSS selector logic
2. ~~**Employee Collection AI Agent**~~ ✅ Completed - March 2, 2026
3. ~~**Public API Access**~~ ✅ Completed - March 2, 2026
4. **Elox Smart Lock Integration** - Pending call on Monday to check if web portal exists
5. UnlockOS Smart Lock Integration (saved for later)
6. Email notifications on check-in/out
7. Room availability calendar view
8. Blockchain integration (saved for later)
9. AI Phone Bot (saved for later)
