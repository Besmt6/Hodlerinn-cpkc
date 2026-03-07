# Hodler Inn - Hotel Management System

A comprehensive hotel management system for railroad crew accommodations, featuring AI-powered concierge, automated portal sync, and real-time notifications.

## Features

- **Guest Check-in/Check-out** - Kiosk interface for railroad crew
- **AI Concierge (Bitsy)** - Voice-enabled chatbot for guest assistance
- **Portal Sync** - Automated reconciliation with API Global Solutions
- **CPKC Email Processing** - Auto-import expected arrivals from email
- **Admin Dashboard** - Complete hotel operations management
- **Telegram Alerts** - Real-time notifications for staff
- **Phone Agent Webhook** - Integration for external phone systems

## Tech Stack

- **Backend:** FastAPI, Python 3.11, Playwright
- **Frontend:** React, Tailwind CSS, Shadcn/UI
- **Database:** MongoDB Atlas
- **AI:** OpenAI GPT-5.2, TTS-1
- **Infrastructure:** Docker, AWS

## Quick Start

### Prerequisites

- Docker & Docker Compose
- MongoDB Atlas account
- Environment variables configured

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/your-repo/hodlerinn.git
   cd hodlerinn
   ```

2. Create environment files:
   ```bash
   cp backend/.env.example backend/.env
   cp frontend/.env.example frontend/.env
   ```

3. Update `.env` files with your credentials

4. Start the application:
   ```bash
   docker-compose up -d --build
   ```

5. Access the application:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8001/api

## Environment Variables

### Backend (`backend/.env`)

| Variable | Description |
|----------|-------------|
| `MONGO_URL` | MongoDB Atlas connection string |
| `DB_NAME` | Database name |
| `ENCRYPTION_KEY` | Fernet encryption key |
| `ADMIN_PASSWORD` | Admin dashboard password |
| `TELEGRAM_BOT_TOKEN` | Telegram bot token |
| `TELEGRAM_CHAT_ID` | Telegram chat/group ID |
| `OPENAI_API_KEY` | OpenAI API key |
| `ZOHO_*` | Zoho integration credentials |

### Frontend (`frontend/.env`)

| Variable | Description |
|----------|-------------|
| `REACT_APP_BACKEND_URL` | Backend API URL |

## API Endpoints

### Public Webhooks

- `GET /api/webhook/guests` - Get checked-in guests (for phone systems)
- `GET /api/webhook/rooms/available` - Get available rooms
- `GET /api/health` - Health check

### Admin APIs

- `POST /api/admin/login` - Admin authentication
- `GET /api/admin/guests` - List all guests
- `GET /api/admin/bookings` - List all bookings
- `GET /api/admin/expected-arrivals` - CPKC expected arrivals
- `GET /api/admin/expected-checkouts` - CPKC expected checkouts

## Deployment

### Manual Deployment

```bash
# SSH into your server
ssh user@your-server

# Navigate to project
cd /path/to/hodlerinn

# Pull latest code
git pull origin main

# Rebuild and restart
docker-compose down
docker-compose up -d --build
```

### CI/CD (GitHub Actions)

The repository includes GitHub Actions workflows for automated deployment:

1. Add these secrets to your GitHub repository:
   - `EC2_HOST` - Your EC2 instance IP/hostname
   - `EC2_USERNAME` - SSH username
   - `EC2_SSH_KEY` - Private SSH key

2. Push to `main` branch to trigger deployment

## Project Structure

```
├── backend/
│   ├── server.py          # Main FastAPI application
│   ├── sync_agent.py      # Portal sync automation
│   ├── config.py          # Configuration
│   ├── database.py        # MongoDB connection
│   ├── security.py        # Encryption utilities
│   ├── models/            # Pydantic schemas
│   ├── routers/           # API route modules
│   ├── services/          # Business logic services
│   └── utils/             # Helper functions
├── frontend/
│   ├── src/
│   │   ├── pages/         # React pages
│   │   └── components/    # Reusable components
│   └── public/
├── docker-compose.yml
├── Dockerfile.backend
├── Dockerfile.frontend
└── nginx.conf
```

## License

Proprietary - Hodler Inn

## Support

For issues or questions, contact the development team.
