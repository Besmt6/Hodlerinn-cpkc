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
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    location /api {
        proxy_pass http://localhost:8001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

Enable and get SSL:
```bash
sudo ln -s /etc/nginx/sites-available/hodlerinn /etc/nginx/sites-enabled/
sudo certbot --nginx -d your-domain.com
sudo systemctl restart nginx
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
