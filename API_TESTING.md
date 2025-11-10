# API Testing Guide

## Test the Complete Notification System

### 1. Start the System

```bash
./setup.sh
# OR
docker-compose up -d
```

### 2. Test User Service

#### Register a User

```bash
curl -X POST http://localhost:8001/users/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "email": "test@example.com",
    "password": "testpassword123",
    "push_token": "test_device_token_12345",
    "preferences": {
      "email": true,
      "push": true
    }
  }'
```

Expected Response:

```json
{
  "success": true,
  "message": "User registered successfully",
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "John Doe",
    "email": "test@example.com",
    "push_token": "test_device_token_12345",
    "is_active": true,
    "created_at": "2025-11-10T...",
    "updated_at": "2025-11-10T..."
  }
}
```

#### Login

```bash
curl -X POST http://localhost:8001/users/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=test@example.com&password=testpass123"
```

Expected Response:

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

#### Get User Info

```bash
TOKEN="<your_token_here>"
USER_ID="<user_uuid_from_registration>"

# Example:
TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0QGV4YW1wbGUuY29tIiwidXNlcl9pZCI6ImRlYjRhZTI4LTRlY2QtNDYwNS04NzQ2LTdkMGNkMjRiZTNmMCIsImV4cCI6MTc2MjgwMDcyN30.7k17llcXD0JwS32A3twJIXMvHoEulW6MPy0WqF2sOHo"
USER_ID="deb4ae28-4ecd-4605-8746-7d0cd24be3f0"

curl -X GET "http://localhost:8001/users/$USER_ID" \
  -H "Authorization: Bearer $TOKEN"
```

#### Get Notification Preferences

```bash
# List all notification preferences for a user
curl -X GET "http://localhost:8001/users/$USER_ID/preferences"
```

Expected Response:

```json
{
  "success": true,
  "message": "Preferences retrieved successfully",
  "data": [
    {
      "id": 1,
      "user_id": "deb4ae28-4ecd-4605-8746-7d0cd24be3f0",
      "channel": "email",
      "enabled": true,
      "preferences": {},
      "created_at": "2025-11-10T...",
      "updated_at": "2025-11-10T..."
    },
    {
      "id": 2,
      "user_id": "deb4ae28-4ecd-4605-8746-7d0cd24be3f0",
      "channel": "push",
      "enabled": true,
      "preferences": {},
      "created_at": "2025-11-10T...",
      "updated_at": "2025-11-10T..."
    }
  ]
}
```

#### Create Additional Notification Preference

```bash
# Note: Preferences for email/push are created during registration
# This endpoint is for adding additional custom preferences
curl -X POST "http://localhost:8001/users/$USER_ID/preferences" \
  -H "Content-Type: application/json" \
  -d '{
    "channel": "sms",
    "enabled": true,
    "preferences": {
      "frequency": "daily_digest",
      "quiet_hours": {
        "start": "22:00",
        "end": "08:00"
      }
    }
  }'
```

#### Update Notification Preference

```bash
# Update an existing preference by preference_id
PREFERENCE_ID="1"

curl -X PUT "http://localhost:8001/users/preferences/$PREFERENCE_ID" \
  -H "Content-Type: application/json" \
  -d '{
    "enabled": false,
    "preferences": {
      "frequency": "weekly"
    }
  }'
```

### 3. Test Template Service

#### Create Email Template

```bash
curl -X POST http://localhost:8002/templates/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "welcome_email",
    "channel": "email",
    "language": "en",
    "subject": "Welcome to Our Platform, {{name}}!",
    "body": "<html><body><h1>Hello {{name}}</h1><p>Welcome! Your email is {{email}}.</p><p>Click <a href=\"{{link}}\">here</a> to get started.</p></body></html>",
    "variables": ["name", "email", "link"]
  }'
```

#### Create Push Template

```bash
curl -X POST http://localhost:8002/templates/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "order_notification",
    "channel": "push",
    "language": "en",
    "subject": "Order #{{order_id}} Update",
    "body": "Your order #{{order_id}} has been {{status}}. Track it here: {{tracking_url}}",
    "variables": ["order_id", "status", "tracking_url"]
  }'
```

#### List All Templates

```bash
curl http://localhost:8002/templates/?limit=10&skip=0
```

#### Get Template by Name

```bash
curl "http://localhost:8002/templates/name/welcome_email?language=en"
```

#### Render Template

```bash
curl -X POST http://localhost:8002/templates/render \
  -H "Content-Type: application/json" \
  -d '{
    "template_name": "welcome_email",
    "language": "en",
    "variables": {
      "name": "John Doe",
      "email": "john@example.com",
      "link": "https://example.com/welcome"
    }
  }'
```

### 4. Test API Gateway - Send Notifications

#### Send Single Email Notification

```bash
# Use UUID for user_id (from registration response)
curl -X POST http://localhost:8000/notifications/send \
  -H "Content-Type: application/json" \
  -H "X-Correlation-ID: test-email-001" \
  -d '{
    "notification_type": "email",
    "user_id": "deb4ae28-4ecd-4605-8746-7d0cd24be3f0",
    "template_code": "welcome_email",
    "variables": {
      "name": "John Doe",
      "link": "https://example.com/welcome",
      "meta": {}
  },
    "request_id": "unique-req-001",
    "priority": 0
  }'
```

Expected Response:

```json
{
  "success": true,
  "message": "Notification queued successfully",
  "data": {
    "id": 1,
    "request_id": "unique-req-001",
    "correlation_id": "test-email-001",
    "user_id": "deb4ae28-4ecd-4605-8746-7d0cd24be3f0",
    "notification_type": "email",
    "template_code": "welcome_email",
    "recipient": "test@example.com",
    "status": "queued",
    "retry_count": 0,
    "created_at": "2025-11-10T...",
    "updated_at": "2025-11-10T..."
  }
}
```

#### Send Single Push Notification

```bash
curl -X POST http://localhost:8000/notifications/send \
  -H "Content-Type: application/json" \
  -H "X-Correlation-ID: test-push-001" \
  -d '{
    "notification_type": "push",
    "user_id": "deb4ae28-4ecd-4605-8746-7d0cd24be3f0",
    "template_code": "order_notification",
    "variables": {
      "name": "John Doe",
      "link": "https://example.com/orders/12345",
      "meta": {
        "order_id": "ORD-12345",
        "status": "shipped",
        "tracking_url": "https://example.com/track/12345"
      }
    },
    "request_id": "unique-req-002",
    "priority": 1
  }'
```

#### Test Idempotency (Same request_id)

```bash
# Send the same request twice with same request_id
curl -X POST http://localhost:8000/notifications/send \
  -H "Content-Type: application/json" \
  -d '{
    "notification_type": "email",
    "user_id": "deb4ae28-4ecd-4605-8746-7d0cd24be3f0",
    "template_code": "welcome_email",
    "variables": {
      "name": "John",
      "link": "https://example.com/welcome",
      "meta": {}
    },
    "request_id": "idempotency-test-001"
  }'

# Second request should return cached result
curl -X POST http://localhost:8000/notifications/send \
  -H "Content-Type: application/json" \
  -d '{
    "notification_type": "email",
    "user_id": "deb4ae28-4ecd-4605-8746-7d0cd24be3f0",
    "template_code": "welcome_email",
    "variables": {
      "name": "John",
      "link": "https://example.com/welcome",
      "meta": {}
    },
    "request_id": "idempotency-test-001"
  }'
```

#### Send Bulk Notifications

```bash
# First, create more users (save their UUIDs from responses)
for i in {2..5}; do
  curl -X POST http://localhost:8001/users/register \
    -H "Content-Type: application/json" \
    -d "{
      \"name\": \"User $i\",
      \"email\": \"user$i@example.com\",
      \"password\": \"pass123\",
      \"preferences\": {
        \"email\": true,
        \"push\": true
      }
    }"
done

# Send bulk notification (replace with actual UUIDs from registration)
curl -X POST http://localhost:8000/notifications/send/bulk \
  -H "Content-Type: application/json" \
  -d '{
    "user_ids": [
      "deb4ae28-4ecd-4605-8746-7d0cd24be3f0",
      "<uuid-2>",
      "<uuid-3>",
      "<uuid-4>",
      "<uuid-5>"
    ],
    "notification_type": "email",
    "template_code": "welcome_email",
    "variables": {
      "name": "Valued Customer",
      "link": "https://example.com/welcome",
      "meta": {}
    }
  }'
```

### 5. Query Notification Status

#### Get Notification by ID

```bash
curl http://localhost:8000/notifications/1
```

#### Get Notification by Request ID

```bash
curl http://localhost:8000/notifications/request/unique-req-001
```

#### Get All Notifications for a User

```bash
# Use UUID instead of integer ID
curl "http://localhost:8000/notifications/user/deb4ae28-4ecd-4605-8746-7d0cd24be3f0?limit=10&skip=0"
```

#### Filter by Status

```bash
curl "http://localhost:8000/notifications/user/deb4ae28-4ecd-4605-8746-7d0cd24be3f0?status=sent"
```

#### Filter by Channel

```bash
curl "http://localhost:8000/notifications/user/deb4ae28-4ecd-4605-8746-7d0cd24be3f0?channel=email"
```

### 6. Health Checks

```bash
# Check all services
curl http://localhost:8000/health  # API Gateway
curl http://localhost:8001/health  # User Service
curl http://localhost:8002/health  # Template Service
```

### 7. Monitor Queues

Open RabbitMQ Management UI:

```
http://localhost:15672
Username: admin
Password: admin
```

Check:

- Queue depth (email.queue, push.queue, failed.queue)
- Message rates
- Consumer status
- Dead letter queue

### 8. View Logs

```bash
# View all logs
docker-compose logs -f

# View specific service
docker-compose logs -f api-gateway
docker-compose logs -f email-service
docker-compose logs -f push-service
docker-compose logs -f user-service
docker-compose logs -f template-service

# Search for correlation ID
docker-compose logs | grep "test-email-001"
```

### 9. Test Rate Limiting

```bash
# Send 101 requests quickly (limit is 100/minute)
for i in {1..101}; do
  curl -X POST http://localhost:8000/notifications/send \
    -H "Content-Type: application/json" \
    -d "{
      \"notification_type\": \"email\",
      \"user_id\": \"deb4ae28-4ecd-4605-8746-7d0cd24be3f0\",
      \"template_code\": \"welcome_email\",
      \"variables\": {
        \"name\": \"User\",
        \"link\": \"https://example.com\",
        \"meta\": {}
      },
      \"request_id\": \"rate-test-$i\"
    }"
  echo ""
done

# The 101st request should return 429 Too Many Requests
```

### 10. Test Error Handling

#### Non-existent User

```bash
curl -X POST http://localhost:8000/notifications/send \
  -H "Content-Type: application/json" \
  -d '{
    "notification_type": "email",
    "user_id": "00000000-0000-0000-0000-000000000000",
    "template_code": "welcome_email",
    "variables": {
      "name": "Test",
      "link": "https://example.com",
      "meta": {}
    },
    "request_id": "error-test-001"
  }'
```

#### Non-existent Template

```bash
curl -X POST http://localhost:8000/notifications/send \
  -H "Content-Type: application/json" \
  -d '{
    "notification_type": "email",
    "user_id": "deb4ae28-4ecd-4605-8746-7d0cd24be3f0",
    "template_code": "nonexistent_template",
    "variables": {
      "name": "Test",
      "link": "https://example.com",
      "meta": {}
    },
    "request_id": "error-test-002"
  }'
```

### 11. Performance Test

```bash
# Install apache bench if not available
# sudo apt-get install apache2-utils

# Create test data file
cat > notification.json << EOF
{
  "notification_type": "email",
  "user_id": "deb4ae28-4ecd-4605-8746-7d0cd24be3f0",
  "template_code": "welcome_email",
  "variables": {
    "name": "LoadTest",
    "link": "https://example.com",
    "meta": {}
  },
  "request_id": "load-test-001"
}
EOF

# Run load test: 1000 requests, 10 concurrent
ab -n 1000 -c 10 -p notification.json -T application/json \
  http://localhost:8000/notifications/send
```

## Expected Results

### ✅ Success Criteria

1. **Registration**: User registered successfully
2. **Login**: JWT token received
3. **Template Creation**: Templates created with version 1
4. **Template Rendering**: Variables correctly substituted
5. **Notification Queued**: Status changes from pending → queued
6. **Email Sent**: Check email service logs for "Email sent successfully"
7. **Push Sent**: Check push service logs for "Push notification sent"
8. **Idempotency**: Second identical request returns cached result
9. **Rate Limiting**: 101st request rejected with 429
10. **Health Checks**: All services return "healthy"

### 📊 Monitor Performance

- API Gateway response time: < 100ms
- Notification queuing: < 50ms
- Email delivery: 2-10 seconds (depends on SMTP)
- Push delivery: 1-5 seconds
- Queue throughput: 1000+ messages/minute

## Troubleshooting

### Emails not sending?

```bash
# Check email service logs
docker-compose logs email-service

# Verify SMTP settings in .env
cat .env | grep SMTP

# Test SMTP connection manually
docker-compose exec email-service python -c "
import smtplib
server = smtplib.SMTP('smtp.gmail.com', 587)
server.starttls()
print('SMTP connection successful!')
server.quit()
"
```

### Push notifications not sending?

```bash
# Check if running in simulation mode
docker-compose logs push-service | grep "simulation"

# Verify FCM credentials exist
ls -la fcm-credentials.json
```

### Queues backing up?

```bash
# Scale workers
docker-compose up -d --scale email-service=3 --scale push-service=3

# Check queue depth in RabbitMQ UI
open http://localhost:15672
```
