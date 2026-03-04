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
- **Database:** MongoDB
- **Automation:** Playwright for web scraping

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

### In Progress 🔄
- [ ] User verification of recent features

### Backlog/Future Tasks 📋
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

## Key Files
- `/app/backend/sync_agent.py` - AI Sync Agent (Playwright automation)
- `/app/backend/server.py` - FastAPI backend (monolithic, needs refactoring)
- `/app/frontend/src/pages/AdminDashboard.jsx` - Admin UI (needs decomposition)
- `/app/frontend/src/pages/GuestPortal.jsx` - Guest check-in/out portal

## Admin Credentials
- Admin access: `/admin` with password `hodlerinn2024`
