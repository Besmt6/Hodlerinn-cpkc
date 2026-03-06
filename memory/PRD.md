# Hodler Inn - Product Requirements Document

## Original Problem Statement
A comprehensive railroad crew accommodation management platform for Hodler Inn in Heavener, OK. The system handles guest check-ins, room management, billing, automated sync with railroad portals, and includes an AI-powered booking chatbot.

## Business Information
- **Address**: 820 US-59, Heavener, OK 74937
- **Property Type**: Railroad Crew Accommodation
- **Total Rooms**: 28
- **Railroad Partner**: CPKC (Canadian Pacific Kansas City)
- **Admin Password**: hodlerinn2024

## Core Features Implemented

### Guest Management
- [x] Guest Portal - Self-service kiosk for railroad crew
- [x] Employee ID verification
- [x] Digital signature capture
- [x] Check-in/Check-out flow
- [x] Voice guidance (OpenAI TTS)

### Admin Dashboard
- [x] Dashboard overview with stats
- [x] Sign-In Sheet view
- [x] Billing Report view
- [x] Room Management
- [x] Employee List management
- [x] Guest Verification
- [x] Guarantee Report
- [x] Portal Settings
- [x] **Documentation** (NEW - March 2025)

### Room Management
- [x] Room status tracking (clean/dirty)
- [x] Occupancy management
- [x] Other guests (non-railroad) booking
- [x] Reservations system
- [x] Auto-dirty marking (20 min after checkout)

### Billing & Reports
- [x] Automated billing calculation (24-hour periods)
- [x] Excel export
- [x] PDF export
- [x] PNG export
- [x] Guarantee report
- [x] Turned-away guests tracking

### Integrations
- [x] API Global railroad portal sync
- [x] Auto-sync at 3 PM Central
- [x] Telegram notifications
- [x] Email alerts (sold-out, available, heads-up, daily)
- [x] Per-recipient email alert preferences
- [x] Zoho WorkDrive backup
- [x] CPKC Email Scraper (expected arrivals)

### AI Features
- [x] **Bitsy Chatbot** - Conversational booking agent
- [x] Voice input support
- [x] Real-time availability
- [x] Dynamic pricing
- [x] Email confirmations
- [x] Telegram notifications to admin

### Demo Mode
- [x] Sandboxed demo environment
- [x] Separate demo database
- [x] Demo Guest Portal (/demo)
- [x] Demo Admin Panel (/demo/admin)
- [x] Sample data (EMP001, EMP002, EMP003)

### Documentation System (NEW)
- [x] Documentation page (/admin/docs)
- [x] Overview tab
- [x] Features tab
- [x] Demo Mode tab
- [x] Billing API tab
- [x] Bitsy Chatbot tab with embed code

## API Endpoints

### Public
- `GET /api/health` - Health check
- `POST /api/checkin` - Check in guest
- `POST /api/checkout` - Check out guest
- `GET /api/guests/{employee_number}` - Get guest info

### Admin - Billing
- `GET /api/admin/records` - Get all records
- `GET /api/admin/export-billing` - Export billing (Excel)
- `GET /api/admin/export-billing-pdf` - Export billing (PDF)
- `GET /api/admin/export-billing-png` - Export billing (PNG)
- `GET /api/admin/guarantee-report` - Guarantee report

### Admin - Rooms
- `GET /api/admin/rooms` - Get all rooms
- `POST /api/admin/rooms` - Create room
- `POST /api/admin/rooms/{number}/mark-dirty` - Mark dirty
- `POST /api/admin/rooms/{number}/mark-clean` - Mark clean
- `POST /api/admin/rooms/block` - Block for other guest

### Admin - Sync
- `GET /api/admin/sync/status` - Sync status
- `POST /api/admin/sync/run` - Run sync
- `GET /api/admin/settings` - Get settings
- `POST /api/admin/settings` - Update settings

### Chatbot
- `POST /api/chatbot/message` - Send message
- `GET /api/chatbot/availability` - Check availability
- `POST /api/chatbot/transcribe` - Voice to text

### Demo
- `POST /api/demo/init` - Initialize demo data
- `GET /api/demo/rooms` - Get demo rooms
- `GET /api/demo/guests` - Get demo guests

## Pending Verifications (P0)
1. Auto-Sync v11 Logic - User verification pending
2. Employee Import v2 - User verification pending
3. Voice Message Echo - User verification pending

## Upcoming Tasks (P1)
1. Deploy all features to production
2. AI Phone Agent (blocked on Virtual PBX info)
3. Smart Lock Integration (blocked on vendor API)

## Future/Backlog (P2-P3)
1. HODL Rewards Token system
2. Code refactoring (server.py ~6000+ lines, AdminDashboard.jsx ~5600+ lines)
3. White-Label SaaS Version

## Tech Stack
- **Frontend**: React, Tailwind CSS, Shadcn UI
- **Backend**: FastAPI, Motor (async MongoDB)
- **Database**: MongoDB Atlas
- **AI/LLM**: emergentintegrations (GPT-5.2)
- **Voice**: OpenAI TTS-1
- **Deployment**: Docker, AWS EC2

## File Structure
```
/app/
├── backend/
│   ├── server.py (main monolith)
│   ├── sync_agent.py
│   └── requirements.txt
└── frontend/
    └── src/
        ├── App.js
        └── pages/
            ├── AdminDashboard.jsx
            ├── GuestPortal.jsx
            ├── BookNow.jsx (Bitsy)
            ├── Documentation.jsx (NEW)
            ├── DemoPortal.jsx
            └── DemoAdmin.jsx
```

## Changelog
- **March 6, 2025**: Added comprehensive Documentation page with 5 tabs (Overview, Features, Demo Mode, Billing API, Bitsy Chatbot)
- **March 5, 2025**: Added Bitsy chatbot, Demo mode, CPKC email scraper, per-recipient alerts
- **March 4, 2025**: Auto-sync v11, email notifications, guarantee reports
