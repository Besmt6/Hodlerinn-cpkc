# Hodler Inn - Easy Deployment Guide

## Quick Start (3 Commands!)

### Step 1: Install Docker on your server
```bash
# For Ubuntu/Debian
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
# Log out and log back in, then:
sudo apt install docker-compose -y
```

### Step 2: Clone your code
```bash
git clone https://github.com/Besmt6/Hodlerinn-cpkc.git
cd Hodlerinn-cpkc
```

### Step 3: Start everything
```bash
docker-compose up -d --build
```

That's it! Your app will be running at:
- Frontend: http://your-server-ip:3000
- Backend API: http://your-server-ip:8001

---

## For Production (with your domain)

### Update the frontend environment
Edit `docker-compose.yml` and change:
```yaml
environment:
  - REACT_APP_BACKEND_URL=https://your-domain.com
```

### Set up Nginx (for SSL/HTTPS)
```bash
sudo apt install nginx certbot python3-certbot-nginx -y
```

Create `/etc/nginx/sites-available/hodlerinn`:
```nginx
server {
    listen 80;
    server_name cpkc.hodlerinn.com;  # Change to your domain

    # API requests - proxy to backend
    location /api {
        proxy_pass http://localhost:8001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_cache_bypass $http_upgrade;
    }

    # Frontend - proxy to Node serve (handles SPA routing)
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_cache_bypass $http_upgrade;
    }
}
```

Enable and get SSL:
```bash
sudo ln -s /etc/nginx/sites-available/hodlerinn /etc/nginx/sites-enabled/
sudo nginx -t  # Test config
sudo certbot --nginx -d cpkc.hodlerinn.com
sudo systemctl restart nginx
```

---

## IMPORTANT: Fix for /book URL Issue

If `/book` URL redirects to `/` (guest portal), the issue is that `serve` 
isn't receiving the request properly. Make sure:

1. The frontend container is using `serve -s` (the -s flag handles SPA routing)
2. Nginx is correctly proxying ALL paths to the frontend

**Quick check:**
```bash
# Test if frontend handles /book directly
curl -I http://localhost:3000/book
# Should return: HTTP/1.1 200 OK

# Test through nginx
curl -I http://cpkc.hodlerinn.com/book
# Should also return: HTTP/1.1 200 OK
```

**If /book doesn't work, try rebuilding frontend:**
```bash
docker-compose up -d --build frontend
```

---

## Useful Commands

### View logs
```bash
docker-compose logs -f
```

### Restart services
```bash
docker-compose restart
```

### Stop everything
```bash
docker-compose down
```

### Update code and redeploy
```bash
git pull
docker-compose up -d --build
```

### Rebuild only frontend (after code changes)
```bash
docker-compose up -d --build frontend
```

### Rebuild only backend (after code changes)
```bash
docker-compose up -d --build backend
```

---

## AWS EC2 Quick Setup

1. Launch EC2 instance:
   - Ubuntu 22.04 LTS
   - t3.medium (recommended) or t3.small
   - 30GB storage
   - Security Group: Allow ports 22, 80, 443, 3000, 8001

2. SSH into your server:
```bash
ssh -i your-key.pem ubuntu@your-ec2-ip
```

3. Follow the "Quick Start" steps above!

---

## Environment Variables (backend/.env)

Make sure your backend/.env has all required keys:
```
MONGO_URL=mongodb://mongodb:27017
DB_NAME=hodler_inn
ADMIN_PASSWORD=hodlerinn2024
EMERGENT_LLM_KEY=sk-emergent-xxxxx
TELEGRAM_BOT_TOKEN=xxxxx
TELEGRAM_CHAT_ID=xxxxx
# ... other keys
```

---

## Troubleshooting

### Check if containers are running
```bash
docker ps
```

### Check container logs
```bash
docker logs hodlerinn-backend
docker logs hodlerinn-frontend
docker logs hodlerinn-mongodb
```

### Restart a specific service
```bash
docker-compose restart backend
```

### Check nginx config
```bash
sudo nginx -t
```

### Check nginx logs
```bash
sudo tail -f /var/log/nginx/error.log
```
