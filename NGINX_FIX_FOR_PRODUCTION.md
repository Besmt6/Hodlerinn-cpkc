# Nginx configuration fix for SPA (Single Page App) routing
# The issue: /book URL is being redirected to /
# 
# In your production nginx.conf or site config, make sure you have:

server {
    listen 80;
    server_name cpkc.hodlerinn.com;
    
    root /var/www/html;  # Or wherever your frontend build is
    index index.html;
    
    # CRITICAL: This is what makes React Router work
    # All frontend routes should serve index.html
    location / {
        try_files $uri $uri/ /index.html;
    }
    
    # API requests go to backend
    location /api {
        proxy_pass http://localhost:8001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}

# The key line is: try_files $uri $uri/ /index.html;
# This tells nginx: 
# 1. First try to serve the exact file requested
# 2. If not found, try as a directory
# 3. If still not found, serve index.html (which loads React app)
#
# Without this, /book returns 404 because there's no "book" file on disk

# ================================================
# If using Docker with nginx, your Dockerfile might need:
# ================================================
# COPY nginx.conf /etc/nginx/conf.d/default.conf
# Make sure nginx.conf has the try_files directive

