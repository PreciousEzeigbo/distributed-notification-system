# 🚀 Complete API Testing Guide - Notification System

Hey! So you want to test this bad boy? I've got you covered. This guide walks you through every single endpoint in the system. Let's make some magic happen! ✨

---

## 📋 Table of Contents

1. [Getting Started](#getting-started)
2. [User Service API](#user-service-api)
3. [Template Service API](#template-service-api)
4. [API Gateway - Notifications](#api-gateway)
5. [FCM Token Management](#fcm-token-management)
6. [Testing Scenarios](#testing-scenarios)
7. [Troubleshooting](#troubleshooting)

---

## 🏁 Getting Started

### Fire Up the System

```bash
# Start everything
docker-compose up -d

# Check if services are healthy
docker-compose ps
```

You should see all services as **healthy**. If not, give them a minute or check the logs.

### Base URLs

```
API Gateway:      http://localhost:8000
User Service:     http://localhost:8001
Template Service: http://localhost:8002
RabbitMQ UI:      http://localhost:15672 (admin/admin)
```

---

## 👤 User Service API

Base URL: `http://localhost:8001`

### 1. Register a New User

**Endpoint:** `POST /users/register`

This is where users sign up. You'll get back a UUID - save it, you'll need it!

```bash
curl -X POST http://localhost:8001/users/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Alice Wonder",
    "email": "alice@example.com",
    "password": "securepass123",
    "preferences": {
      "email": true,
      "push": true
    }
  }' | jq .
```

**What you get back:**

```json
{
  "success": true,
  "message": "User registered successfully",
  "data": {
    "id": "cc8fdc7f-23e4-4181-a557-fc7f18cd1889",
    "name": "Alice Wonder",
    "email": "alice@example.com",
    "push_token": null,
    "is_active": true,
    "created_at": "2025-11-11T19:55:34.972631Z",
    "updated_at": "2025-11-11T19:55:34.972647Z"
  }
}
```

💡 **Pro tip:** The `push_token` is null because you haven't registered your device yet. We'll do that later!

---

### 2. Login (Get Your Access Token)

**Endpoint:** `POST /users/login`

You need this token for authenticated endpoints. Keep it safe!

```bash
curl -X POST http://localhost:8001/users/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=alice@example.com&password=securepass123" | jq .
```

**Response:**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhbGljZUBl...",
  "token_type": "bearer"
}
```

Now save that token:

```bash
TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhbGljZUBl..."
USER_ID="cc8fdc7f-23e4-4181-a557-fc7f18cd1889"
```

---

### 3. Get Current User Info

**Endpoint:** `GET /users/me`

Want to see your profile? Here's how:

```bash
curl -X GET http://localhost:8001/users/me \
  -H "Authorization: Bearer $TOKEN" | jq .
```

**Response:**

```json
{
  "success": true,
  "message": "User retrieved successfully",
  "data": {
    "id": "cc8fdc7f-23e4-4181-a557-fc7f18cd1889",
    "name": "Alice Wonder",
    "email": "alice@example.com",
    "push_token": null,
    "is_active": true,
    "created_at": "2025-11-11T19:55:34.972631Z",
    "updated_at": "2025-11-11T19:55:34.972647Z"
  }
}
```

---

### 4. Get User by ID

**Endpoint:** `GET /users/{user_id}`

Lookup any user by their UUID (doesn't need auth):

```bash
curl -X GET "http://localhost:8001/users/$USER_ID" | jq .
```

---

### 5. Get User by Email

**Endpoint:** `GET /users/email/{email}`

This is handy for internal service communication:

```bash
curl -X GET "http://localhost:8001/users/email/alice@example.com" | jq .
```

---

### 6. Update User Profile

**Endpoint:** `PUT /users/{user_id}`

Let's say Alice wants to change her name:

```bash
curl -X PUT "http://localhost:8001/users/$USER_ID" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Alice Wonderland"
  }' | jq .
```

You can only update your own profile (security, ya know? 🔒).

---

### 7. List All Users

**Endpoint:** `GET /users/`

Want to see everyone? (Requires auth)

```bash
curl -X GET "http://localhost:8001/users/?skip=0&limit=10" \
  -H "Authorization: Bearer $TOKEN" | jq .
```

**Query Parameters:**
- `skip`: Number of records to skip (default: 0)
- `limit`: Max records to return (default: 100, max: 1000)

---

### 8. Manage Notification Preferences

#### Get All Preferences

**Endpoint:** `GET /users/{user_id}/preferences`

```bash
curl -X GET "http://localhost:8001/users/$USER_ID/preferences" | jq .
```

**Response:**

```json
{
  "success": true,
  "message": "Notification preferences retrieved successfully",
  "data": [
    {
      "id": 1,
      "user_id": "cc8fdc7f-23e4-4181-a557-fc7f18cd1889",
      "channel": "email",
      "enabled": true,
      "preferences": {},
      "created_at": "2025-11-11T19:55:35.123Z",
      "updated_at": "2025-11-11T19:55:35.123Z"
    },
    {
      "id": 2,
      "user_id": "cc8fdc7f-23e4-4181-a557-fc7f18cd1889",
      "channel": "push",
      "enabled": true,
      "preferences": {},
      "created_at": "2025-11-11T19:55:35.456Z",
      "updated_at": "2025-11-11T19:55:35.456Z"
    }
  ]
}
```

#### Create New Preference

**Endpoint:** `POST /users/{user_id}/preferences`

Add a new notification channel (like SMS):

```bash
curl -X POST "http://localhost:8001/users/$USER_ID/preferences" \
  -H "Content-Type: application/json" \
  -d '{
    "channel": "sms",
    "enabled": true,
    "preferences": {
      "quiet_hours": {
        "start": "22:00",
        "end": "08:00"
      }
    }
  }' | jq .
```

#### Update Preference

**Endpoint:** `PUT /users/preferences/{preference_id}`

Let's disable email notifications:

```bash
curl -X PUT "http://localhost:8001/users/preferences/1" \
  -H "Content-Type: application/json" \
  -d '{
    "enabled": false
  }' | jq .
```

#### Delete Preference

**Endpoint:** `DELETE /users/preferences/{preference_id}`

```bash
curl -X DELETE "http://localhost:8001/users/preferences/3" | jq .
```

---

## 📱 FCM Token Management

This is how mobile apps register for push notifications. It's super important!

### 1. Register FCM Token

**Endpoint:** `POST /users/me/fcm-token`

After a user logs in on their mobile app, the app needs to register its Firebase device token:

```bash
curl -X POST http://localhost:8001/users/me/fcm-token \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "fcm_token": "eXuMZLqSTg6Wa5KQqJvhBN:APA91bF2wBxH7KnZqQ_your_actual_firebase_token_here"
  }' | jq .
```

**Response:**

```json
{
  "success": true,
  "message": "FCM token registered successfully",
  "data": {
    "id": "cc8fdc7f-23e4-4181-a557-fc7f18cd1889",
    "name": "Alice Wonder",
    "email": "alice@example.com",
    "push_token": "eXuMZLqSTg6Wa5KQqJvhBN:APA91bF2wBxH7KnZqQ_your_actual_firebase_token_here",
    "is_active": true
  }
}
```

💡 **When to call this:**
- Right after user logs in on mobile
- When Firebase refreshes the token
- When user switches devices

---

### 2. Update FCM Token

**Endpoint:** `POST /users/me/fcm-token` (same endpoint!)

Firebase sometimes refreshes tokens. Just call the same endpoint with the new token:

```bash
curl -X POST http://localhost:8001/users/me/fcm-token \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "fcm_token": "NEW_TOKEN_xyz789:APA91bF2wBxH7KnZqQ_refreshed_token"
  }' | jq .
```

---

### 3. Remove FCM Token (Logout)

**Endpoint:** `DELETE /users/me/fcm-token`

When user logs out, remove their token so they don't get notifications:

```bash
curl -X DELETE http://localhost:8001/users/me/fcm-token \
  -H "Authorization: Bearer $TOKEN" | jq .
```

**Response:**

```json
{
  "success": true,
  "message": "FCM token removed successfully",
  "data": null
}
```

---

## 📝 Template Service API

Base URL: `http://localhost:8002`

Templates are the blueprint for your notifications. Let's create some!

### 1. Create Email Template

**Endpoint:** `POST /templates/`

```bash
curl -X POST http://localhost:8002/templates/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "welcome_email",
    "channel": "email",
    "language": "en",
    "subject": "Welcome to NotifyHub, {{name}}! 🎉",
    "body": "<html><body><h1>Hey {{name}}!</h1><p>We are so excited to have you. Your email is <strong>{{email}}</strong>.</p><p>Get started by clicking <a href=\"{{link}}\">here</a>.</p><footer>Cheers,<br>The Team</footer></body></html>",
    "variables": ["name", "email", "link"]
  }' | jq .
```

**Response:**

```json
{
  "success": true,
  "message": "Template created successfully",
  "data": {
    "id": 1,
    "name": "welcome_email",
    "channel": "email",
    "language": "en",
    "subject": "Welcome to NotifyHub, {{name}}! 🎉",
    "body": "<html>...</html>",
    "variables": ["name", "email", "link"],
    "version": 1,
    "is_active": true,
    "created_at": "2025-11-11T20:00:00.000Z"
  }
}
```

---

### 2. Create Push Template

**Endpoint:** `POST /templates/`

```bash
curl -X POST http://localhost:8002/templates/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "order_shipped",
    "channel": "push",
    "language": "en",
    "subject": "📦 Order #{{order_id}} Shipped!",
    "body": "Your order has been shipped! Track it here: {{tracking_url}}",
    "variables": ["order_id", "tracking_url"]
  }' | jq .
```

---

### 3. List All Templates

**Endpoint:** `GET /templates/`

```bash
curl "http://localhost:8002/templates/?skip=0&limit=10" | jq .
```

**Query Parameters:**
- `skip`: Pagination offset (default: 0)
- `limit`: Records per page (default: 10)
- `channel`: Filter by channel (email, push, sms)
- `language`: Filter by language (en, es, fr, etc.)

---

### 4. Get Template by Name

**Endpoint:** `GET /templates/name/{name}`

```bash
curl "http://localhost:8002/templates/name/welcome_email?language=en" | jq .
```

---

### 5. Get Template by ID

**Endpoint:** `GET /templates/{template_id}`

```bash
curl "http://localhost:8002/templates/1" | jq .
```

---

### 6. Update Template

**Endpoint:** `PUT /templates/{template_id}`

Let's update our welcome email:

```bash
curl -X PUT "http://localhost:8002/templates/1" \
  -H "Content-Type: application/json" \
  -d '{
    "subject": "Welcome Aboard, {{name}}! 🚀",
    "body": "<html><body><h1>Welcome {{name}}!</h1><p>Updated content here...</p></body></html>"
  }' | jq .
```

💡 **Note:** This creates version 2 of the template. Old version is archived but kept for auditing.

---

### 7. Delete Template

**Endpoint:** `DELETE /templates/{template_id}`

```bash
curl -X DELETE "http://localhost:8002/templates/1" | jq .
```

⚠️ **Warning:** This soft-deletes the template (sets `is_active = false`). It won't actually delete data.

---

### 8. Render Template

**Endpoint:** `POST /templates/render`

Want to see what your template looks like with real data?

```bash
curl -X POST http://localhost:8002/templates/render \
  -H "Content-Type: application/json" \
  -d '{
    "template_name": "welcome_email",
    "language": "en",
    "variables": {
      "name": "Alice Wonder",
      "email": "alice@example.com",
      "link": "https://app.notifyhub.com/welcome"
    }
  }' | jq .
```

**Response:**

```json
{
  "success": true,
  "message": "Template rendered successfully",
  "data": {
    "subject": "Welcome to NotifyHub, Alice Wonder! 🎉",
    "body": "<html><body><h1>Hey Alice Wonder!</h1><p>We are so excited to have you. Your email is <strong>alice@example.com</strong>.</p><p>Get started by clicking <a href=\"https://app.notifyhub.com/welcome\">here</a>.</p></body></html>"
  }
}
```

---

## 🔔 API Gateway - Notifications

Base URL: `http://localhost:8000`

This is where the magic happens. Send notifications to your users!

### 1. Health Check

**Endpoint:** `GET /health`

Always good to check if everything's running:

```bash
curl http://localhost:8000/health | jq .
```

**Response:**

```json
{
  "success": true,
  "message": "All services healthy",
  "data": {
    "api_gateway": "healthy",
    "user_service": "healthy",
    "template_service": "healthy",
    "rabbitmq": "connected",
    "redis": "connected",
    "database": "connected"
  }
}
```

---

### 2. Root Endpoint

**Endpoint:** `GET /`

```bash
curl http://localhost:8000/ | jq .
```

Just a friendly welcome message with API info.

---

### 3. Send Single Notification

**Endpoint:** `POST /notifications/send`

This is the main event! Let's send a notification:

```bash
curl -X POST http://localhost:8000/notifications/send \
  -H "Content-Type: application/json" \
  -H "X-Correlation-ID: test-001" \
  -d '{
    "notification_type": "email",
    "user_id": "cc8fdc7f-23e4-4181-a557-fc7f18cd1889",
    "template_code": "welcome_email",
    "variables": {
      "name": "Alice Wonder",
      "email": "alice@example.com",
      "link": "https://app.notifyhub.com/welcome"
    },
    "request_id": "unique-req-001",
    "priority": 0
  }' | jq .
```

**Request Fields:**
- `notification_type`: "email" or "push"
- `user_id`: User's UUID (from registration)
- `template_code`: Template name you created
- `variables`: Data to fill in the template
- `request_id`: Unique ID for idempotency (optional)
- `priority`: 0-10, higher = more urgent (optional, default: 0)

**Response:**

```json
{
  "success": true,
  "message": "Notification queued successfully",
  "data": {
    "id": 1,
    "request_id": "unique-req-001",
    "correlation_id": "test-001",
    "user_id": "cc8fdc7f-23e4-4181-a557-fc7f18cd1889",
    "notification_type": "email",
    "template_code": "welcome_email",
    "recipient": "alice@example.com",
    "status": "queued",
    "priority": 0,
    "retry_count": 0,
    "created_at": "2025-11-11T20:15:00.000Z",
    "updated_at": "2025-11-11T20:15:00.000Z"
  }
}
```

💡 **Status Flow:** pending → queued → processing → sent (or failed)

---

### 4. Send Push Notification

**Endpoint:** `POST /notifications/send`

Same endpoint, just change the type to "push":

```bash
curl -X POST http://localhost:8000/notifications/send \
  -H "Content-Type: application/json" \
  -d '{
    "notification_type": "push",
    "user_id": "cc8fdc7f-23e4-4181-a557-fc7f18cd1889",
    "template_code": "order_shipped",
    "variables": {
      "order_id": "ORD-12345",
      "tracking_url": "https://track.example.com/12345"
    },
    "priority": 5
  }' | jq .
```

⚠️ **Important:** User must have registered their FCM token first!

---

### 5. Send Bulk Notifications

**Endpoint:** `POST /notifications/send/bulk`

Need to notify multiple users at once? I got you:

```bash
curl -X POST http://localhost:8000/notifications/send/bulk \
  -H "Content-Type: application/json" \
  -d '{
    "user_ids": [
      "cc8fdc7f-23e4-4181-a557-fc7f18cd1889",
      "deb4ae28-4ecd-4605-8746-7d0cd24be3f0",
      "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
    ],
    "notification_type": "email",
    "template_code": "weekly_newsletter",
    "variables": {
      "week": "Week 45",
      "link": "https://newsletter.example.com/week45"
    }
  }' | jq .
```

**Response:**

```json
{
  "success": true,
  "message": "Bulk notifications queued successfully",
  "data": {
    "queued": 3,
    "failed": 0,
    "notification_ids": [1, 2, 3]
  }
}
```

---

### 6. Get Notification by ID

**Endpoint:** `GET /notifications/{notification_id}`

Want to check on a specific notification?

```bash
curl "http://localhost:8000/notifications/1" | jq .
```

---

### 7. Get Notification by Request ID

**Endpoint:** `GET /notifications/request/{request_id}`

If you used a custom `request_id`, you can look it up:

```bash
curl "http://localhost:8000/notifications/request/unique-req-001" | jq .
```

---

### 8. Get User's Notifications

**Endpoint:** `GET /notifications/user/{user_id}`

See all notifications for a specific user:

```bash
curl "http://localhost:8000/notifications/user/$USER_ID?skip=0&limit=10" | jq .
```

**Query Parameters:**
- `skip`: Pagination offset
- `limit`: Results per page
- `status`: Filter by status (pending, queued, processing, sent, failed)
- `notification_type`: Filter by type (email, push)

**Examples:**

```bash
# Get only sent emails
curl "http://localhost:8000/notifications/user/$USER_ID?status=sent&notification_type=email" | jq .

# Get failed notifications
curl "http://localhost:8000/notifications/user/$USER_ID?status=failed" | jq .
```

---

## 🎯 Testing Scenarios

Let me show you some real-world scenarios to test.

### Scenario 1: New User Onboarding

```bash
# Step 1: User signs up
curl -X POST http://localhost:8001/users/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Bob Builder",
    "email": "bob@example.com",
    "password": "build123",
    "preferences": {"email": true, "push": true}
  }' | jq -r '.data.id' > user_id.txt

USER_ID=$(cat user_id.txt)

# Step 2: Send welcome email
curl -X POST http://localhost:8000/notifications/send \
  -H "Content-Type: application/json" \
  -d "{
    \"notification_type\": \"email\",
    \"user_id\": \"$USER_ID\",
    \"template_code\": \"welcome_email\",
    \"variables\": {
      \"name\": \"Bob Builder\",
      \"email\": \"bob@example.com\",
      \"link\": \"https://app.example.com/welcome\"
    }
  }" | jq .

# Step 3: Check notification status
sleep 5  # Give it time to process
curl "http://localhost:8000/notifications/user/$USER_ID" | jq .
```

---

### Scenario 2: Mobile App Login Flow

```bash
# Step 1: User logs in
TOKEN=$(curl -X POST http://localhost:8001/users/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=alice@example.com&password=securepass123" | jq -r '.access_token')

# Step 2: Mobile app registers FCM token
curl -X POST http://localhost:8001/users/me/fcm-token \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "fcm_token": "device_token_abc123xyz"
  }' | jq .

# Step 3: Send a push notification
curl -X POST http://localhost:8000/notifications/send \
  -H "Content-Type: application/json" \
  -d '{
    "notification_type": "push",
    "user_id": "cc8fdc7f-23e4-4181-a557-fc7f18cd1889",
    "template_code": "order_shipped",
    "variables": {
      "order_id": "ORD-98765",
      "tracking_url": "https://track.example.com/98765"
    }
  }' | jq .
```

---

### Scenario 3: Test Idempotency

Send the same request twice - you should get the same result:

```bash
# First request
curl -X POST http://localhost:8000/notifications/send \
  -H "Content-Type: application/json" \
  -d '{
    "notification_type": "email",
    "user_id": "cc8fdc7f-23e4-4181-a557-fc7f18cd1889",
    "template_code": "welcome_email",
    "variables": {"name": "Test", "email": "test@example.com", "link": "https://example.com"},
    "request_id": "idempotent-test-001"
  }' | jq '.data.id'

# Second request (same request_id)
curl -X POST http://localhost:8000/notifications/send \
  -H "Content-Type: application/json" \
  -d '{
    "notification_type": "email",
    "user_id": "cc8fdc7f-23e4-4181-a557-fc7f18cd1889",
    "template_code": "welcome_email",
    "variables": {"name": "Test", "email": "test@example.com", "link": "https://example.com"},
    "request_id": "idempotent-test-001"
  }' | jq '.data.id'

# Both should return the same notification ID!
```

---

### Scenario 4: Preference Management

```bash
# User wants to disable email notifications
USER_ID="cc8fdc7f-23e4-4181-a557-fc7f18cd1889"

# Get current preferences
curl "http://localhost:8001/users/$USER_ID/preferences" | jq '.data[] | select(.channel == "email")'

# Disable email notifications
PREF_ID=1  # Use the ID from above
curl -X PUT "http://localhost:8001/users/preferences/$PREF_ID" \
  -H "Content-Type: application/json" \
  -d '{"enabled": false}' | jq .

# Now try sending an email - it should respect the preference
curl -X POST http://localhost:8000/notifications/send \
  -H "Content-Type: application/json" \
  -d "{
    \"notification_type\": \"email\",
    \"user_id\": \"$USER_ID\",
    \"template_code\": \"welcome_email\",
    \"variables\": {\"name\": \"Test\", \"email\": \"test@example.com\", \"link\": \"https://example.com\"}
  }" | jq .
```

---

### Scenario 5: Error Handling

Let's test what happens when things go wrong:

```bash
# Test 1: Non-existent user
curl -X POST http://localhost:8000/notifications/send \
  -H "Content-Type: application/json" \
  -d '{
    "notification_type": "email",
    "user_id": "00000000-0000-0000-0000-000000000000",
    "template_code": "welcome_email",
    "variables": {"name": "Ghost", "email": "ghost@example.com", "link": "https://example.com"}
  }' | jq .

# Test 2: Non-existent template
curl -X POST http://localhost:8000/notifications/send \
  -H "Content-Type: application/json" \
  -d '{
    "notification_type": "email",
    "user_id": "cc8fdc7f-23e4-4181-a557-fc7f18cd1889",
    "template_code": "template_that_doesnt_exist",
    "variables": {"name": "Test"}
  }' | jq .

# Test 3: Invalid UUID format
curl -X GET "http://localhost:8001/users/not-a-valid-uuid" | jq .

# Test 4: Missing required field
curl -X POST http://localhost:8000/notifications/send \
  -H "Content-Type: application/json" \
  -d '{
    "notification_type": "email",
    "user_id": "cc8fdc7f-23e4-4181-a557-fc7f18cd1889"
  }' | jq .
```

---

## 🔍 Monitoring & Debugging

### Check Service Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f api-gateway
docker-compose logs -f email-service
docker-compose logs -f push-service

# Search for specific correlation ID
docker-compose logs | grep "test-001"

# Follow last 100 lines
docker-compose logs --tail=100 -f email-service
```

---

### RabbitMQ Management

Open in browser: http://localhost:15672

**Credentials:** admin / admin

**What to check:**
- **Queues:** See message counts in email.queue, push.queue, failed.queue
- **Consumers:** Make sure workers are connected
- **Message rates:** Incoming/outgoing messages per second
- **Dead letter queue:** Failed messages that need attention

---

### Database Queries

```bash
# Connect to API Gateway DB
docker-compose exec gateway-db psql -U api_gateway -d gateway_db

# Check notifications
SELECT id, user_id, notification_type, status, created_at 
FROM notifications 
ORDER BY created_at DESC 
LIMIT 10;

# Check failed notifications
SELECT id, user_id, notification_type, status, error_message, retry_count
FROM notifications
WHERE status = 'failed';

# Exit
\q
```

```bash
# Connect to User Service DB
docker-compose exec user-db psql -U user_service -d user_service_db

# Check users
SELECT id, name, email, push_token, is_active FROM users;

# Check preferences
SELECT u.email, np.channel, np.enabled 
FROM users u 
JOIN notification_preferences np ON u.id = np.user_id;

\q
```

---

### Performance Testing

```bash
# Install apache bench if you don't have it
# sudo apt-get install apache2-utils

# Create test payload
cat > test_notification.json << 'EOF'
{
  "notification_type": "email",
  "user_id": "cc8fdc7f-23e4-4181-a557-fc7f18cd1889",
  "template_code": "welcome_email",
  "variables": {
    "name": "LoadTest",
    "email": "test@example.com",
    "link": "https://example.com"
  }
}
EOF

# Run 1000 requests with 10 concurrent connections
ab -n 1000 -c 10 \
  -p test_notification.json \
  -T application/json \
  http://localhost:8000/notifications/send

# Check the results
# Look for:
# - Requests per second
# - Time per request
# - Failed requests (should be 0)
```

---

## 🐛 Troubleshooting

### Problem: "Service Unhealthy"

```bash
# Check which service is down
docker-compose ps

# Check logs
docker-compose logs [service-name]

# Restart specific service
docker-compose restart [service-name]

# Nuclear option: restart everything
docker-compose down && docker-compose up -d
```

---

### Problem: Emails Not Sending

```bash
# Check email service logs
docker-compose logs email-service | grep -i "error\|fail"

# Verify SMTP configuration
cat email-service/.env | grep SMTP

# Check if running in simulation mode
docker-compose logs email-service | grep "simulation"

# Test SMTP connection manually
docker-compose exec email-service python -c "
import smtplib
try:
    server = smtplib.SMTP('smtp.gmail.com', 587, timeout=10)
    server.starttls()
    print('✅ SMTP connection successful!')
    server.quit()
except Exception as e:
    print(f'❌ SMTP connection failed: {e}')
"
```

---

### Problem: Push Notifications Not Working

```bash
# Check if FCM credentials exist
ls -la push-service/fcm-credentials.json

# Check push service logs
docker-compose logs push-service | grep -i "fcm\|firebase"

# Verify user has FCM token
curl "http://localhost:8001/users/$USER_ID" | jq '.data.push_token'

# If null, user needs to register their token!
```

---

### Problem: RabbitMQ Connection Failed

```bash
# Check RabbitMQ status
docker-compose ps rabbitmq

# Check RabbitMQ logs
docker-compose logs rabbitmq

# Restart RabbitMQ
docker-compose restart rabbitmq

# Wait for it to be healthy
watch docker-compose ps rabbitmq
```

---

### Problem: Queue Backing Up

```bash
# Check queue depth
# Go to http://localhost:15672 and check queue lengths

# Scale up workers
docker-compose up -d --scale email-service=3 --scale push-service=3

# Check if workers are connected
docker-compose logs email-service | grep "Connected to RabbitMQ"
```

---

### Problem: High Response Times

```bash
# Check Redis connection
docker-compose exec redis redis-cli ping
# Should return: PONG

# Check database connections
docker-compose exec gateway-db pg_isready
docker-compose exec user-db pg_isready
docker-compose exec template-db pg_isready

# Monitor resource usage
docker stats

# If CPU/Memory high, consider scaling or upgrading resources
```

---

## 📊 Expected Performance

Here's what "good" looks like:

| Metric | Expected Value |
|--------|----------------|
| API Gateway Response Time | < 100ms |
| Notification Queuing | < 50ms |
| Email Delivery (total) | 2-10 seconds |
| Push Delivery (total) | 1-5 seconds |
| Queue Throughput | 1000+ msgs/min |
| DB Query Time | < 10ms |
| Cache Hit Rate | > 80% |

---

## 🎉 Success Checklist

- ✅ All services show "healthy" in `docker-compose ps`
- ✅ Can register and login users
- ✅ Can create templates
- ✅ Can send email notifications
- ✅ Can send push notifications (with FCM token)
- ✅ FCM token registration works
- ✅ Notification status updates (queued → sent)
- ✅ Bulk notifications work
- ✅ Idempotency works (same request_id returns cached result)
- ✅ Error handling works (graceful failures)
- ✅ Preferences are respected
- ✅ RabbitMQ queues are processing
- ✅ Logs are showing successful sends

---

## 🚀 Quick Test Script

Want to test everything at once? Here's a script:

```bash
#!/bin/bash
set -e

echo "🚀 Starting Notification System Test Suite"

# 1. Register user
echo "1️⃣ Registering user..."
USER_RESPONSE=$(curl -s -X POST http://localhost:8001/users/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test User",
    "email": "quicktest@example.com",
    "password": "test123",
    "preferences": {"email": true, "push": true}
  }')

USER_ID=$(echo $USER_RESPONSE | jq -r '.data.id')
echo "✅ User created: $USER_ID"

# 2. Login
echo "2️⃣ Logging in..."
TOKEN=$(curl -s -X POST http://localhost:8001/users/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=quicktest@example.com&password=test123" | jq -r '.access_token')
echo "✅ Token received"

# 3. Register FCM token
echo "3️⃣ Registering FCM token..."
curl -s -X POST http://localhost:8001/users/me/fcm-token \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"fcm_token": "test_device_token_xyz"}' > /dev/null
echo "✅ FCM token registered"

# 4. Send email notification
echo "4️⃣ Sending email notification..."
EMAIL_NOTIF=$(curl -s -X POST http://localhost:8000/notifications/send \
  -H "Content-Type: application/json" \
  -d "{
    \"notification_type\": \"email\",
    \"user_id\": \"$USER_ID\",
    \"template_code\": \"welcome_email\",
    \"variables\": {
      \"name\": \"Test User\",
      \"email\": \"quicktest@example.com\",
      \"link\": \"https://example.com\"
    }
  }")

EMAIL_ID=$(echo $EMAIL_NOTIF | jq -r '.data.id')
echo "✅ Email notification queued: $EMAIL_ID"

# 5. Send push notification
echo "5️⃣ Sending push notification..."
PUSH_NOTIF=$(curl -s -X POST http://localhost:8000/notifications/send \
  -H "Content-Type: application/json" \
  -d "{
    \"notification_type\": \"push\",
    \"user_id\": \"$USER_ID\",
    \"template_code\": \"order_shipped\",
    \"variables\": {
      \"order_id\": \"TEST-123\",
      \"tracking_url\": \"https://track.example.com/123\"
    }
  }")

PUSH_ID=$(echo $PUSH_NOTIF | jq -r '.data.id')
echo "✅ Push notification queued: $PUSH_ID"

# 6. Check notification status
echo "6️⃣ Waiting 5 seconds for processing..."
sleep 5

echo "📧 Email notification status:"
curl -s "http://localhost:8000/notifications/$EMAIL_ID" | jq '.data.status'

echo "📱 Push notification status:"
curl -s "http://localhost:8000/notifications/$PUSH_ID" | jq '.data.status'

echo ""
echo "🎉 Test suite completed!"
echo "Check logs with: docker-compose logs -f"
```

Save this as `quick_test.sh`, make it executable (`chmod +x quick_test.sh`), and run it!

---

## 📚 Additional Resources

- **FCM Setup:** See `FCM_SETUP.md` for Firebase configuration
- **SMTP Setup:** Check email-service/.env.example for SMTP providers
- **Architecture:** Read `ARCHITECTURE.txt` for system design
- **Contributing:** See `CONTRIBUTING.md` for development guidelines

---

## 💬 Need Help?

If you're stuck, here's what to check:

1. ✅ Are all services healthy? (`docker-compose ps`)
2. ✅ Are there errors in logs? (`docker-compose logs`)
3. ✅ Is RabbitMQ running? (http://localhost:15672)
4. ✅ Do you have templates created?
5. ✅ Did you register FCM token for push notifications?
6. ✅ Are notification preferences enabled for the user?

Still stuck? Check the logs with correlation IDs to trace requests through the system!

---

**Happy Testing! 🚀**

Made with ❤️ by the NotifyHub Team
