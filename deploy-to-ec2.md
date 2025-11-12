# Deploying to EC2 with docker-compose.prod.yml

## Prerequisites

1. **EC2 Instance Running** (Ubuntu 20.04+ or Amazon Linux 2)
2. **SSH Access** to your EC2 instance
3. **Domain/IP** of your EC2 instance
4. **Security Groups** configured:
   - Port 22 (SSH)
   - Port 80 (HTTP)
   - Port 443 (HTTPS)
   - Port 8000 (API Gateway - temporary, later use nginx)

---

## Step 1: Connect to EC2

```bash
# Replace with your key and EC2 IP
ssh -i ~/your-key.pem ubuntu@your-ec2-ip
# OR
ssh -i ~/your-key.pem ec2-user@your-ec2-ip  # For Amazon Linux
```

---

## Step 2: Install Docker & Docker Compose on EC2

```bash
# Update system
sudo apt-get update && sudo apt-get upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add your user to docker group (no need for sudo)
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.24.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Log out and back in for group changes to take effect
exit
# SSH back in
ssh -i ~/your-key.pem ubuntu@your-ec2-ip

# Verify installation
docker --version
docker-compose --version
```

---

## Step 3: Clone Your Repository on EC2

```bash
# Install git if not present
sudo apt-get install -y git

# Clone your repo
git clone https://github.com/PreciousEzeigbo/distributed-notification-system.git

# Navigate to project
cd distributed-notification-system
```

---

## Step 4: Configure Environment Variables

You have **two options**:

### Option A: Use Individual Service .env Files (Recommended)

```bash
# API Gateway
nano api-gateway/.env
```

Add:
```properties
DATABASE_URL=postgresql://gateway_service:CHANGE_THIS_PASSWORD@gateway-db:5432/gateway_service_db
REDIS_URL=redis://redis:6379/0
RABBITMQ_URL=amqp://admin:CHANGE_THIS_PASSWORD@rabbitmq:5672/
USER_SERVICE_URL=http://user-service-nestjs:3000
TEMPLATE_SERVICE_URL=http://template-service:3000
SECRET_KEY=CHANGE_THIS_TO_A_LONG_RANDOM_STRING_MIN_64_CHARS
RATE_LIMIT_PER_MINUTE=100
PORT=8000
```

```bash
# User Service
nano user-service-nestjs/.env
```

Add:
```properties
DB_HOST=user-db
DB_PORT=5432
DB_USER=user_service
DB_PASSWORD=CHANGE_THIS_PASSWORD
DB_NAME=user_service_db
RABBITMQ_URL=amqp://admin:CHANGE_THIS_PASSWORD@rabbitmq:5672/
PORT=3000
NODE_ENV=production
```

```bash
# Template Service
nano template-service/.env
```

Add:
```properties
DB_HOST=template-db
DB_PORT=5432
DB_USER=template_service
DB_PASSWORD=CHANGE_THIS_PASSWORD
DB_NAME=template_service_db
PORT=3000
NODE_ENV=production
```

```bash
# Email Service
nano email-service/.env
```

Add:
```properties
RABBITMQ_URL=amqp://admin:CHANGE_THIS_PASSWORD@rabbitmq:5672/
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM=noreply@yourapp.com
TEMPLATE_SERVICE_URL=http://template-service:3000
EMAIL_QUEUE=email.queue
MAX_RETRIES=3
```

```bash
# Push Service
nano push-service/.env
```

Add:
```properties
RABBITMQ_URL=amqp://admin:CHANGE_THIS_PASSWORD@rabbitmq:5672/
FCM_CREDENTIALS_FILE=/app/fcm-credentials.json
TEMPLATE_SERVICE_URL=http://template-service:3000
PUSH_QUEUE=push.queue
MAX_RETRIES=3
```

### Option B: Update docker-compose.prod.yml (Alternative)

```bash
nano docker-compose.prod.yml
```

Update passwords in the environment sections directly.

---

## Step 5: Update docker-compose.prod.yml Passwords

**IMPORTANT**: Change default passwords!

```bash
nano docker-compose.prod.yml
```

Find and update these:

```yaml
# PostgreSQL databases
POSTGRES_PASSWORD: CHANGE_THIS_PASSWORD  # Change all 3 databases

# RabbitMQ
RABBITMQ_DEFAULT_USER: admin
RABBITMQ_DEFAULT_PASS: CHANGE_THIS_PASSWORD  # Change this

# API Gateway
SECRET_KEY: CHANGE_THIS_TO_LONG_RANDOM_STRING  # Min 64 chars
```

Generate a secure SECRET_KEY:
```bash
openssl rand -base64 64
```

---

## Step 6: Deploy with Production Compose File

```bash
# Pull latest changes (if you made any)
git pull origin main

# Build and start all services in detached mode
docker-compose -f docker-compose.prod.yml up -d --build

# This will:
# 1. Build all service images
# 2. Start PostgreSQL databases
# 3. Start Redis and RabbitMQ
# 4. Start all microservices
# 5. Run in background (detached)
```

---

## Step 7: Verify Deployment

### Check Container Status

```bash
# View all running containers
docker-compose -f docker-compose.prod.yml ps

# All services should show "Up" and "healthy"
```

### Check Logs

```bash
# View all logs
docker-compose -f docker-compose.prod.yml logs -f

# View specific service logs
docker-compose -f docker-compose.prod.yml logs -f api-gateway
docker-compose -f docker-compose.prod.yml logs -f user-service-nestjs
docker-compose -f docker-compose.prod.yml logs -f template-service
docker-compose -f docker-compose.prod.yml logs -f email-service
docker-compose -f docker-compose.prod.yml logs -f push-service
```

### Test Health Endpoints

```bash
# Test API Gateway (from EC2)
curl http://localhost:8000/health | jq

# Test User Service
curl http://localhost:3000/health | jq

# Test Template Service  
curl http://localhost:3000/health | jq

# Test from outside (replace with your EC2 public IP)
curl http://your-ec2-public-ip:8000/health
```

---

## Step 8: Configure Firewall (AWS Security Group)

1. Go to **AWS Console** → **EC2** → **Security Groups**
2. Find your instance's security group
3. Add **Inbound Rules**:

| Type | Protocol | Port | Source | Description |
|------|----------|------|--------|-------------|
| SSH | TCP | 22 | My IP | SSH access |
| HTTP | TCP | 80 | 0.0.0.0/0 | HTTP traffic |
| HTTPS | TCP | 443 | 0.0.0.0/0 | HTTPS traffic |
| Custom TCP | TCP | 8000 | 0.0.0.0/0 | API Gateway (temporary) |

---

## Step 9: Set Up Nginx Reverse Proxy (Recommended)

### Install Nginx

```bash
sudo apt-get install -y nginx
```

### Configure Nginx

```bash
sudo nano /etc/nginx/sites-available/notification-system
```

Add:
```nginx
server {
    listen 80;
    server_name your-domain.com;  # Or your EC2 public IP

    location / {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /health {
        proxy_pass http://localhost:8000/health;
        access_log off;
    }
}
```

Enable the site:
```bash
sudo ln -s /etc/nginx/sites-available/notification-system /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

Now access your API at: `http://your-ec2-ip/` instead of `:8000`

---

## Step 10: Set Up SSL with Let's Encrypt (Optional but Recommended)

```bash
# Install Certbot
sudo apt-get install -y certbot python3-certbot-nginx

# Get SSL certificate (requires domain name)
sudo certbot --nginx -d your-domain.com

# Auto-renewal is set up automatically
# Test renewal:
sudo certbot renew --dry-run
```

---

## Common Docker Compose Commands

### Start Services
```bash
docker-compose -f docker-compose.prod.yml up -d
```

### Stop Services
```bash
docker-compose -f docker-compose.prod.yml down
```

### Restart Services
```bash
docker-compose -f docker-compose.prod.yml restart
```

### Restart Specific Service
```bash
docker-compose -f docker-compose.prod.yml restart api-gateway
```

### View Logs
```bash
# All services
docker-compose -f docker-compose.prod.yml logs -f

# Last 100 lines
docker-compose -f docker-compose.prod.yml logs --tail=100

# Specific service
docker-compose -f docker-compose.prod.yml logs -f user-service-nestjs
```

### Rebuild and Restart (after code changes)
```bash
git pull origin main
docker-compose -f docker-compose.prod.yml up -d --build
```

### Check Resource Usage
```bash
docker stats
```

### Clean Up (Remove everything)
```bash
docker-compose -f docker-compose.prod.yml down -v
# -v removes volumes (careful: this deletes database data!)
```

---

## Troubleshooting

### Service Won't Start

```bash
# Check logs
docker-compose -f docker-compose.prod.yml logs service-name

# Restart service
docker-compose -f docker-compose.prod.yml restart service-name

# Rebuild service
docker-compose -f docker-compose.prod.yml up -d --build service-name
```

### Database Connection Issues

```bash
# Check if database is running
docker-compose -f docker-compose.prod.yml ps user-db

# Connect to database
docker exec -it user-db psql -U user_service -d user_service_db

# Inside psql:
\dt  # List tables
SELECT * FROM users LIMIT 5;
\q   # Quit
```

### Out of Disk Space

```bash
# Check disk usage
df -h

# Clean up Docker
docker system prune -a --volumes
# WARNING: This removes all unused containers, networks, images, and volumes
```

### Port Already in Use

```bash
# Find what's using the port
sudo lsof -i :8000

# Kill the process
sudo kill -9 <PID>
```

### Memory Issues

```bash
# Check memory
free -h

# Restart services with lower memory limits
# Edit docker-compose.prod.yml and add:
# mem_limit: 512m
```

---

## Monitoring & Maintenance

### Set Up Auto-Start on Boot

```bash
# Enable Docker to start on boot
sudo systemctl enable docker

# Containers will auto-restart (restart: unless-stopped in compose file)
```

### Backup Databases

```bash
# Create backup script
nano ~/backup-databases.sh
```

Add:
```bash
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR=~/backups

mkdir -p $BACKUP_DIR

# Backup user database
docker exec user-db pg_dump -U user_service user_service_db > $BACKUP_DIR/user_db_$DATE.sql

# Backup template database  
docker exec template-db pg_dump -U template_service template_service_db > $BACKUP_DIR/template_db_$DATE.sql

# Backup gateway database
docker exec gateway-db pg_dump -U gateway_service gateway_service_db > $BACKUP_DIR/gateway_db_$DATE.sql

echo "Backups completed: $DATE"

# Keep only last 7 days
find $BACKUP_DIR -name "*.sql" -mtime +7 -delete
```

```bash
chmod +x ~/backup-databases.sh

# Add to crontab (daily at 2 AM)
crontab -e
# Add: 0 2 * * * /home/ubuntu/backup-databases.sh
```

### Monitor Logs

```bash
# Install log viewer
sudo apt-get install -y multitail

# View multiple logs at once
multitail -l 'docker-compose -f docker-compose.prod.yml logs -f api-gateway' \
          -l 'docker-compose -f docker-compose.prod.yml logs -f email-service'
```

---

## Quick Reference

### Your Services Will Be Available At:

- **API Gateway**: `http://your-ec2-ip:8000` (or `http://your-domain.com` with nginx)
- **RabbitMQ UI**: `http://your-ec2-ip:15672` (admin/your-password)
- **Databases**: Internal only (not exposed to internet)

### Important Files:

- **docker-compose.prod.yml**: Production deployment config
- **api-gateway/.env**: API Gateway environment
- **user-service-nestjs/.env**: User service environment
- **template-service/.env**: Template service environment
- **email-service/.env**: Email service environment
- **push-service/.env**: Push service environment

### Important Commands:

```bash
# Deploy
docker-compose -f docker-compose.prod.yml up -d --build

# Update after git pull
git pull && docker-compose -f docker-compose.prod.yml up -d --build

# Stop everything
docker-compose -f docker-compose.prod.yml down

# View logs
docker-compose -f docker-compose.prod.yml logs -f

# Restart a service
docker-compose -f docker-compose.prod.yml restart service-name
```

---

## Security Checklist

- [ ] Changed all default passwords
- [ ] Generated secure SECRET_KEY (64+ characters)
- [ ] Configured AWS Security Groups
- [ ] Set up Nginx reverse proxy
- [ ] Installed SSL certificate (Let's Encrypt)
- [ ] Set up automated backups
- [ ] Configured firewall (ufw or AWS)
- [ ] Updated SMTP credentials
- [ ] Added real Firebase credentials
- [ ] Removed or secured RabbitMQ management UI port (15672)
- [ ] Set up monitoring/alerting

---

## Next Steps

1. Test all endpoints: `./test_all_services.sh` (from local machine, update URLs)
2. Set up domain name and DNS
3. Configure SSL/HTTPS
4. Set up monitoring (CloudWatch, Prometheus, etc.)
5. Configure automated backups
6. Set up CI/CD pipeline to auto-deploy

**Your notification system is now running in production!** 🎉
