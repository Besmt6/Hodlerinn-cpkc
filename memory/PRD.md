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
- [x] Documentation page

### Room Management
- [x] Room status tracking (clean/dirty)
- [x] Occupancy management
- [x] Other guests (non-railroad) booking
- [x] Reservations system with confirm/cancel
- [x] Auto-dirty marking (20 min after checkout)

### Billing & Reports
- [x] Automated billing calculation (24-hour periods)
- [x] Excel export
- [x] PDF export
- [x] PNG export
- [x] Guarantee report
- [x] Turned-away guests tracking

### AI Chatbot (Bitsy) - UPDATED March 6, 2025
- [x] Conversational booking flow
- [x] Voice greeting on page load ("I'm Bitsy, your hotel concierge...")
- [x] Voice responses (Bitsy speaks all replies)
- [x] Voice input with auto-stop (silence detection)
- [x] Voice on/off toggle button
- [x] Real-time availability checking
- [x] Dynamic pricing (single/double bed)
- [x] **Returning guest recognition** - skips name/email/phone for repeat guests
- [x] Email confirmations
- [x] Telegram notifications to admin

### Reservation Management - UPDATED March 6, 2025
- [x] Pending/Confirmed status tracking
- [x] **Confirm button** - Mark as phone confirmed
- [x] **Manual cancel** - Cancel confirmed reservations
- [x] Auto-cancel only applies to unconfirmed reservations
- [x] Telegram notifications for confirm/cancel

### Integrations
- [x] API Global railroad portal sync
- [x] Auto-sync at 3 PM Central
- [x] Telegram notifications
- [x] Email alerts (sold-out, available, heads-up, daily)
- [x] Per-recipient email alert preferences
- [x] Zoho WorkDrive backup
- [x] CPKC Email Scraper (expected arrivals)

### Demo Mode
- [x] Sandboxed demo environment
- [x] Separate demo database
- [x] Demo Guest Portal (/demo)
- [x] Demo Admin Panel (/demo/admin)
- [x] Sample data (EMP001, EMP002, EMP003)

## API Endpoints

### Chatbot
- `POST /api/chatbot/message` - Send message to chatbot
- `GET /api/chatbot/availability` - Check room availability
- `POST /api/chatbot/transcribe` - Voice to text (OpenAI Whisper)

### Reservations (NEW)
- `GET /api/admin/rooms/reservations` - Get all reservations
- `POST /api/admin/rooms/reservations/{id}/confirm` - Mark as confirmed
- `POST /api/admin/rooms/reservations/{id}/cancel` - Manual cancel
- `DELETE /api/admin/rooms/reservations/{id}` - Delete reservation

## Pending Verifications (P1)
1. Auto-Sync v11 Logic - User verification pending
2. Voice Message Echo - User verification pending

## Upcoming Tasks (P1)
1. Deploy all features to production
2. AI Phone Agent (blocked on phone company response)
3. Smart Lock Integration (blocked on vendor API)

## Future/Backlog (P2-P3)
1. HODL Rewards Token system
2. Code refactoring (server.py ~7900 lines, AdminDashboard.jsx ~5600 lines)
3. White-Label SaaS Version

## Tech Stack
- **Frontend**: React, Tailwind CSS, Shadcn UI
- **Backend**: FastAPI, Motor (async MongoDB)
- **Database**: MongoDB Atlas
- **AI/LLM**: emergentintegrations (GPT-5.2, Whisper)
- **Voice**: Web Speech API (TTS), OpenAI Whisper (STT)
- **Email Parsing**: pdfplumber, imaplib (Zoho IMAP)
- **Deployment**: Docker, Docker Compose, AWS EC2

## AWS Production Server
- **Server**: ubuntu@ip-172-31-9-167
- **Public IP**: 3.149.0.151
- **Production URL**: http://3.149.0.151:3000
- **Admin Dashboard**: http://3.149.0.151:3000/admin/dashboard
- **Project Folder**: `~/Hodlerinn-cpkc`
- **Docker Containers**:
  - `hodlerinn-frontend` (port 3000)
  - `hodlerinn-backend` (port 8001)
  - `hodlerinn-mongodb` (port 27017)
- **Deploy Commands**:
  ```bash
  cd ~/Hodlerinn-cpkc
  git pull origin main
  docker-compose down
  docker-compose up -d --build
  ```
- **Check Logs**: `docker logs hodlerinn-backend --tail 100`

## Changelog
- **March 6, 2025 (Session 3)**: 
  - **FIXED**: CPKC Email Scraper - scheduler async issue, IMAP enabled, PDF column mapping
  - **FIXED**: Import from Portal - rewrote to use Billing Period dropdown, 530 employees imported
  - **IMPROVED**: BookNow UI - removed duplicate rates, header shows "$79 + tax"
  - **IMPROVED**: Mobile voice - added "Tap to hear Bitsy" button, fixed response speech
  - **ADDED**: Policy notice with icons (Non-Smoking, No Pets) below chat input
- **March 6, 2025 (Session 2)**: 
  - Fixed Bitsy greeting ("I'm Bitsy" for both voice and text)
  - Added automatic silence detection for voice input
  - Added returning guest recognition
  - Added reservation confirm/cancel system with Status column
- **March 6, 2025 (Session 1)**: Added Documentation page with 5 tabs
- **March 5, 2025**: Added Bitsy chatbot, Demo mode, CPKC email scraper
