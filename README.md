# Notification System - Microservices Architecture

![Tests](https://img.shields.io/badge/tests-21%2F22%20passing-brightgreen)
![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![NestJS](https://img.shields.io/badge/nestjs-10.x-red)
![TypeScript](https://img.shields.io/badge/typescript-5.x-blue)
![Docker](https://img.shields.io/badge/docker-required-blue)
![License](https://img.shields.io/badge/license-MIT-green)

A scalable, distributed notification system built with microservices architecture that handles multiple notification channels (Email, Push notifications) with advanced features like circuit breaker patterns, retry logic, idempotency, and rate limiting.

## 📖 Documentation

- **[API_TESTING.md](./API_TESTING.md)** - Complete API endpoint documentation, testing examples, and troubleshooting
- **[PROJECT_CHARTER.md](./PROJECT_CHARTER.md)** - Detailed project specifications and requirements
- **[FCM_SETUP.md](./FCM_SETUP.md)** - Firebase Cloud Messaging setup guide
- **[ARCHITECTURE.txt](./ARCHITECTURE.txt)** - System architecture and design details
- **[CONTRIBUTING.md](./CONTRIBUTING.md)** - Contribution guidelines

## 📋 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Features](#features)
- [Quick Start](#quick-start)
- [Services](#services)
- [API Reference](#api-reference)
- [Testing](#testing)
- [Configuration](#configuration)
- [Troubleshooting](#troubleshooting)
- [Contributors](#contributors)

## Overview

A high-performance notification system designed for:

- **Performance**: 1,000+ notifications per minute
- **Reliability**: 99.5% delivery success rate
- **Scalability**: Horizontal scaling for all services
- **Resilience**: Circuit breaker and retry mechanisms

## Architecture

### System Diagram

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

### Tech Stack

- **Backend (Python)**: FastAPI (Python 3.11+)
- **Backend (NestJS)**: NestJS 10.x, TypeScript 5.x, TypeORM
- **Databases**: PostgreSQL 15 (3 separate instances)
- **Cache**: Redis 7
- **Message Queue**: RabbitMQ 3
- **Containerization**: Docker & Docker Compose
- **Authentication**: JWT (JSON Web Tokens)
- **Templates**: Jinja2

## Features

### Core Features

- ✅ Multi-channel notifications (Email, Push)
- ✅ Template management with Jinja2
- ✅ User authentication & preferences
- ✅ Bulk notification sending
- ✅ FCM token management

### Advanced Features

- ✅ Circuit breaker pattern
- ✅ Exponential backoff retry
- ✅ Idempotency keys
- ✅ Rate limiting (100 req/min)
- ✅ Dead letter queue
- ✅ Correlation ID tracking
- ✅ Structured JSON logging

## Quick Start

### Prerequisites

- Docker 20.10+
- Docker Compose 1.29+
- curl (for testing)

### 1. Clone Repository

```bash
git clone https://github.com/PreciousEzeigbo/distributed-notification-system.git
cd distributed-notification-system
```

### 2. Configure Environment

Copy and edit environment files for each service:

```bash
# Copy example files
cp api-gateway/.env.example api-gateway/.env
cp user-service-nestjs/.env.example user-service-nestjs/.env
cp template-service/.env.example template-service/.env
cp email-service/.env.example email-service/.env
cp push-service/.env.example push-service/.env
```

**Important**: Each service has its own `.env` file with only the configuration it needs.

**api-gateway/.env:**

```bash
DATABASE_URL=postgresql://gateway_service:gateway_password@gateway-db:5432/gateway_service_db
REDIS_URL=redis://redis:6379/0
RABBITMQ_URL=amqp://admin:admin@rabbitmq:5672/
USER_SERVICE_URL=http://user-service-nestjs:3000
TEMPLATE_SERVICE_URL=http://template-service:3000
SECRET_KEY=your-super-secret-key-min-64-characters
RATE_LIMIT_PER_MINUTE=100
PORT=8000
```

**user-service-nestjs/.env:**

```bash
DB_HOST=user-db
DB_PORT=5432
DB_USER=user_service
DB_PASSWORD=user_password
DB_NAME=user_service_db
RABBITMQ_URL=amqp://admin:admin@rabbitmq:5672/
PORT=3000
NODE_ENV=production
```

**template-service/.env:**

```bash
DB_HOST=template-db
DB_PORT=5432
DB_USER=template_service
DB_PASSWORD=template_password
DB_NAME=template_service_db
PORT=3000
NODE_ENV=production
```

**email-service/.env:**

```bash
RABBITMQ_URL=amqp://admin:admin@rabbitmq:5672/
SMTP_HOST=sandbox.smtp.mailtrap.io
SMTP_PORT=2525
SMTP_USER=your-mailtrap-username
SMTP_PASSWORD=your-mailtrap-password
SMTP_FROM=noreply@notificationapp.com
TEMPLATE_SERVICE_URL=http://template-service:3000
EMAIL_QUEUE=email.queue
MAX_RETRIES=3
```

**push-service/.env:**

```bash
RABBITMQ_URL=amqp://admin:admin@rabbitmq:5672/
FCM_CREDENTIALS_FILE=/app/fcm-credentials.json
TEMPLATE_SERVICE_URL=http://template-service:3000
PUSH_QUEUE=push.queue
MAX_RETRIES=3
```

> **📌 Note**: **📌 Firebase Setup**: For FCM setup, see [PROJECT_CHARTER.md - Section 17](./PROJECT_CHARTER.md#17-firebase-cloud-messaging-setup)

### 3. Start Services

```bash
docker-compose up -d

# Wait for services to become healthy (~30 seconds)

docker-compose ps
```

### 4. Verify Health

```bash

# All services should show "Up (healthy)"

docker-compose ps

# Test API Gateway

curl http://localhost:8000/health | python3 -m json.tool
```

### 5. Run Integration Tests

```bash
chmod +x test_all_services.sh
./test_all_services.sh
```

Expected output: **21/22 tests passing (95%)**

> **Note**: The PostgreSQL database test may show as failing, but this is a false negative - all databases are working correctly. The actual pass rate for functional tests is 95%.

## Services

### API Gateway (Port 8000)

**Language**: Python/FastAPI  
**Entry point** for all client requests. Handles routing, validation, JWT authentication, rate limiting, and message queuing.

**Health Check**: `http://localhost:8000/health`  
**Database**: gateway_service_db (Port 5434)

### User Service (Port 8001)

**Language**: NestJS/TypeScript  
Manages **user authentication**, registration, profiles, preferences, and FCM tokens.

**Health Check**: `http://localhost:8001/health`  
**Database**: user_service_db (Port 5432)  
**ORM**: TypeORM with UUID primary keys

### Template Service (Port 8002)

**Language**: NestJS/TypeScript  
Stores and renders **notification templates** with variable substitution.

**Health Check**: `http://localhost:8002/health`  
**Database**: template_service_db (Port 5433)  
**ORM**: TypeORM

### Email Service (Background Worker)

**Language**: Python/FastAPI  
Consumes `email.queue` and sends emails via SMTP with retry logic and circuit breaker.

### Push Service (Background Worker)

**Language**: Python/FastAPI  
Consumes `push.queue` and sends push notifications via Firebase Cloud Messaging.

### Infrastructure

- **PostgreSQL**: 3 separate databases for service isolation
- **Redis** (Port 6380): Caching, rate limiting, idempotency
- **RabbitMQ** (Ports 5672, 15672): Message queue with management UI

## API Reference

### 📚 Complete Documentation

**See [API_TESTING.md](./API_TESTING.md) for detailed endpoint documentation, examples, and troubleshooting.**

### Quick Reference

#### Base URLs

```
API Gateway:      http://localhost:8000
User Service:     http://localhost:8001 (NestJS)
Template Service: http://localhost:8002 (NestJS)
RabbitMQ UI:      http://localhost:15672
```

#### Sample Request Formats

**Send Notification**

```http
POST /notifications/send
Authorization: Bearer <token>
Content-Type: application/json

{
  "notification_type": "email",
  "user_id": "uuid-here",
  "template_code": "welcome_email",
  "variables": {
    "name": "John Doe",
    "link": "https://example.com"
  },
  "request_id": "unique-request-id",
  "priority": 0
}
```

**Register User**

```http
POST /users/register
Content-Type: application/json

{
  "name": "John Doe",
  "email": "john@example.com",
  "password": "SecurePass123!",
  "preferences": {
    "email": true,
    "push": true
  }
}
```

**Login**

```http
POST /users/login
Content-Type: application/x-www-form-urlencoded

username=john@example.com&password=SecurePass123!
```

#### Schema Definitions

**User ID Format**: UUID (e.g., `a383359a-f766-411c-8fd0-06754a606675`)

**NotificationType** (Enum)

```python
email = "email"
push = "push"
```

**NotificationStatus** (Enum)

```python
pending = "pending"
delivered = "delivered"
failed = "failed"
```

**Variables** (Dict[str, Any])

```python
# Email example
{
  "name": "John Doe",
  "link": "https://example.com",
  "email": "john@example.com"
}

# Push example
{
  "title": "Order Shipped",
  "body": "Your order is on the way!",
  "action_url": "https://example.com/orders/123"
}
```

### Standard Response Format

```json
{
  "success": true,
  "message": "Operation successful",
  "data": {},
  "error": null,
  "meta": null
}
```

## Testing

### Automated Test Suite

Run the complete integration test suite:

```bash
chmod +x test_all_services.sh
./test_all_services.sh
```

Tests include:

- ✅ Service health checks (all services)
- ✅ User registration & authentication
- ✅ FCM token management
- ✅ Template CRUD operations
- ✅ Email & push notifications
- ✅ Idempotency verification
- ✅ Rate limiting (100 req/min)
- ✅ RabbitMQ queue operations
- ✅ Redis cache operations
- ✅ End-to-end notification flow

**Current Pass Rate**: 95% (21/22 tests passing)

> **Note**: The PostgreSQL CLI test shows as failing due to `pg_isready` not being available, but all three databases (user, template, gateway) are operational and serving requests correctly. All functional tests pass.

### Manual Testing

**For comprehensive API testing examples and troubleshooting, see [API_TESTING.md](./API_TESTING.md)**

Quick health check:

```bash
# Test all services
curl http://localhost:8000/health # API Gateway
curl http://localhost:8001/health # User Service (NestJS)
curl http://localhost:8002/health # Template Service (NestJS)
```

### Unit Tests

```bash

# Run all tests

pytest

# Run specific service tests

cd api-gateway && pytest
cd user-service && pytest
```

### Monitoring

**RabbitMQ Management UI**: http://localhost:15672 (admin/admin)

- View queues: `email.queue`, `push.queue`, `failed.queue`
- Monitor message flow and consumer activity

**View Logs**:

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f api-gateway
docker-compose logs -f user-service-nestjs
docker-compose logs -f template-service
docker-compose logs -f email-service
```

**Database Inspection**:

```bash
# Connect to user database (NestJS/TypeORM)
docker exec -it user-db psql -U user_service -d user_service_db

# View users with UUID
SELECT id, name, email, created_at FROM users LIMIT 5;

# Connect to gateway database
docker exec -it gateway-db psql -U gateway_service -d gateway_service_db

# View notifications
SELECT id, request_id, notification_type, status, created_at
FROM notification_requests
ORDER BY created_at DESC
LIMIT 10;
```

## Configuration

### Environment Variables

#### Common Variables

```bash
DATABASE_URL=postgresql://user:password@host:5432/dbname
REDIS_URL=redis://redis:6379/0
RABBITMQ_URL=amqp://admin:admin@rabbitmq:5672/
SECRET_KEY=your-secret-key
LOG_LEVEL=INFO
```

#### Email Service

```bash
SMTP_HOST=smtp.mailtrap.io
SMTP_PORT=2525
SMTP_USER=your-user
SMTP_PASSWORD=your-password
SMTP_FROM_EMAIL=noreply@example.com
```

#### Push Service

```bash
FCM_CREDENTIALS_FILE=/app/fcm-credentials.json
FCM_PROJECT_ID=your-firebase-project-id
```

### Port Mapping

| Service                   | Internal Port | External Port | Access URL             |
| ------------------------- | ------------- | ------------- | ---------------------- |
| API Gateway               | 8000          | 8000          | http://localhost:8000  |
| User Service (NestJS)     | 3000          | 8001          | http://localhost:8001  |
| Template Service (NestJS) | 3000          | 8002          | http://localhost:8002  |
| RabbitMQ (AMQP)           | 5672          | 5672          | amqp://localhost:5672  |
| RabbitMQ (UI)             | 15672         | 15672         | http://localhost:15672 |
| Redis                     | 6379          | 6380          | redis://localhost:6380 |
| PostgreSQL (User)         | 5432          | 5432          | localhost:5432         |
| PostgreSQL (Template)     | 5432          | 5433          | localhost:5433         |
| PostgreSQL (Gateway)      | 5432          | 5434          | localhost:5434         |

**Important**:

- Service-to-service communication uses **internal ports** and **container names**
- External access uses **external ports** and **localhost**
- Example: API Gateway calls `http://user-service-nestjs:3000` (not `http://localhost:8001`)

## Troubleshooting

### Common Issues

#### Services Not Starting

```bash

# Check logs

docker-compose logs

# Restart all services

docker-compose down
docker-compose up -d
```

#### Database Authentication Failed

**Problem**: \`FATAL: password authentication failed\`

**Solution**: Ensure \`.env\` database credentials match \`docker-compose.yml\`:

```bash

# Verify credentials

grep "POSTGRES" docker-compose.yml
grep "DATABASE_URL" api-gateway/.env

# Expected format:

# DATABASE_URL=postgresql://gateway_service:gateway_password@gateway-db:5432/gateway_service_db

```

#### RabbitMQ Connection Refused

**Problem**: Worker services can't connect to RabbitMQ

**Solution**: Add \`RABBITMQ_URL\` to worker \`.env\` files:

```bash

# email-service/.env and push-service/.env

RABBITMQ_URL=amqp://admin:admin@rabbitmq:5672/

# Restart workers

docker-compose restart email-service push-service
```

#### Port Already in Use

```bash

# Check what's using the port

sudo lsof -i :8000

# Change ports in docker-compose.yml or stop conflicting service

```

#### Push Notifications: "Invalid FCM token"

**Status**: ✅ **EXPECTED** during testing with dummy tokens

**Explanation**: Test tokens like \`test_fcm_token_XXX\` are rejected by FCM. For production:

1. Set up mobile/web app with Firebase SDK
2. Get real FCM token from device
3. Register user with real token

See [PROJECT_CHARTER.md - Section 17](./PROJECT_CHARTER.md#17-firebase-cloud-messaging-setup) for FCM setup.

#### Service-to-Service Communication Fails

**Problem**: API Gateway can't reach other services

**Solution**: Use **container names and internal ports** in `.env` files:

```bash
# api-gateway/.env - Use container names and internal ports
USER_SERVICE_URL=http://user-service-nestjs:3000 # ✅ Correct
TEMPLATE_SERVICE_URL=http://template-service:3000 # ✅ Correct

# NOT external ports or localhost:
USER_SERVICE_URL=http://localhost:8001 # ❌ Wrong (external)
USER_SERVICE_URL=http://user-service-nestjs:8001 # ❌ Wrong (port)
```

### Getting Help

**For comprehensive troubleshooting, see [API_TESTING.md](./API_TESTING.md#-troubleshooting)**

Common resources:

- Check service logs: \`docker-compose logs -f <service>\`
- RabbitMQ UI: http://localhost:15672
- Database inspection: \`docker exec -it gateway-db psql -U gateway_service -d gateway_service_db\`
- Health endpoints: \`curl http://localhost:8000/health\`

## Project Structure

```
notification-system/
├── api-gateway/              # Python/FastAPI - Entry point, routing, queue management
├── user-service-nestjs/      # NestJS/TypeScript - User authentication & management (TypeORM)
├── template-service/         # NestJS/TypeScript - Template storage & rendering (TypeORM)
├── email-service/            # Python/FastAPI - Email worker
├── push-service/             # Python/FastAPI - Push notification worker
├── docker-compose.yml        # Container orchestration
├── docker-compose.prod.yml   # Production deployment config
├── test_all_services.sh      # Automated integration test script
├── deploy.sh                 # Deployment automation script
├── API_TESTING.md            # Complete API documentation
├── PROJECT_CHARTER.md        # Project specifications
└── README.md                 # This file
```

## Development

### Local Development

```bash
# Python services
cd api-gateway
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# NestJS services
cd user-service-nestjs
npm install
npm run start:dev  # Runs on port 3000

cd template-service
npm install
npm run start:dev  # Runs on port 3000
```

### Horizontal Scaling

```bash

# Scale API Gateway

docker-compose up -d --scale api-gateway=3

# Scale workers

docker-compose up -d --scale email-service=2 --scale push-service=2
```

## Security

- **JWT tokens** expire after 30 minutes
- **Passwords** hashed with bcrypt (user-service-nestjs)
- **Rate limiting**: 100 requests/minute per user
- **CORS** configured for specific origins
- **No secrets** in code or logs
- **UUID primary keys** for users (prevents enumeration attacks)
- **Database credentials** in environment variables per service
- **Per-service isolation**: Each service only knows credentials it needs

## Contributors

**HNG BACKEND TRACK - Team 21**

## Support

For issues and questions:

- Review [API_TESTING.md](./API_TESTING.md) for comprehensive API documentation
- Check [DEPLOYMENT.md](./DEPLOYMENT.md) for production deployment guidance
- Review [PER_SERVICE_ENV_GUIDE.md](./PER_SERVICE_ENV_GUIDE.md) for environment configuration
- Check [PROJECT_CHARTER.md](./PROJECT_CHARTER.md) for specifications
- Review logs: `docker-compose logs -f <service>`
- RabbitMQ UI: http://localhost:15672
- Check service health endpoints

---

**Built by HNG Backend Track - Team 21**
