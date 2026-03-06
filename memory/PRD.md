# Hodler Inn - Product Requirements Document

## Original Problem Statement
Build a two-part application, "Hodler Inn," with a guest portal and an admin backend for managing railroad crew accommodations.

### Guest Portal Requirements
1. Unified check-in flow for new and returning guests
2. Guests can check in even if not on pre-approved employee list (marked "pending verification")
3. Guests check out by entering room number
4. Voice guidance and visual feedback
5. "How to Use" section with video tutorial

### Admin Backend Requirements
1. Dashboard for guest activity reporting
2. Billing and reporting features (Excel, PNG, PDF) with record editing
3. Full CRUD for employee management, including bulk import
4. AI agent to scrape historical data from third-party railroad portal
5. AI daily sync agent to verify stays against railroad portal
6. Telegram notifications for check-ins
7. Bulk verification system for pending guests
8. Employee name auto-update to match portal format
9. AI Phone Agent for wake-up calls
10. Automatic daily data backups
11. Automatic "sold out" email notifications
12. Room management (blocking, cleaning status)
13. "Guarantee Report" for tracking unused guaranteed rooms

## Technology Stack
- **Frontend:** React, Tailwind CSS, Shadcn UI
- **Backend:** FastAPI, pymongo, apscheduler
- **Database:** MongoDB Atlas (shared cloud database)
- **Automation:** Playwright for web scraping

## Deployment Architecture
- **Production Domain:** cpkc.hodlerinn.com → Points to **Emergent** (this is what guests use!)
- **Emergent Preview:** hodler-preview.preview.emergentagent.com
- **AWS Backup Server:** 3.149.0.151 (EC2 instance, for testing/backup only)
- **Database:** Both Emergent and AWS connect to the same MongoDB Atlas cluster (shared data)

## AWS Account Details
- **Account ID:** 3051-3786-5409
- **Account Name:** Hodlerinn
- **Region:** US East (Ohio) - us-east-2
- **Credits:** $100 USD (expires September 5, 2026)
- **Instance IP:** 3.149.0.151

## Key Database Schema
- `guests`: `{ employee_number, name, room_number, check_in, check_out }`
- `employees`: `{ employee_number, name }`
- `settings`: `{ email_settings, telegram_chat_id, auto_sync_start_date }`
- `hodler_inn_state`: `{ key: 'sold_out_status', value: { was_sold_out: bool } }`
- `turned_away_guests`: `{ date, guest_name, bed_type, price, reason, notes }`
- `name_aliases`: `{ portal_name, employee_number }`

## Third-Party Integrations
1. **API Global Solutions - Provider Rail Portal** - Playwright automation for guest verification
2. **OpenAI TTS-1** - Voice guidance on guest portal
3. **Telegram** - Admin notifications
4. **Zoho WorkDrive** - Daily backups

## Implementation Status

### Completed Features ✅
- [x] Guest Portal with voice guidance and visual feedback
- [x] Admin Dashboard with guest activity reporting
- [x] Employee CRUD with bulk import
- [x] Billing reports (Excel, PNG, PDF)
- [x] Telegram notifications
- [x] Room management and cleaning status
- [x] Guarantee Report with turned away guests logging
- [x] "Room Available" and "Heads Up" email notifications
- [x] Guest verification (Block/Remove unverified guests)
- [x] Date filtering on billing exports
- [x] Zoho WorkDrive backup integration
- [x] **AI Sync Agent** - Fixed date picker interaction and error handling (March 4, 2026)

### Recently Fixed (March 5, 2026)
- [x] **AI Sync Agent Classification Bug (P0)** - Fixed logic where matched entries weren't being counted as "Verified"
  - Entries already verified on portal + matching Hodler record are now counted
  - Entries where verify_entry fails but name match is confirmed are still counted
  - Version updated to 2026-03-05-v4
- [x] **Nights Billed Calculation Bug (P1)** - Changed from calendar-day based to 24-hour period based
  - Now uses `math.ceil(hours/24)` for accurate billing
  - 28-hour stay = 2 nights (was incorrectly showing 1 night)
- [x] **Sync Status Dashboard Card** - Added prominent sync status indicator to main dashboard
  - Shows breakdown: Verified (green), No Bill (amber), Missing (blue), Errors (red)
  - Shows timestamp of last sync
  - Placeholder message when no sync has been run

### Completed (December 2025)
- [x] **Per-Recipient Email Alerts** - Admins can now customize which alerts (Sold Out, Rooms Available, Low Availability, Daily Status) each email recipient receives
  - New table UI showing recipients with individual alert toggles
  - Backend APIs updated to support per-recipient preferences
  - Backwards compatible with old string format
  - Master toggles preserved for global on/off control

### In Progress 🔄
- [ ] User verification of sync agent fix (recommend running a manual sync to confirm)
- [ ] User verification of billing calculation on real stays
- [ ] User verification of Employee Import (v2) via "Import from Portal" button

### Backlog/Future Tasks 📋
- [ ] **P0:** Verify Auto-Sync v11 results (EWING, HOLLEY test case)
- [ ] **P1:** AI Phone Agent (blocked - waiting on Virtual PBX provider info)
- [ ] **P2:** Smart Lock Integration (blocked - waiting on vendor API info)
- [ ] **P2:** Code Refactoring (decompose `server.py` and `AdminDashboard.jsx`)
- [ ] **P2:** White-Label SaaS Version
- [ ] **P2:** Blockchain Integration for immutable ledger

## Key API Endpoints
- `/api/admin/sync/test-date-picker` - Diagnostic: Test date picker interaction
- `/api/admin/sync/count-entries` - Diagnostic: Count portal entries
- `/api/admin/sync/run` - Run full sync
- `/api/admin/turned-away-guests` - CRUD for turned away guests
- `/api/guests/unverified/block` - Block pending guest
- `/api/guests/unverified/remove` - Remove pending guest
- `/api/admin/export-billing/excel` - Export billing (supports date range)
- `/api/admin/email-alerts/settings` - GET/POST email alert settings
- `/api/admin/email-alerts/recipients/add` - Add email recipient
- `/api/admin/email-alerts/recipients` - DELETE email recipient
- `/api/admin/email-alerts/recipients/alerts` - PUT update per-recipient alerts

## Key Files
- `/app/backend/sync_agent.py` - AI Sync Agent (Playwright automation)
- `/app/backend/server.py` - FastAPI backend (monolithic, needs refactoring)
- `/app/frontend/src/pages/AdminDashboard.jsx` - Admin UI (needs decomposition)
- `/app/frontend/src/pages/GuestPortal.jsx` - Guest check-in/out portal

## Admin Credentials
- Admin access: `/admin` with password `hodlerinn2024`
