# Hodler Inn - Product Requirements Document

## Original Problem Statement
Build a two-part application, "Hodler Inn," with a guest portal and an admin backend for managing railroad crew hotel stays.

### Guest Portal Requirements
1. Unified check-in flow for new and returning guests
2. Guests can check in even if not on pre-approved employee list (marked as "pending verification")
3. Guests check out by entering their room number
4. Voice guidance and visual feedback
5. "How to Use" section with video tutorial

### Admin Backend Requirements
1. Dashboard for guest activity reporting
2. Billing and reporting features (Excel, PNG, PDF), with record editing
3. Full CRUD for employee management, including bulk import
4. AI agent to scrape historical data from third-party railroad portal
5. AI daily sync agent to verify stays against railroad portal
6. Telegram notifications for check-ins
7. Bulk verification system for pending guests
8. Employee names auto-update to match railroad portal format during sync
9. AI Phone Agent to handle wake-up calls from CPKC
10. Automatic daily data backups (to email or cloud storage)
11. Automatic "sold out" email notifications to the railroad company
12. Room management (blocking, dirty/clean status tracking)
13. "Guarantee Report" for unused guaranteed rooms

---

## What's Been Implemented

### Core Guest Portal (Completed)
- [x] Check-in flow with employee verification
- [x] Check-out flow by room number lookup
- [x] Unverified guest check-in with company name validation (CPKC only)
- [x] Voice guidance using OpenAI TTS-1 (configurable speed from admin)
- [x] Help page with video tutorial (Loom: b0647a5a59e34f42826cd2a16a5ab233)
- [x] Sign-in sheet view for guests (with In-House Only filter)
- [x] Kiosk mode / fullscreen support
- [x] Auto-idle reset to menu
- [x] Larger signature box (200px) with thicker pen strokes for tablet use
- [x] Security: "Call Help Phone" message after 2 wrong company name attempts
- [x] Audio management to prevent voice overlap/echo (audioPlaying flag)

### Admin Dashboard (Completed)
- [x] Employee management (CRUD)
- [x] Bulk employee import
- [x] Booking records management
- [x] Reporting (Excel, PNG, PDF export)
- [x] Guest verification section with bulk approve
- [x] Room management (dirty/clean status, room blocking)
- [x] Telegram notification settings (with test button)
- [x] Voice settings: Enable/disable, volume control, speed control (0.5-1.2)
- [x] Email settings for sold-out notifications
- [x] Zoho WorkDrive backup configuration
- [x] Guarantee Report page
- [x] Sign-in sheet with date picker and In-House Only filter
- [x] Auto-sync start date configuration

### AI Sync Agent (Completed)
- [x] Playwright automation for railroad portal
- [x] Automatic employee ID and room number entry
- [x] Skip already-verified entries (blue checkmark)
- [x] Auto-sync employee names to portal format
- [x] Scheduled daily sync at 3 PM Central
- [x] **NEW:** "Load More" pagination handling (up to 20 clicks)
- [x] **NEW:** Stricter name matching (first+last name, 0.85-0.9 threshold)

### Latest Updates (March 2026)
- [x] How to Use video updated to new Loom embed
- [x] Audio management overhaul to prevent voice echo/overlap
- [x] AI sync agent pagination ("Load More") and name matching fixes
- [x] Employee CRUD bug fixes (lookup by employee_number fallback)
- [x] Telegram test button added to admin panel
- [x] DatePicker component for calendar pop-up date selection
- [x] In-House Only filter on sign-in sheets
- [x] **Employee name sync to Guest Portal** - Admin employee name changes now sync to `guests` collection
- [x] **Room Available Alert** - Email notification when rooms become available after sold out
- [x] **Heads Up Notice** - Email notification when only 4 rooms available (low availability warning)
- [x] **Turned Away Guests Log** - Track guests turned away to honor CPKC room guarantee in Guarantee Report
- [x] **Zoho Backup Date Picker** - Select any date for manual backup upload with signatures
- [x] **Export Date Filtering** - All billing exports (Excel, PNG, PDF) support date range filtering
- [x] **Guest Block/Unblock** - Admin can block guests from checking in again
- [x] **Guest Remove** - Admin can remove unverified guests from system
- [x] **Second Check-in Prevention** - Unverified guests cannot check in twice

---

## Pending/In Progress

### P0 - Critical (User Verification Required)
- [ ] **Voice Echo/Overlap** - Code fix deployed, awaiting user testing on Fully Kiosk Browser
- [ ] **AI Sync Agent Accuracy** - Pagination and name matching fixes deployed, awaiting user testing against railroad portal

### P1 - High Priority
- [ ] **AI Phone Agent Implementation** - Blocked on Virtual PBX provider info
  - Requirements doc created: `/app/AI_Phone_Agent_Requirements.md`
  - Key tasks: PBX API integration, phone_name field, call routing logic

---

## Future/Backlog

### P2 - Medium Priority
- [ ] Smart Lock Integration (blocked on vendor API research)
- [ ] White-Label SaaS Version (multi-tenant)
- [ ] Blockchain Integration (immutable ledger)
- [ ] **Refactoring:** 
  - `server.py` (1600+ lines) → Split into routers
  - `AdminDashboard.jsx` (2000+ lines) → Split into components

---

## Technical Architecture

```
/app/
├── AI_Phone_Agent_Requirements.md
├── backend/
│   ├── .env
│   ├── requirements.txt
│   ├── server.py          # FastAPI endpoints (monolith, needs refactoring)
│   └── sync_agent.py      # Playwright portal automation with pagination
└── frontend/
    └── src/
        ├── components/
        │   ├── ui/
        │   │   ├── calendar.jsx
        │   │   └── popover.jsx
        │   └── DatePicker.jsx    # Reusable calendar date picker
        └── pages/
            ├── AdminDashboard.jsx  # Main admin UI (needs refactoring)
            └── GuestPortal.jsx     # Guest UI with audio management
```

### Tech Stack
- **Frontend:** React, Tailwind CSS, Shadcn/UI
- **Backend:** FastAPI, pymongo, apscheduler, playwright
- **Database:** MongoDB
- **Integrations:** OpenAI TTS-1, Telegram Bot, Zoho WorkDrive, Railroad Portal (Playwright)

### Key API Endpoints
- `/api/checkin` - Guest check-in
- `/api/checkout` - Guest check-out
- `/api/guests/register-pending` - Register unverified guest
- `/api/admin/guests/bulk-verify` - Bulk approve pending guests
- `/api/admin/sync/run` - Trigger AI sync agent
- `/api/admin/employees/{id}` - Employee CRUD (with employee_number fallback)
- `/api/admin/settings/telegram/test` - Test Telegram notification
- `/api/admin/settings/auto-sync-start-date` - Set sync start date
- `/api/voice-settings` - Get voice settings (enabled, volume, speed)
- `/api/voice-dynamic/{type}/{name}` - Dynamic TTS generation

### Key Database Collections
- `settings` - App configuration (voice, email, Zoho, Telegram, auto-sync)
- `employees` - Employee records (id, employee_number, name)
- `bookings` - Guest booking records
- `sync_history` - AI sync results log

---

## Credentials
- **Admin:** Access at `/admin` with password `hodlerinn2024`

---

## Critical Notes
- **Voice Audio:** Uses `audioPlaying` flag and `stopAllAudio()` to prevent overlap
- **AI Sync Agent:** Clicks "Load More" up to 20 times, uses strict first+last name matching
- **Company Validation:** Only "CPKC" (case-insensitive) allowed for new employee check-ins
- **Deployment:** Custom domain (`cpkc.hodlerinn.com`) may need re-linking after deploys
