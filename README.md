# Notification System - Microservices Architecture

A scalable, distributed notification system built with microservices architecture that handles multiple notification channels (Email, Push, SMS) with advanced features including circuit breaker patterns, retry logic, idempotency, and rate limiting.

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Features](#features)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Services](#services)
- [API Documentation](#api-documentation)
- [Configuration](#configuration)
- [Testing](#testing)
- [Monitoring](#monitoring)
- [Troubleshooting](#troubleshooting)

## Overview

This notification system is designed to handle high-volume notification delivery across multiple channels with the following goals:

- **Performance**: Handle 1,000+ notifications per minute
- **Reliability**: 99.5% delivery success rate
- **Scalability**: All services support horizontal scaling
- **Resilience**: Circuit breaker and retry mechanisms for fault tolerance

## Architecture

### System Components

```
┌─────────────┐     ┌──────────────────┐     ┌──────────────┐
│   Client    │────▶│   API Gateway    │────▶│ User Service │
└─────────────┘     └──────────────────┘     └──────────────┘
                            │
                            ├──────────────────┐
                            ▼                  ▼
                    ┌──────────────┐   ┌─────────────────┐
                    │   RabbitMQ   │   │ Template Service│
                    └──────────────┘   └─────────────────┘
                            │
                    ┌───────┴───────┐
                    ▼               ▼
            ┌──────────────┐  ┌──────────────┐
            │Email Service │  │ Push Service │
            └──────────────┘  └──────────────┘
```

### Technology Stack

- **API Framework**: FastAPI (Python 3.11)
- **Databases**: PostgreSQL 15 (3 separate instances)
- **Cache**: Redis 7
- **Message Queue**: RabbitMQ 3
- **Containerization**: Docker & Docker Compose
- **Authentication**: JWT (JSON Web Tokens)
- **Template Engine**: Jinja2

## Features

### Core Functionality

- **Multi-Channel Support**: Email, Push notifications, SMS (extensible)
- **Template Management**: Store and version notification templates
- **User Management**: Authentication, preferences, profile management
- **Bulk Notifications**: Send to multiple recipients efficiently

### Advanced Features

- **Circuit Breaker**: Automatic failure detection and recovery
- **Retry Logic**: Exponential backoff for failed deliveries
- **Idempotency**: Prevent duplicate notification sends
- **Rate Limiting**: 100 requests per minute per user
- **Dead Letter Queue**: Handle permanently failed messages
- **Correlation IDs**: Request tracking across services
- **Structured Logging**: JSON-formatted logs with correlation

## Prerequisites

- Docker 20.10+
- Docker Compose 1.29+
- curl (for testing)
- Python 3.11+ (for local development)

## Quick Start

### 1. Clone and Configure

```bash
git clone https://github.com/PreciousEzeigbo/distributed-notification-system.git
cd distributed-notification-system
cp .env.example .env
```

### 2. Configure Environment Variables

Edit `.env` file with your credentials:

```bash
# SMTP Configuration (for email service)
SMTP_HOST=sandbox.smtp.mailtrap.io
SMTP_PORT=2525
SMTP_USER=your-mailtrap-user
SMTP_PASSWORD=your-mailtrap-password
SMTP_FROM_EMAIL=noreply@notification-system.com

# Firebase Cloud Messaging (for push service)
FCM_CREDENTIALS_FILE=/app/fcm-credentials.json
FCM_CREDENTIALS_PATH=./fcm-credentials.json

# Security
SECRET_KEY=your-super-secret-key-change-this-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### 3. Start All Services

```bash
# Use the automated startup script
./fix_and_start.sh

# Or manually
docker-compose up -d
```

### 4. Verify System Health

```bash
# Check all containers
docker-compose ps

# Test API Gateway
curl http://localhost:8000/health

# Test User Service
curl http://localhost:8001/health

# Test Template Service
curl http://localhost:8002/health
```

## Services

### API Gateway (Port 8000)

**Purpose**: Entry point for all client requests

**Responsibilities**:

- Request routing and validation
- JWT token validation
- Rate limiting (100 req/min per user)
- Idempotency checking
- Message queue publishing
- Notification status tracking

**Health Check**: `GET http://localhost:8000/health`

**Database**: gateway_service_db (Port 5434)

### User Service (Port 8001)

**Purpose**: User and authentication management

**Responsibilities**:

- User registration and login
- JWT token generation
- User profile management
- Notification preferences
- User validation for other services

**Health Check**: `GET http://localhost:8001/health`

**Database**: user_service_db (Port 5432)

### Template Service (Port 8002)

**Purpose**: Notification template storage and rendering

**Responsibilities**:

- Store notification templates
- Template versioning
- Variable substitution (Jinja2)
- Multi-language support
- Template validation

**Health Check**: `GET http://localhost:8002/health`

**Database**: template_service_db (Port 5433)

### Email Service (Background Worker)

**Purpose**: Consume email queue and send emails

**Responsibilities**:

- Consume messages from `email.queue`
- Fetch and render templates
- Send emails via SMTP
- Retry logic with circuit breaker
- Send failed messages to DLQ

**Queue**: email.queue

### Push Service (Background Worker)

**Purpose**: Consume push notification queue

**Responsibilities**:

- Consume messages from `push.queue`
- Fetch and render templates
- Send via Firebase Cloud Messaging
- Retry logic with circuit breaker
- Send failed messages to DLQ

**Queue**: push.queue

### Infrastructure Services

- **PostgreSQL**: 3 separate databases for service isolation
- **Redis** (Port 6380): Caching, rate limiting, idempotency tracking
- **RabbitMQ** (Ports 5672, 15672): Message queue with management UI

## API Documentation

### Standard Response Format

All API endpoints return responses in this format:

```json
{
  "success": true,
  "message": "Operation completed successfully",
  "data": {
    /* response data */
  },
  "error": null,
  "meta": {
    "timestamp": "2025-11-10T12:34:56.789Z",
    "correlation_id": "uuid-v4",
    "page": 1,
    "per_page": 20,
    "total": 100,
    "total_pages": 5
  }
}
```

### Authentication

#### Register User

```http
POST /users/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecurePass123!"
}
```

#### Login

```http
POST /users/login
Content-Type: application/x-www-form-urlencoded

username=user@example.com&password=SecurePass123!
```

Response:

```json
{
  "success": true,
  "data": {
    "access_token": "eyJhbGc...",
    "token_type": "bearer"
  }
}
```

### Sending Notifications

#### Send Single Notification

```http
POST /notifications/send
Authorization: Bearer <token>
Idempotency-Key: unique-key-12345
Content-Type: application/json

{
  "channel": "email",
  "recipient": "recipient@example.com",
  "template_name": "welcome_email",
  "variables": {
    "username": "John Doe",
    "activation_link": "https://example.com/activate"
  },
  "priority": "normal"
}
```

#### Send Bulk Notifications

```http
POST /notifications/send-bulk
Authorization: Bearer <token>
Content-Type: application/json

{
  "channel": "email",
  "template_name": "monthly_newsletter",
  "recipients": [
    {
      "recipient": "user1@example.com",
      "variables": { "name": "John" }
    },
    {
      "recipient": "user2@example.com",
      "variables": { "name": "Jane" }
    }
  ]
}
```

#### Check Notification Status

```http
GET /notifications/status/{notification_id}
Authorization: Bearer <token>
```

### Template Management

#### Create Template

```http
POST /templates
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "welcome_email",
  "subject": "Welcome to {{company_name}}!",
  "body": "Hello {{username}}, welcome to our platform!",
  "channel": "email",
  "language": "en",
  "variables": ["company_name", "username"]
}
```

#### List Templates

```http
GET /templates?page=1&per_page=20&channel=email
Authorization: Bearer <token>
```

#### Render Template

```http
POST /templates/render
Content-Type: application/json

{
  "template_name": "welcome_email",
  "variables": {
    "company_name": "TechCorp",
    "username": "John Doe"
  }
}
```

### User Preferences

#### Set Notification Preferences

```http
POST /users/preferences
Authorization: Bearer <token>
Content-Type: application/json

{
  "channel": "email",
  "enabled": true,
  "preferences": {
    "marketing": true,
    "transactional": true,
    "frequency": "daily"
  }
}
```

## Configuration

### Environment Variables

#### Common Variables (All Services)

```bash
# Service Configuration
SERVICE_NAME=service-name
SERVICE_VERSION=1.0.0
PORT=8000

# Database
DATABASE_URL=postgresql://user:password@host:5432/dbname
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=10

# Redis
REDIS_URL=redis://redis:6380
REDIS_TTL=86400

# JWT Authentication
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
```

#### Email Service Specific

```bash
SMTP_HOST=smtp.mailtrap.io
SMTP_PORT=2525
SMTP_USER=your-user
SMTP_PASSWORD=your-password
SMTP_FROM_EMAIL=noreply@notification-system.com
SMTP_USE_TLS=True
```

#### Push Service Specific

```bash
FCM_CREDENTIALS_FILE=/app/fcm-credentials.json
```

#### Circuit Breaker & Retry

```bash
CIRCUIT_BREAKER_THRESHOLD=5
CIRCUIT_BREAKER_TIMEOUT=60
MAX_RETRIES=3
RETRY_BASE_DELAY=2
RETRY_MAX_DELAY=60
```

### RabbitMQ Configuration

**Exchange**: notifications.direct (type: direct)

**Queues**:

- `email.queue` - Email notifications with DLX
- `push.queue` - Push notifications with DLX
- `failed.queue` - Dead letter queue

**Routing Keys**:

- `email` -> email.queue
- `push` -> push.queue
- `failed` -> failed.queue

## Testing

### Manual API Testing

1. **Register a user**:

```bash
curl -X POST http://localhost:8001/users/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Test123!"}'
```

2. **Login**:

```bash
curl -X POST http://localhost:8001/users/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=test@example.com&password=Test123!"
```

3. **Create a template**:

```bash
curl -X POST http://localhost:8002/templates \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "test_email",
    "subject": "Test {{subject}}",
    "body": "Hello {{name}}!",
    "channel": "email",
    "variables": ["subject", "name"]
  }'
```

4. **Send a notification**:

```bash
curl -X POST http://localhost:8000/notifications/send \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Idempotency-Key: test-key-001" \
  -H "Content-Type: application/json" \
  -d '{
    "channel": "email",
    "recipient": "recipient@example.com",
    "template_name": "test_email",
    "variables": {
      "subject": "Welcome",
      "name": "John"
    }
  }'
```

### Viewing Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f api-gateway
docker-compose logs -f email-service
docker-compose logs -f push-service

# Last 50 lines
docker-compose logs --tail=50 api-gateway
```

### Accessing RabbitMQ Management UI

Open browser: http://localhost:15672

- Username: admin
- Password: admin

View queues, exchanges, and message flow.

## Monitoring

### Health Checks

All REST services expose `/health` endpoints:

```bash
# API Gateway
curl http://localhost:8000/health | python3 -m json.tool

# User Service
curl http://localhost:8001/health | python3 -m json.tool

# Template Service
curl http://localhost:8002/health | python3 -m json.tool
```

### Service Status

```bash
# Check all containers
docker-compose ps

# Check resource usage
docker stats

# Check specific service logs
docker-compose logs --tail=100 email-service
```

### Database Connections

```bash
# Connect to User Service DB
docker exec -it user-db psql -U user_service -d user_service_db

# Connect to Template Service DB
docker exec -it template-db psql -U template_service -d template_service_db

# Connect to Gateway DB
docker exec -it gateway-db psql -U gateway_service -d gateway_service_db
```

### Redis Monitoring

```bash
# Connect to Redis CLI
docker exec -it redis redis-cli

# Check keys
KEYS *

# Monitor commands in real-time
MONITOR
```

## Troubleshooting

### Services Not Starting

**Problem**: Containers exit immediately

**Solution**:

```bash
# Check logs for errors
docker-compose logs

# Restart with the fix script
./fix_and_start.sh
```

### Port Already in Use

**Problem**: Port 6379 already in use (Redis conflict)

**Solution**: The system uses port 6380 for Redis to avoid conflicts. If needed, update docker-compose.yml ports.

### Queue Declaration Errors

**Problem**: PRECONDITION_FAILED errors in worker services

**Solution**:

```bash
# Delete existing queues
docker exec rabbitmq rabbitmqctl delete_queue email.queue
docker exec rabbitmq rabbitmqctl delete_queue push.queue

# Restart API Gateway first (creates queues)
docker-compose restart api-gateway

# Then restart workers
docker-compose restart email-service push-service
```

### Worker Services Crash Loop

**Problem**: Email/Push services keep restarting

**Solution**:

```bash
# Check worker logs
docker-compose logs --tail=50 email-service
docker-compose logs --tail=50 push-service

# Ensure API Gateway started first
./fix_and_start.sh
```

### Database Connection Issues

**Problem**: "database not found" or connection errors

**Solution**:

```bash
# Check database health
docker-compose ps

# Restart databases
docker-compose restart user-db template-db gateway-db

# Wait for health checks
sleep 10
```

### "Empty reply from server" when testing APIs

**Problem**: curl returns empty response

**Solution**:

```bash
# Wait for services to fully initialize
sleep 15

# Check if service is actually running
docker-compose ps api-gateway

# Check logs for startup errors
docker-compose logs api-gateway
```

## Performance Optimization

### Horizontal Scaling

Scale specific services:

```bash
# Scale API Gateway to 3 instances
docker-compose up -d --scale api-gateway=3

# Scale worker services
docker-compose up -d --scale email-service=2 --scale push-service=2
```

### Database Connection Pooling

Configured in each service's database.py:

- Pool size: 20
- Max overflow: 10
- Pool timeout: 30s

### Redis Caching

- Rate limit data: 60s TTL
- Idempotency keys: 24h TTL
- Session data: 30min TTL

## Development

### Local Development Setup

1. Install dependencies:

```bash
cd user-service
pip install -r requirements.txt
```

2. Run service locally:

```bash
uvicorn app.main:app --reload --port 8001
```

### Adding a New Service

1. Create service directory
2. Add Dockerfile
3. Create requirements.txt
4. Implement FastAPI app with /health endpoint
5. Add to docker-compose.yml
6. Update documentation

### Code Structure

```
notification-system/
├── api-gateway/
│   ├── app/
│   │   ├── main.py
│   │   ├── routes.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── config.py
│   │   ├── database.py
│   │   └── utils/
│   │       ├── circuit_breaker.py
│   │       ├── retry_handler.py
│   │       ├── logging_config.py
│   │       └── response_models.py
│   ├── Dockerfile
│   └── requirements.txt
├── user-service/
│   ├── app/
│   │   ├── main.py
│   │   ├── routes.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── config.py
│   │   └── database.py
│   ├── Dockerfile
│   └── requirements.txt
├── template-service/
│   ├── app/
│   │   ├── main.py
│   │   ├── routes.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── config.py
│   │   └── database.py
│   ├── Dockerfile
│   └── requirements.txt
├── email-service/
│   ├── app/
│   │   ├── main.py
│   │   ├── consumer.py
│   │   └── utils/
│   │       ├── circuit_breaker.py
│   │       ├── retry_handler.py
│   │       └── logging_config.py
│   ├── Dockerfile
│   └── requirements.txt
├── push-service/
│   ├── app/
│   │   ├── main.py
│   │   ├── consumer.py
│   │   └── utils/
│   │       ├── circuit_breaker.py
│   │       ├── retry_handler.py
│   │       └── logging_config.py
│   ├── Dockerfile
│   └── requirements.txt
├── docker-compose.yml
├── .env.example
├── .gitignore
├── PROJECT_CHARTER.md
├── CONTRIBUTING.md
├── ARCHITECTURE.txt
└── README.md
```

## Security Considerations

- JWT tokens expire after 30 minutes
- Passwords hashed with bcrypt
- Rate limiting prevents abuse
- CORS configured for specific origins
- Database credentials in environment variables
- No secrets in code or logs

## Contributors

**HNG BACKEND TRACK-Team 21**

## Support

For issues and questions:

- Check logs: `docker-compose logs -f`
- Review troubleshooting section
- Check RabbitMQ management UI: http://localhost:15672
