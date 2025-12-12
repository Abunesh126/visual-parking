# 🚀 Deployment Guide - Mall Parking System

This guide covers deploying the Mall Parking System to production environments.

## 📋 Production Requirements

### **Minimum System Requirements**
- **CPU**: 4+ cores (8+ recommended for CV processing)
- **RAM**: 8GB minimum (16GB+ recommended with GPU)
- **Storage**: 100GB+ SSD for database and logs
- **Network**: 1Gbps for camera streaming
- **GPU**: NVIDIA GPU with 4GB+ VRAM (optional but recommended)

### **Software Prerequisites**
- **OS**: Ubuntu 20.04+ / CentOS 8+ / Windows Server 2019+
- **Python**: 3.8-3.11
- **Node.js**: 16.x LTS or 18.x LTS
- **Database**: MySQL 8.0+ or MariaDB 10.6+
- **Web Server**: Nginx or Apache (for frontend)
- **Process Manager**: PM2, systemd, or Docker

## 🐳 Docker Deployment (Recommended)

### **1. Create Docker Compose Configuration**

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  # Database
  mysql:
    image: mysql:8.0
    environment:
      MYSQL_ROOT_PASSWORD: ${DB_ROOT_PASSWORD}
      MYSQL_DATABASE: mall_parking_db
      MYSQL_USER: parking_user
      MYSQL_PASSWORD: ${DB_PASSWORD}
    ports:
      - "3306:3306"
    volumes:
      - mysql_data:/var/lib/mysql
      - ./sql/init.sql:/docker-entrypoint-initdb.d/init.sql
    restart: unless-stopped
    networks:
      - parking_network

  # Backend API
  backend:
    build:
      context: ./parking-backend
      dockerfile: Dockerfile.prod
    environment:
      DATABASE_URL: mysql://parking_user:${DB_PASSWORD}@mysql:3306/mall_parking_db
      ENVIRONMENT: production
      CV_ENABLED: "true"
    ports:
      - "8000:8000"
    depends_on:
      - mysql
    restart: unless-stopped
    volumes:
      - ./logs:/app/logs
      - ./camera_feeds:/app/camera_feeds
    networks:
      - parking_network

  # Frontend Dashboard
  frontend:
    build:
      context: ./dashboard
      dockerfile: Dockerfile.prod
    ports:
      - "80:80"
      - "443:443"
    environment:
      REACT_APP_API_URL: https://api.parking.yourdomain.com
    depends_on:
      - backend
    restart: unless-stopped
    volumes:
      - ./ssl:/etc/nginx/ssl:ro
    networks:
      - parking_network

  # Redis for caching and real-time updates
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    restart: unless-stopped
    volumes:
      - redis_data:/data
    networks:
      - parking_network

volumes:
  mysql_data:
  redis_data:

networks:
  parking_network:
    driver: bridge
```

### **2. Create Production Dockerfiles**

**Backend Dockerfile (parking-backend/Dockerfile.prod):**
```dockerfile
FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libffi-dev \
    libssl-dev \
    libmysqlclient-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Start application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Frontend Dockerfile (dashboard/Dockerfile.prod):**
```dockerfile
# Build stage
FROM node:18-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production

COPY . .
RUN npm run build

# Production stage
FROM nginx:alpine

# Copy built app
COPY --from=builder /app/build /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.prod.conf /etc/nginx/nginx.conf

# Expose ports
EXPOSE 80 443

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
```

### **3. Deploy with Docker Compose**

```bash
# Create environment file
cat << EOF > .env
DB_ROOT_PASSWORD=secure_root_password_here
DB_PASSWORD=secure_user_password_here
EOF

# Start services
docker-compose -f docker-compose.prod.yml up -d

# Check status
docker-compose -f docker-compose.prod.yml ps

# View logs
docker-compose -f docker-compose.prod.yml logs -f backend
```

## 🖥️ Manual Deployment (Traditional)

### **1. Backend Deployment**

```bash
# Create application user
sudo useradd -m -s /bin/bash parking
sudo usermod -aG docker parking

# Create application directory
sudo mkdir -p /opt/parking-system
sudo chown parking:parking /opt/parking-system

# Switch to application user
sudo su - parking
cd /opt/parking-system

# Clone and setup
git clone <your-repo> .
cd parking-backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create configuration
cat << EOF > .env
DATABASE_URL=mysql://parking_user:password@localhost:3306/mall_parking_db
ENVIRONMENT=production
CV_ENABLED=true
EOF

# Initialize database
python app/init_db.py
```

### **2. Create Systemd Service**

```ini
# /etc/systemd/system/parking-backend.service
[Unit]
Description=Mall Parking System Backend
After=network.target mysql.service

[Service]
Type=simple
User=parking
Group=parking
WorkingDirectory=/opt/parking-system/parking-backend
Environment=PATH=/opt/parking-system/parking-backend/venv/bin
ExecStart=/opt/parking-system/parking-backend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable parking-backend
sudo systemctl start parking-backend
sudo systemctl status parking-backend
```

### **3. Frontend Deployment with Nginx**

```bash
# Build frontend
cd /opt/parking-system/dashboard
npm install
npm run build

# Copy to web directory
sudo cp -r build/* /var/www/parking-dashboard/
```

**Nginx Configuration:**
```nginx
# /etc/nginx/sites-available/parking-system
server {
    listen 80;
    listen [::]:80;
    server_name parking.yourdomain.com;
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name parking.yourdomain.com;

    # SSL Configuration
    ssl_certificate /etc/ssl/certs/parking.yourdomain.com.pem;
    ssl_certificate_key /etc/ssl/private/parking.yourdomain.com.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;

    # Frontend
    location / {
        root /var/www/parking-dashboard;
        index index.html;
        try_files $uri $uri/ /index.html;
    }

    # API Proxy
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }

    # WebSocket support for real-time updates
    location /ws {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "Upgrade";
        proxy_set_header Host $host;
    }
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/parking-system /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## 🗄️ Database Configuration

### **1. Production MySQL Setup**

```sql
-- Create optimized database
CREATE DATABASE mall_parking_db 
    CHARACTER SET utf8mb4 
    COLLATE utf8mb4_unicode_ci;

-- Create user with limited privileges
CREATE USER 'parking_user'@'localhost' IDENTIFIED BY 'secure_password_here';
CREATE USER 'parking_user'@'%' IDENTIFIED BY 'secure_password_here';

GRANT SELECT, INSERT, UPDATE, DELETE ON mall_parking_db.* TO 'parking_user'@'localhost';
GRANT SELECT, INSERT, UPDATE, DELETE ON mall_parking_db.* TO 'parking_user'@'%';

FLUSH PRIVILEGES;
```

### **2. Database Optimizations**

```sql
-- Add performance indexes
ALTER TABLE slots ADD INDEX idx_vehicle_type_occupied (vehicle_type, is_occupied);
ALTER TABLE tickets ADD INDEX idx_entry_time_plate (entry_time, plate_number);
ALTER TABLE tickets ADD INDEX idx_active_tickets (exit_time) WHERE exit_time IS NULL;
ALTER TABLE event_logs ADD INDEX idx_timestamp_type (timestamp, event_type);

-- Configure MySQL for production
-- Add to /etc/mysql/mysql.conf.d/mysqld.cnf:
[mysqld]
innodb_buffer_pool_size = 2G
innodb_log_file_size = 256M
innodb_flush_log_at_trx_commit = 2
query_cache_size = 128M
max_connections = 500
```

## 🔒 Security Configuration

### **1. Firewall Setup**

```bash
# Allow only necessary ports
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow from 192.168.0.0/16 to any port 3306  # Database access
sudo ufw enable
```

### **2. SSL/TLS Setup**

```bash
# Using Let's Encrypt
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d parking.yourdomain.com

# Or use your own certificates
sudo mkdir -p /etc/ssl/{certs,private}
sudo cp your-cert.pem /etc/ssl/certs/parking.yourdomain.com.pem
sudo cp your-key.key /etc/ssl/private/parking.yourdomain.com.key
sudo chmod 644 /etc/ssl/certs/parking.yourdomain.com.pem
sudo chmod 600 /etc/ssl/private/parking.yourdomain.com.key
```

### **3. Application Security**

**Backend Security Settings:**
```python
# app/core/config.py
import secrets

class Settings:
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    CORS_ORIGINS: List[str] = ["https://parking.yourdomain.com"]
    ALLOWED_HOSTS: List[str] = ["parking.yourdomain.com", "localhost"]
```

## 📊 Monitoring & Logging

### **1. Application Monitoring**

**Install monitoring tools:**
```bash
# Prometheus + Grafana
docker run -d --name prometheus -p 9090:9090 prom/prometheus
docker run -d --name grafana -p 3001:3000 grafana/grafana
```

**Backend metrics endpoint:**
```python
# Add to app/main.py
from prometheus_client import Counter, Histogram, generate_latest

entry_events = Counter('parking_entries_total', 'Total entry events')
response_time = Histogram('http_request_duration_seconds', 'HTTP request duration')

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type="text/plain")
```

### **2. Log Management**

```bash
# Configure log rotation
sudo cat << EOF > /etc/logrotate.d/parking-system
/opt/parking-system/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 0644 parking parking
    postrotate
        systemctl reload parking-backend
    endscript
}
EOF
```

**Application logging configuration:**
```python
# app/core/logging.py
import logging
from logging.handlers import RotatingFileHandler

def setup_logging():
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # File handler
    file_handler = RotatingFileHandler(
        'logs/parking_system.log',
        maxBytes=50*1024*1024,  # 50MB
        backupCount=10
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)
    
    # Root logger
    logging.basicConfig(
        level=logging.INFO,
        handlers=[file_handler, console_handler]
    )
```

## 🔄 Backup & Recovery

### **1. Automated Database Backup**

```bash
#!/bin/bash
# /opt/parking-system/scripts/backup-db.sh

BACKUP_DIR="/opt/backups/parking-system"
DATE=$(date +%Y%m%d_%H%M%S)
DB_NAME="mall_parking_db"

mkdir -p $BACKUP_DIR

# Create backup
mysqldump -u parking_user -p$DB_PASSWORD \
    --single-transaction \
    --routines \
    --triggers \
    $DB_NAME | gzip > $BACKUP_DIR/parking_db_$DATE.sql.gz

# Keep only last 30 days of backups
find $BACKUP_DIR -name "parking_db_*.sql.gz" -mtime +30 -delete

echo "Backup completed: parking_db_$DATE.sql.gz"
```

**Add to crontab:**
```bash
# Daily backup at 2 AM
0 2 * * * /opt/parking-system/scripts/backup-db.sh
```

### **2. Application Backup**

```bash
#!/bin/bash
# Backup application files and configuration
tar -czf /opt/backups/parking-system/app_backup_$(date +%Y%m%d).tar.gz \
    /opt/parking-system \
    /etc/nginx/sites-available/parking-system \
    /etc/systemd/system/parking-backend.service
```

## 🚀 Performance Optimization

### **1. Database Performance**

```sql
-- Optimize for read-heavy workload
SET GLOBAL innodb_buffer_pool_size = 2147483648;  -- 2GB
SET GLOBAL query_cache_size = 134217728;          -- 128MB
SET GLOBAL max_connections = 500;

-- Create materialized view for dashboard
CREATE VIEW parking_summary AS
SELECT 
    f.name as floor_name,
    COUNT(s.id) as total_slots,
    SUM(CASE WHEN s.is_occupied THEN 1 ELSE 0 END) as occupied_slots,
    SUM(CASE WHEN s.vehicle_type = 'CAR' THEN 1 ELSE 0 END) as car_slots,
    SUM(CASE WHEN s.vehicle_type = 'BIKE' THEN 1 ELSE 0 END) as bike_slots
FROM floors f
LEFT JOIN slots s ON f.id = s.floor_id
GROUP BY f.id, f.name;
```

### **2. API Performance**

```python
# Add Redis caching
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend

@app.on_event("startup")
async def startup():
    redis = aioredis.from_url("redis://localhost", encoding="utf8", decode_responses=True)
    FastAPICache.init(RedisBackend(redis), prefix="parking-cache")

# Cache parking availability
@app.get("/api/v1/parking-availability")
@cache(expire=30)  # Cache for 30 seconds
async def get_parking_availability():
    # ... implementation
```

### **3. Frontend Performance**

```javascript
// Code splitting and lazy loading
const Dashboard = lazy(() => import('./pages/Dashboard'));
const FloorView = lazy(() => import('./pages/FloorView'));

// Service Worker for caching
// public/sw.js
const CACHE_NAME = 'parking-dashboard-v1';
const urlsToCache = [
  '/',
  '/static/js/bundle.js',
  '/static/css/main.css',
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(urlsToCache))
  );
});
```

## 📋 Health Checks & Monitoring

### **1. Automated Health Checks**

```bash
#!/bin/bash
# /opt/parking-system/scripts/health-check.sh

API_URL="https://parking.yourdomain.com/api/v1/health"
WEBHOOK_URL="your-slack-webhook-url"

response=$(curl -s -w "%{http_code}" -o /dev/null "$API_URL")

if [ "$response" != "200" ]; then
    curl -X POST -H 'Content-type: application/json' \
        --data '{"text":"🚨 Parking System Health Check Failed! HTTP: '$response'"}' \
        "$WEBHOOK_URL"
fi
```

### **2. System Monitoring**

```yaml
# docker-compose.monitoring.yml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3001:3000"
    environment:
      GF_SECURITY_ADMIN_PASSWORD: admin
    volumes:
      - grafana_data:/var/lib/grafana
      - ./grafana/dashboards:/var/lib/grafana/dashboards

volumes:
  prometheus_data:
  grafana_data:
```

## 🎯 Deployment Checklist

### **Pre-Deployment**
- [ ] Database is created and configured
- [ ] SSL certificates are installed
- [ ] Environment variables are set
- [ ] Firewall rules are configured
- [ ] Backup system is set up
- [ ] Monitoring is configured

### **Deployment**
- [ ] Code is deployed to production server
- [ ] Database schema is migrated
- [ ] Services are started and enabled
- [ ] Health checks pass
- [ ] Frontend is accessible
- [ ] API endpoints respond correctly

### **Post-Deployment**
- [ ] Monitor system resources
- [ ] Check application logs
- [ ] Verify real-time updates work
- [ ] Test camera integrations
- [ ] Confirm backup jobs run
- [ ] Load test the system

---

**🎉 Congratulations! Your Mall Parking System is now deployed to production!**

For support, monitoring, and maintenance, refer to the main README.md and system logs.