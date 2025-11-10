# Project Charter: Notification System

This document outlines the core principles, architectural guidelines, and expected standards for contributing to the Notification System. Our goal is to build a robust, scalable, and extensible microservice-based notification platform.

## 1. What We Are Building

The Notification System is a microservice-oriented platform designed to manage and deliver various types of notifications (e.g., email, push, in-app) to users. It comprises an API Gateway, a User Service, an Email Service, Push Service and Template Service.

### 8.1. API Endpoints

- Use kebab-case for URLs: `/api/v1/notifications/send`
- Use plural nouns for resources: `/users`, `/templates`
- Version APIs: `/api/v1/`, `/api/v2/`

### 8.2. Code Variables & Functions

- **Python Services**: Use `snake_case` for variables, functions, parameters
- **Other Languages**: Follow language-specific conventions (e.g., camelCase for JavaScript)
- **Database Columns**: Use `snake_case` across all services for consistency

### 8.3. Environment Variables

- Use UPPER_SNAKE_CASE: `DATABASE_URL`, `SMTP_HOST`, `JWT_SECRET_KEY`

### 8.4. Message Queue Names

- Use dot notation: `email.queue`, `push.queue`, `failed.queue`

## 9. Environment Configuration

### 9.1. Required Environment Variables and a Template Service. These services are designed to be independent and communicate efficiently to provide a comprehensive notification solution.

## 2. Core Principles & Rules!! READ AND READ AGAIN

To ensure consistency, maintainability, and interoperability across services, especially given the use of multiple programming languages, the following rules must be adhered to:

### 2.1. Microservice Autonomy & Language Agnosticism

- **Rule:** Each service should be independently deployable, scalable, and maintainable. You are free to choose the most suitable programming language and technology stack for your service.
- **Why:** Promotes flexibility, allows teams to leverage specialized tools, and prevents technology lock-in. Existing services (e.g., `user-service`, `email-service`, `push-service`, `template-service`) serve as reference implementations for architectural patterns and communication styles, but not necessarily language.

### 2.2. API Gateway as Entry Point

- **Rule:** All external client requests must route through the `api-gateway`. Direct access to individual services from external clients is forbidden.
- **Why:** Centralizes request handling, authentication, authorization, rate limiting, and provides a single, consistent interface to the notification system.

### 2.3. Standardized Communication

- **Rule:** Services must communicate primarily via well-defined, language-agnostic protocols such as HTTP/REST (with JSON payloads) or message queues (e.g., RabbitMQ, Kafka).
- **Why:** Ensures interoperability between services built with different technologies and promotes loose coupling.

### 2.4. Data Ownership & Isolation

- **Rule:** Each service is responsible for its own data and should not directly access another service's database. Data sharing should occur exclusively through well-defined API endpoints.
- **Why:** Enforces service autonomy, prevents tight coupling, and simplifies data management and schema evolution.

### 2.5. Consistent Logging & Monitoring

- **Rule:** All services must implement standardized logging practices (e.g., structured logs in JSON format) and expose metrics for monitoring.
- **Why:** Facilitates centralized log aggregation, easier debugging, performance monitoring, and operational visibility across the entire system.

### 2.6. API Documentation

- **Rule:** Every service exposing an API must provide clear and up-to-date documentation (e.g., OpenAPI/Swagger specifications).
- **Why:** Enables seamless integration between services and provides clear contracts for consumers.

### 2.7. Error Handling

- **Rule:** Implement consistent error handling mechanisms and response formats across all services.
- **Why:** Provides a predictable experience for API consumers and simplifies error diagnosis.

## 3. Response Formats

All API responses, both successful and erroneous, should adhere to a standardized JSON format.

### 3.1. Success Response Format

```json
{
  "status": "success",
  "data": {
    // Service-specific data payload
  },
  "message": "Optional success message"
}
```

### 3.2. Error Response Format

```json
{
  "status": "error",
  "code": "UNIQUE_ERROR_CODE", // e.g., "USER_NOT_FOUND", "INVALID_INPUT"
  "message": "A human-readable description of the error.",
  "details": {
    // Optional: More specific details, e.g., validation errors, stack trace (in dev)
  }
}
```

- **`status`**: Indicates "success" or "error".
- **`code`**: A unique, machine-readable error code for programmatic handling.
- **`message`**: A concise, human-readable explanation of the error.
- **`details`**: An optional object for additional context, such as validation errors (e.g., `{"field": "email", "reason": "invalid format"}`) or internal error identifiers.

## 4. Service Architecture

### 4.1. Service Overview

The system consists of five core services:

| Service              | Port   | Technology     | Responsibility                                                 |
| -------------------- | ------ | -------------- | -------------------------------------------------------------- |
| **API Gateway**      | 8000   | Python/FastAPI | Entry point, auth, rate limiting, idempotency, status tracking |
| **User Service**     | 8001   | Python/FastAPI | User management, authentication (JWT), preferences             |
| **Template Service** | 8002   | Python/FastAPI | Template storage, versioning, rendering (Jinja2)               |
| **Email Service**    | Worker | Python         | Consumes email.queue, sends via SMTP                           |
| **Push Service**     | Worker | Python         | Consumes push.queue, sends via FCM                             |

### 4.2. Infrastructure Components

- **RabbitMQ**: Message broker with `email.queue`, `push.queue`, and `failed.queue` (dead letter queue)
- **Redis**: Caching, rate limiting, idempotency tracking
- **PostgreSQL**: Three databases (gateway-db, user-db, template-db)
- **Docker Compose**: Container orchestration

### 4.3. Communication Patterns

- **Synchronous**: HTTP/REST for service-to-service calls (e.g., fetching user data, template rendering)
- **Asynchronous**: RabbitMQ for notification processing (email, push)

## 5. Key Technical Concepts

### 5.1. Circuit Breaker Pattern

- **Purpose**: Prevent cascading failures when external services (SMTP, FCM) are down
- **Threshold**: 5 consecutive failures
- **Timeout**: 60 seconds before attempting recovery
- **States**: CLOSED → OPEN → HALF-OPEN → CLOSED

### 5.2. Retry Mechanism

- **Max Retries**: 3 attempts
- **Backoff Strategy**: Exponential (2s, 4s, 8s)
- **Dead Letter Queue**: Failed messages after max retries go to `failed.queue`

### 5.3. Idempotency

- **Purpose**: Prevent duplicate notification processing
- **Implementation**: `request_id` tracked in Redis with 24-hour TTL
- **Response**: Return HTTP 409 for duplicate requests

### 5.4. Rate Limiting

- **Limit**: 100 requests per minute per user
- **Storage**: Redis-based
- **Response**: HTTP 429 with rate limit headers

### 5.5. Correlation IDs

- **Purpose**: Track requests across service boundaries
- **Header**: `X-Correlation-ID`
- **Requirement**: Propagate to all downstream services and logs

### 5.6. Health Checks

- **Endpoint**: `GET /health` on every service
- **Purpose**: Service discovery, load balancing, monitoring
- **Response**: Include dependency health (database, Redis, RabbitMQ)

## 6. API Endpoints

### 6.1. API Gateway (Port 8000)

**Base URL:** `http://localhost:8000/api/v1`

#### Send Notification

```http
POST /api/v1/notifications/
Authorization: Bearer {jwt_token}
Content-Type: application/json

{
  "notification_type": "email|push",
  "user_id": "uuid",
  "template_code": "welcome_email",
  "variables": {
    "name": "John Doe",
    "link": "https://example.com",
    "meta": {}
  },
  "request_id": "unique-request-id",
  "priority": 0,
  "metadata": {}
}

Response: 201 Created
{
  "status": "success",
  "data": {
    "notification_id": "uuid",
    "status": "queued",
    "created_at": "2025-11-10T12:34:56Z"
  },
  "message": "Notification queued successfully"
}
```

#### Get Notification Status

```http
GET /api/v1/notifications/{notification_id}
Authorization: Bearer {jwt_token}

Response: 200 OK
{
  "status": "success",
  "data": {
    "notification_id": "uuid",
    "user_id": "uuid",
    "notification_type": "email",
    "status": "sent|pending|failed",
    "created_at": "2025-11-10T12:34:56Z",
    "updated_at": "2025-11-10T12:35:00Z",
    "error": null
  }
}
```

#### Update Notification Status (Internal - Worker Services)

```http
POST /api/v1/{notification_type}/status
Content-Type: application/json

{
  "notification_id": "uuid",
  "status": "sent|failed",
  "timestamp": "2025-11-10T12:35:00Z",
  "error": "Optional error message"
}

Response: 200 OK
{
  "status": "success",
  "message": "Status updated successfully"
}
```

#### Health Check

```http
GET /health

Response: 200 OK
{
  "status": "success",
  "data": {
    "status": "healthy",
    "service": "api-gateway",
    "checks": {
      "database": "ok",
      "redis": "ok",
      "rabbitmq": "ok"
    }
  }
}
```

### 6.2. User Service (Port 8001)

**Base URL:** `http://localhost:8001/api/v1`

#### Register User

```http
POST /api/v1/users/
Content-Type: application/json

{
  "name": "John Doe",
  "email": "john@example.com",
  "password": "secure_password",
  "push_token": "fcm-device-token-optional",
  "preferences": {
    "email": true,
    "push": true
  }
}

Response: 201 Created
{
  "status": "success",
  "data": {
    "user_id": "uuid",
    "name": "John Doe",
    "email": "john@example.com",
    "created_at": "2025-11-10T12:34:56Z"
  },
  "message": "User registered successfully"
}
```

#### Login

```http
POST /api/v1/users/login
Content-Type: application/x-www-form-urlencoded

username=john@example.com
password=secure_password

Response: 200 OK
{
  "status": "success",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "expires_in": 1800
  }
}
```

#### Get Current User

```http
GET /api/v1/users/me
Authorization: Bearer {jwt_token}

Response: 200 OK
{
  "status": "success",
  "data": {
    "user_id": "uuid",
    "name": "John Doe",
    "email": "john@example.com",
    "push_token": "fcm-device-token",
    "preferences": {
      "email": true,
      "push": true
    },
    "created_at": "2025-11-10T12:34:56Z"
  }
}
```

#### Get User by ID

```http
GET /api/v1/users/{user_id}
Authorization: Bearer {jwt_token}

Response: 200 OK
{
  "status": "success",
  "data": {
    "user_id": "uuid",
    "name": "John Doe",
    "email": "john@example.com",
    "preferences": {
      "email": true,
      "push": true
    }
  }
}
```

#### Update User Preferences

```http
PUT /api/v1/users/preferences
Authorization: Bearer {jwt_token}
Content-Type: application/json

{
  "preferences": {
    "email": false,
    "push": true
  }
}

Response: 200 OK
{
  "status": "success",
  "data": {
    "preferences": {
      "email": false,
      "push": true
    }
  },
  "message": "Preferences updated successfully"
}
```

### 6.3. Template Service (Port 8002)

**Base URL:** `http://localhost:8002/api/v1`

#### Create Template

```http
POST /api/v1/templates/
Authorization: Bearer {jwt_token}
Content-Type: application/json

{
  "name": "welcome_email",
  "subject": "Welcome to {{app_name}}!",
  "body": "Hi {{name}},\n\nWelcome to our platform! Click here: {{link}}",
  "channel": "email|push",
  "language": "en",
  "version": "1.0.0",
  "variables": ["name", "link", "app_name"]
}

Response: 201 Created
{
  "status": "success",
  "data": {
    "template_id": "uuid",
    "name": "welcome_email",
    "channel": "email",
    "language": "en",
    "version": "1.0.0",
    "created_at": "2025-11-10T12:34:56Z"
  },
  "message": "Template created successfully"
}
```

#### List Templates

```http
GET /api/v1/templates/?channel=email&language=en&page=1&limit=20
Authorization: Bearer {jwt_token}

Response: 200 OK
{
  "status": "success",
  "data": [
    {
      "template_id": "uuid",
      "name": "welcome_email",
      "subject": "Welcome to {{app_name}}!",
      "channel": "email",
      "language": "en",
      "version": "1.0.0"
    }
  ],
  "meta": {
    "page": 1,
    "per_page": 20,
    "total": 1,
    "total_pages": 1
  }
}
```

#### Get Template by Code

```http
GET /api/v1/templates/{template_code}
Authorization: Bearer {jwt_token}

Response: 200 OK
{
  "status": "success",
  "data": {
    "template_id": "uuid",
    "name": "welcome_email",
    "subject": "Welcome to {{app_name}}!",
    "body": "Hi {{name}},\n\nWelcome to our platform! Click here: {{link}}",
    "channel": "email",
    "language": "en",
    "version": "1.0.0",
    "variables": ["name", "link", "app_name"]
  }
}
```

#### Render Template

```http
POST /api/v1/templates/render
Authorization: Bearer {jwt_token}
Content-Type: application/json

{
  "template_code": "welcome_email",
  "variables": {
    "name": "John Doe",
    "link": "https://example.com/verify",
    "app_name": "NotificationApp"
  }
}

Response: 200 OK
{
  "status": "success",
  "data": {
    "subject": "Welcome to NotificationApp!",
    "body": "Hi John Doe,\n\nWelcome to our platform! Click here: https://example.com/verify"
  }
}
```

#### Update Template

```http
PUT /api/v1/templates/{template_id}
Authorization: Bearer {jwt_token}
Content-Type: application/json

{
  "subject": "Updated subject",
  "body": "Updated body with {{name}}",
  "version": "1.1.0"
}

Response: 200 OK
{
  "status": "success",
  "data": {
    "template_id": "uuid",
    "version": "1.1.0",
    "updated_at": "2025-11-10T12:40:00Z"
  },
  "message": "Template updated successfully"
}
```

#### Delete Template

```http
DELETE /api/v1/templates/{template_id}
Authorization: Bearer {jwt_token}

Response: 200 OK
{
  "status": "success",
  "message": "Template deleted successfully"
}
```

## 7. Data Flow

### 7.1. Send Notification Flow

1. Client sends POST to `/api/v1/notifications/`
2. API Gateway validates request, checks idempotency, rate limit
3. Gateway saves notification (status: `pending`)
4. Gateway publishes message to RabbitMQ queue (email/push)
5. Worker service consumes message
6. Worker fetches template from Template Service
7. Worker renders template with variables
8. Worker sends notification via SMTP/FCM (with retry & circuit breaker)
9. Worker updates status in API Gateway (status: `sent` or `failed`)
10. Failed messages after max retries go to `failed.queue`

### 7.2. Authentication Flow

1. User registers via User Service
2. User logs in with credentials
3. User Service returns JWT token
4. Client includes token in `Authorization: Bearer {token}` header
5. API Gateway validates token on every request

## 8. Naming Conventions

### 8.1. API Endpoints

### 6.2. Authentication Flow

1. User registers via User Service
2. User logs in with credentials
3. User Service returns JWT token
4. Client includes token in `Authorization: Bearer {token}` header
5. API Gateway validates token on every request

## 7. Naming Conventions

### 7.1. API Endpoints

- Use kebab-case for URLs: `/api/v1/notifications/send`
- Use plural nouns for resources: `/users`, `/templates`
- Version APIs: `/api/v1/`, `/api/v2/`

### 7.2. Code Variables & Functions

- **Python Services**: Use `snake_case` for variables, functions, parameters
- **Other Languages**: Follow language-specific conventions (e.g., camelCase for JavaScript)
- **Database Columns**: Use `snake_case` across all services for consistency

### 7.3. Environment Variables

- Use UPPER_SNAKE_CASE: `DATABASE_URL`, `SMTP_HOST`, `JWT_SECRET_KEY`

### 7.4. Message Queue Names

- Use dot notation: `email.queue`, `push.queue`, `failed.queue`

## 8. Environment Configuration

### 8.1. Required Environment Variables

**Database:**

```
DATABASE_URL=postgresql://user:pass@host:5432/dbname
```

**Redis:**

```
REDIS_URL=redis://redis:6380
```

**RabbitMQ:**

```
RABBITMQ_URL=amqp://admin:admin@rabbitmq:5672/
```

**JWT Authentication:**

```
SECRET_KEY=your-secret-key-64-chars-min
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

**SMTP (Email Service):**

```
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM=noreply@yourapp.com
```

**FCM (Push Service):**

```
FCM_CREDENTIALS_FILE=/app/fcm-credentials.json
```

**Circuit Breaker:**

```
CIRCUIT_BREAKER_THRESHOLD=5
CIRCUIT_BREAKER_TIMEOUT=60
```

**Retry Configuration:**

```
MAX_RETRIES=3
RETRY_BASE_DELAY=2
RETRY_MAX_DELAY=60
```

## 10. Testing Standards

### 10.1. Unit Tests

- **Coverage**: Minimum 70% code coverage
- **Scope**: Test individual functions, classes, methods in isolation
- **Mocking**: Mock external dependencies (database, Redis, RabbitMQ, HTTP calls)

### 9.2. Integration Tests

- **Scope**: Test service interactions (e.g., API Gateway → User Service)
- **Database**: Use test databases, not production
- **Cleanup**: Reset database state after each test

### 9.3. End-to-End Tests

- **Scope**: Test complete flows (user registration → notification sent)
- **Environment**: Use docker-compose test environment
- **Validation**: Verify emails sent, status updated, queues processed

### 10.4. Test Checklist

- [ ] User registration and login
- [ ] JWT authentication enforced
- [ ] Template creation and rendering
- [ ] Email notification sent
- [ ] Push notification sent
- [ ] Rate limiting (101st request returns 429)
- [ ] Idempotency (duplicate request returns 409)
- [ ] Circuit breaker triggers after 5 failures
- [ ] Retry with exponential backoff
- [ ] Failed messages go to dead letter queue
- [ ] Health checks return correct status
- [ ] Correlation IDs propagate

## 11. Deployment

### 11.1. Local Development

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### 11.2. Production Considerations

- Use managed services for PostgreSQL, Redis, RabbitMQ when possible
- Implement horizontal scaling for worker services
- Set up monitoring and alerting (Prometheus, Grafana, ELK Stack)
- Configure log aggregation
- Use secrets management (e.g., AWS Secrets Manager, HashiCorp Vault)
- Implement CI/CD pipelines for automated testing and deployment

## 12. Performance Requirements

- **Throughput**: Handle 1,000+ notifications per minute
- **Response Time**: API Gateway responds in < 100ms
- **Availability**: 99.5% uptime
- **Delivery Rate**: 99.5% successful notification delivery
- **Scalability**: Services must support horizontal scaling

## 13. Security Guidelines

### 13.1. Authentication

- All endpoints (except `/health`, `/register`, `/login`) require JWT authentication
- Tokens expire after 30 minutes (configurable)
- Use strong secret keys (minimum 64 characters)

### 12.2. Data Protection

- Never log sensitive data (passwords, tokens, API keys)
- Hash passwords using bcrypt (cost factor ≥ 12)
- Use HTTPS in production
- Store credentials in environment variables, never in code

### 12.3. Input Validation

- Validate all input data
- Sanitize user-provided content in templates
- Implement request size limits
- Use parameterized queries to prevent SQL injection

### 12.4. Rate Limiting & Throttling

- Implement rate limiting on all public endpoints
- Use exponential backoff for retries
- Monitor for suspicious activity

## 14. Monitoring & Observability

### 14.1. Logging

- Use structured JSON logging
- Include correlation IDs in all logs
- Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
- Centralize logs using ELK Stack or similar

### 14.2. Metrics to Track

- Request rate per endpoint
- Response times (p50, p95, p99)
- Error rates per service
- Queue lengths and processing times
- Circuit breaker state changes
- Database connection pool usage
- Cache hit/miss rates

### 14.3. Health Monitoring

- Implement `/health` endpoints on all services
- Monitor dependencies (database, Redis, RabbitMQ)
- Set up alerts for service degradation

## 15. Documentation Requirements

Every service must provide:

1. **README.md**: Setup instructions, dependencies, how to run locally
2. **API Documentation**: OpenAPI/Swagger specification
3. **Environment Variables**: List of required and optional env vars
4. **Architecture Diagram**: Service's internal architecture
5. **Database Schema**: Tables, relationships, indexes

## 16. Contribution Guidelines

Refer to the `CONTRIBUTING.md` file for detailed guidelines on:

- Code style and standards
- Pull request process
- Branching strategy
- Commit message format
- Code review guidelines
- Testing requirements

## 17. Additional Resources

- **System Architecture**: See `ARCHITECTURE.txt` for detailed diagrams
- **API Testing**: See `README.md` for example API calls
- **Development Setup**: See individual service READMEs

---

**Document Version:** 2.0  
**Last Updated:** November 10, 2025  
**Team:** Group 21
