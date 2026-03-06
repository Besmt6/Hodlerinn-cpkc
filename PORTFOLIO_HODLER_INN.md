# Portfolio: Hodler Inn - Smart Hotel Management System

## Project Overview

**Hodler Inn** is a full-stack hotel management system designed specifically for railroad crew accommodations. The system automates guest check-in/check-out, billing verification, and integrates with third-party railroad portals for seamless operations.

**Role:** Product Owner & Solution Architect  
**Timeline:** March 2026  
**Status:** Live in Production

---

## Business Problem

Railroad companies contract with hotels to provide lodging for train crews. The existing process was:
- Manual paper sign-in sheets
- Time-consuming data entry into railroad portals
- Billing discrepancies and disputes
- No real-time visibility into occupancy
- Missed revenue from unverified stays

**Impact:** Hours of daily administrative work, billing errors, and lost revenue.

---

## Solution Delivered

### 1. Guest Self-Service Kiosk
- Touch-screen check-in/check-out portal
- Voice-guided instructions for guests
- Automatic room assignment
- Real-time availability display

### 2. AI-Powered Sync Agent
- Automated verification against railroad portal
- Intelligent name matching (handles variations like "SMITH,(JOHN)" vs "John Smith")
- Fills Employee ID and Room Number automatically
- Catches late arrivals across billing periods

### 3. Admin Dashboard
- Real-time occupancy tracking
- Billing reports (Excel, PDF, PNG export)
- Employee management with portal import
- Telegram notifications for check-ins

### 4. Smart Billing System
- 24-hour period-based billing (not calendar days)
- Automatic "Nights Billed" calculation
- Guarantee report for contracted rooms

### 5. Cloud Infrastructure
- Primary deployment on Emergent platform
- Backup deployment on AWS EC2
- Shared MongoDB Atlas database
- Zero-downtime failover capability

---

## Technical Achievements

| Challenge | Solution Implemented |
|-----------|---------------------|
| Name format variations | AI-powered name normalization and matching |
| Late arrival tracking | Multi-day portal scanning with date range support |
| Billing accuracy | Time-based calculation: ceil(hours/24) |
| Data redundancy | Dual-site deployment with shared cloud database |
| Portal automation | Playwright-based browser automation |
| Real-time sync | Background task processing with progress tracking |

---

## Key Features I Designed

1. **"Include Previous Day" Sync** - Catches guests who appear on different billing dates
2. **Blue Entry Detection** - Identifies already-verified entries and fills missing data
3. **Employee Date Range Scanner** - Bulk import employees from any date range
4. **Voice Pronunciation Fixes** - Custom TTS pronunciation for names like "Brian"
5. **Export/Import System** - One-click database backup and migration

---

## Results & Impact

- **Time Saved:** ~2 hours/day of manual data entry eliminated
- **Accuracy:** 95%+ automated billing verification
- **Visibility:** Real-time dashboard for all operations
- **Reliability:** Dual-site deployment with shared database
- **Scalability:** System handles 200+ employees, 100+ daily check-ins

---

## Skills Demonstrated

### Product & Business
- Requirements gathering and prioritization
- User experience design for non-technical users
- Business process optimization
- Stakeholder communication

### Technical Understanding
- Cloud infrastructure (AWS, MongoDB Atlas)
- API integrations and automation
- Database design and management
- Deployment and DevOps concepts

### Problem Solving
- Identified edge cases (late arrivals, name variations)
- Designed solutions for real-world scenarios
- Iterative improvement based on testing
- Debug and troubleshoot complex systems

---

## Technologies Used

| Category | Technologies |
|----------|-------------|
| Frontend | React, Tailwind CSS, Shadcn UI |
| Backend | Python, FastAPI |
| Database | MongoDB, MongoDB Atlas |
| Automation | Playwright (browser automation) |
| AI/ML | OpenAI TTS, LiteLLM |
| Infrastructure | Docker, AWS EC2, Kubernetes |
| Integrations | Telegram, Zoho WorkDrive |

---

## What I Learned

1. **Technical communication** - Translating business needs into technical requirements
2. **System thinking** - Understanding how components connect and affect each other
3. **Iterative development** - Building, testing, and improving in cycles
4. **Cloud architecture** - Multi-site deployment with shared databases
5. **Automation value** - How AI can eliminate repetitive manual work

---

## Contact

Ready to bring this problem-solving approach to your organization.

**Available for:**
- Product Manager roles
- Business Analyst positions
- Operations & Process Improvement
- Startup opportunities

---

*"The best solutions come from understanding real problems, not just technology."*
