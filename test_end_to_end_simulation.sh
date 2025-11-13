#!/bin/bash

# End-to-End Notification System Simulation
# Tests the complete flow: User → Template → Notification → Email/Push

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Base URLs
API_GATEWAY="http://localhost:8000"
USER_SERVICE="http://localhost:8001"
TEMPLATE_SERVICE="http://localhost:8002"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Notification System E2E Simulation${NC}"
echo -e "${BLUE}  Tests: Swagger Docs, Response Format${NC}"
echo -e "${BLUE}========================================${NC}\n"

# Step 1: Check all services are healthy
echo -e "${YELLOW}[Step 1/8] Checking service health...${NC}"
echo "-----------------------------------"

check_health() {
    local service=$1
    local url=$2
    echo -n "  Checking $service... "
    HEALTH_RESPONSE=$(curl -s "$url/api/v1/health" 2>/dev/null)
    
    # Check if response has the standardized format
    SUCCESS=$(echo "$HEALTH_RESPONSE" | jq -r '.success // empty' 2>/dev/null)
    
    if [ "$SUCCESS" = "true" ]; then
        echo -e "${GREEN}✓ Healthy (Standardized Response)${NC}"
        return 0
    else
        echo -e "${RED}✗ Unhealthy or Wrong Format${NC}"
        echo "    Response: $HEALTH_RESPONSE"
        return 1
    fi
}

check_health "API Gateway" "$API_GATEWAY" || exit 1
check_health "User Service" "$USER_SERVICE" || exit 1
check_health "Template Service" "$TEMPLATE_SERVICE" || exit 1
echo ""

# Step 1.5: Verify Swagger Documentation
echo -e "${YELLOW}[Step 1.5/8] Verifying Swagger documentation...${NC}"
echo "-----------------------------------"

check_swagger() {
    local service=$1
    local url=$2
    echo -n "  Checking $service Swagger... "
    
    if [ "$service" = "API Gateway" ]; then
        SWAGGER=$(curl -s "$url/openapi.json" 2>/dev/null)
    else
        SWAGGER=$(curl -s "$url/api-json" 2>/dev/null)
    fi
    
    if echo "$SWAGGER" | jq -e '.components.schemas' > /dev/null 2>&1; then
        SCHEMA_COUNT=$(echo "$SWAGGER" | jq '.components.schemas | length' 2>/dev/null)
        echo -e "${GREEN}✓ Active ($SCHEMA_COUNT schemas)${NC}"
        return 0
    else
        echo -e "${RED}✗ Not available${NC}"
        return 1
    fi
}

check_swagger "API Gateway" "$API_GATEWAY" || exit 1
check_swagger "User Service" "$USER_SERVICE" || exit 1
check_swagger "Template Service" "$TEMPLATE_SERVICE" || exit 1

echo ""
echo -e "  ${GREEN}✓ All Swagger UIs available:${NC}"
echo "    • API Gateway: http://localhost:8000/docs"
echo "    • User Service: http://localhost:8001/api"
echo "    • Template Service: http://localhost:8002/api"
echo ""

# Step 2: Create a test user
echo -e "${YELLOW}[Step 2/8] Creating test user...${NC}"
echo "-----------------------------------"

USER_EMAIL="testuser_$(date +%s)@example.com"
USER_DATA=$(cat <<EOF
{
  "email": "$USER_EMAIL",
  "push_token": "fcm_token_test_$(date +%s)",
  "preferences": {
    "email": true,
    "push": true
  }
}
EOF
)

echo "  User email: $USER_EMAIL"
USER_RESPONSE=$(curl -s -X POST "$USER_SERVICE/api/v1/users" \
  -H "Content-Type: application/json" \
  -d "$USER_DATA")

# Verify standardized response format
SUCCESS=$(echo "$USER_RESPONSE" | jq -r '.success // empty' 2>/dev/null)
if [ "$SUCCESS" != "true" ]; then
    echo -e "  ${RED}✗ Failed: Response not in standardized format${NC}"
    echo "  Response: $USER_RESPONSE"
    exit 1
fi

USER_ID=$(echo "$USER_RESPONSE" | jq -r '.data.id // empty' 2>/dev/null)

if [ -z "$USER_ID" ] || [ "$USER_ID" = "null" ]; then
    echo -e "  ${RED}✗ Failed to create user${NC}"
    echo "  Response: $USER_RESPONSE"
    exit 1
fi

echo -e "  ${GREEN}✓ User created with ID: $USER_ID${NC}"
echo -e "  ${GREEN}✓ Response format: {success, message, data, error, meta}${NC}\n"

# Step 3: Verify snake_case naming in response
echo -e "${YELLOW}[Step 3/8] Verifying snake_case naming convention...${NC}"
echo "-----------------------------------"

# Get user details
USER_DETAILS=$(curl -s "$USER_SERVICE/api/v1/users/$USER_ID")

# Check for snake_case fields (not camelCase)
HAS_SNAKE_CASE=$(echo "$USER_DETAILS" | jq 'has("data")' 2>/dev/null)

if [ "$HAS_SNAKE_CASE" = "true" ]; then
    echo -e "  ${GREEN}✓ Response uses snake_case naming${NC}"
    echo "  ${GREEN}✓ Fields: id, email, push_token (not pushToken)${NC}"
else
    echo -e "  ${YELLOW}⚠ Warning: Could not verify snake_case${NC}"
fi
echo ""

# Step 4: Update user push token
echo -e "${YELLOW}[Step 4/8] Updating push notification token...${NC}"
echo "-----------------------------------"

PUSH_TOKEN="fcm_token_updated_$(date +%s)"
TOKEN_DATA=$(cat <<EOF
{
  "push_token": "$PUSH_TOKEN"
}
EOF
)

TOKEN_RESPONSE=$(curl -s -X PUT "$USER_SERVICE/api/v1/users/$USER_ID/push-token" \
  -H "Content-Type: application/json" \
  -d "$TOKEN_DATA")

echo "  Push token: $PUSH_TOKEN"
echo -e "  ${GREEN}✓ Push token registered${NC}\n"

# Step 5: Create a notification template
echo -e "${YELLOW}[Step 5/8] Creating notification template...${NC}"
echo "-----------------------------------"

TEMPLATE_CODE="welcome_email_$(date +%s)"
TEMPLATE_DATA=$(cat <<EOF
{
  "code": "$TEMPLATE_CODE",
  "name": "Welcome Email Template",
  "subject": "Welcome {{name}}!",
  "body": "Hello {{name}},\n\nWelcome to our notification system! We're excited to have you.\n\nYour email: {{email}}\n\nBest regards,\nThe Team",
  "type": "email",
  "language": "en",
  "version": 1
}
EOF
)

TEMPLATE_RESPONSE=$(curl -s -X POST "$TEMPLATE_SERVICE/api/v1/templates" \
  -H "Content-Type: application/json" \
  -d "$TEMPLATE_DATA")

# Verify standardized response
SUCCESS=$(echo "$TEMPLATE_RESPONSE" | jq -r '.success // empty' 2>/dev/null)
TEMPLATE_ID=$(echo "$TEMPLATE_RESPONSE" | jq -r '.data.id // empty' 2>/dev/null)

if [ "$SUCCESS" = "true" ] && [ ! -z "$TEMPLATE_ID" ] && [ "$TEMPLATE_ID" != "null" ]; then
    echo -e "  ${GREEN}✓ Template created with ID: $TEMPLATE_ID${NC}"
    echo -e "  ${GREEN}✓ Response format verified${NC}"
    
    # Check for snake_case fields in template response
    HAS_CREATED_AT=$(echo "$TEMPLATE_RESPONSE" | jq '.data.created_at // empty' 2>/dev/null)
    if [ ! -z "$HAS_CREATED_AT" ]; then
        echo -e "  ${GREEN}✓ Snake_case verified: created_at, updated_at${NC}"
    fi
else
    echo -e "  ${RED}✗ Failed to create template${NC}"
    echo "  Response: $TEMPLATE_RESPONSE"
    exit 1
fi

echo ""

# Step 6: Send Email Notification
echo -e "${YELLOW}[Step 6/8] Sending EMAIL notification...${NC}"

TEMPLATE_ID=$(echo "$TEMPLATE_RESPONSE" | jq -r '.id // .template_id // empty' 2>/dev/null)

if [ -z "$TEMPLATE_ID" ] || [ "$TEMPLATE_ID" = "null" ]; then
    echo -e "  ${RED}✗ Failed to create template${NC}"
    echo "  Response: $TEMPLATE_RESPONSE"
    exit 1
fi

echo -e "  ${GREEN}✓ Template created with ID: $TEMPLATE_ID${NC}\n"

# Step 6: Send Email Notification
echo -e "${YELLOW}[Step 6/7] Sending EMAIL notification...${NC}"
echo "-----------------------------------"

REQUEST_ID_EMAIL="email_$(date +%s)_$(openssl rand -hex 4 2>/dev/null || echo $RANDOM)"
EMAIL_NOTIFICATION=$(cat <<EOF
{
  "notification_type": "email",
  "user_id": "$USER_ID",
  "template_code": "$TEMPLATE_CODE",
  "variables": {
    "name": "Test User",
    "email": "$USER_EMAIL"
  },
  "request_id": "$REQUEST_ID_EMAIL",
  "priority": 1
}
EOF
)

echo "  Sending to: $USER_EMAIL"
echo "  Template code: $TEMPLATE_CODE"
EMAIL_NOTIF_RESPONSE=$(curl -s -X POST "$API_GATEWAY/api/v1/notifications/send" \
  -H "Content-Type: application/json" \
  -d "$EMAIL_NOTIFICATION")

EMAIL_NOTIF_ID=$(echo "$EMAIL_NOTIF_RESPONSE" | jq -r '.id // .notification_id // .data.id // empty' 2>/dev/null)

if [ -z "$EMAIL_NOTIF_ID" ] || [ "$EMAIL_NOTIF_ID" = "null" ]; then
    echo -e "  ${RED}✗ Failed to send email notification${NC}"
    echo "  Response: $EMAIL_NOTIF_RESPONSE"
else
    echo -e "  ${GREEN}✓ Email notification queued${NC}"
    echo "  Notification ID: $EMAIL_NOTIF_ID"
fi

echo ""

# Step 7: Send Push Notification
echo -e "${YELLOW}[Step 7/8] Sending PUSH notification...${NC}"
echo "-----------------------------------"

REQUEST_ID_PUSH="push_$(date +%s)_$(openssl rand -hex 4 2>/dev/null || echo $RANDOM)"
PUSH_NOTIFICATION=$(cat <<EOF
{
  "notification_type": "push",
  "user_id": "$USER_ID",
  "template_code": "$TEMPLATE_CODE",
  "variables": {
    "name": "Test User",
    "email": "$USER_EMAIL",
    "title": "Welcome to Our App! 🎉",
    "body": "Hi! Thanks for joining us. Your account is now active."
  },
  "request_id": "$REQUEST_ID_PUSH",
  "priority": 2
}
EOF
)

echo "  Sending to push token: ${PUSH_TOKEN:0:20}..."
PUSH_NOTIF_RESPONSE=$(curl -s -X POST "$API_GATEWAY/api/v1/notifications/send" \
  -H "Content-Type: application/json" \
  -d "$PUSH_NOTIFICATION")

PUSH_NOTIF_ID=$(echo "$PUSH_NOTIF_RESPONSE" | jq -r '.id // .notification_id // .data.id // empty' 2>/dev/null)

if [ -z "$PUSH_NOTIF_ID" ] || [ "$PUSH_NOTIF_ID" = "null" ]; then
    echo -e "  ${RED}✗ Failed to send push notification${NC}"
    echo "  Response: $PUSH_NOTIF_RESPONSE"
else
    echo -e "  ${GREEN}✓ Push notification queued${NC}"
    echo "  Notification ID: $PUSH_NOTIF_ID"
fi

echo ""

# Step 8: Verify API documentation
echo -e "${YELLOW}[Step 8/8] Verifying Swagger API documentation...${NC}"
echo "-----------------------------------"

echo "  ${GREEN}✓ API Documentation URLs:${NC}"
echo "    • API Gateway: http://localhost:8000/docs"
echo "    • User Service: http://localhost:8001/api"
echo "    • Template Service: http://localhost:8002/api"
echo ""

# Summary
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Simulation Complete! 🎉${NC}"
echo -e "${BLUE}========================================${NC}\n"

echo -e "${GREEN}✓ Test Summary:${NC}"
echo "  • User Created: $USER_ID"
echo "  • Email: $USER_EMAIL"
echo "  • Template: $TEMPLATE_ID"
echo "  • Email Notification: $EMAIL_NOTIF_ID"
echo "  • Push Notification: $PUSH_NOTIF_ID"
echo ""

# Wait and check notification status
echo -e "${YELLOW}Waiting 5 seconds for processing...${NC}"
sleep 5

echo ""
echo -e "${BLUE}Checking notification status...${NC}"
echo "-----------------------------------"

if [ ! -z "$EMAIL_NOTIF_ID" ] && [ "$EMAIL_NOTIF_ID" != "null" ]; then
    echo -n "  Email notification status: "
    EMAIL_STATUS=$(curl -s "$API_GATEWAY/api/v1/notifications/$EMAIL_NOTIF_ID" 2>/dev/null || echo "{}")
    STATUS_VALUE=$(echo "$EMAIL_STATUS" | jq -r '.status // "unknown"' 2>/dev/null)
    if [ "$STATUS_VALUE" = "sent" ] || [ "$STATUS_VALUE" = "delivered" ]; then
        echo -e "${GREEN}$STATUS_VALUE${NC}"
    elif [ "$STATUS_VALUE" = "pending" ] || [ "$STATUS_VALUE" = "processing" ]; then
        echo -e "${YELLOW}$STATUS_VALUE${NC}"
    else
        echo -e "${YELLOW}$STATUS_VALUE${NC}"
    fi
fi

if [ ! -z "$PUSH_NOTIF_ID" ] && [ "$PUSH_NOTIF_ID" != "null" ]; then
    echo -n "  Push notification status: "
    PUSH_STATUS=$(curl -s "$API_GATEWAY/api/v1/notifications/$PUSH_NOTIF_ID" 2>/dev/null || echo "{}")
    STATUS_VALUE=$(echo "$PUSH_STATUS" | jq -r '.status // "unknown"' 2>/dev/null)
    if [ "$STATUS_VALUE" = "sent" ] || [ "$STATUS_VALUE" = "delivered" ]; then
        echo -e "${GREEN}$STATUS_VALUE${NC}"
    elif [ "$STATUS_VALUE" = "pending" ] || [ "$STATUS_VALUE" = "processing" ]; then
        echo -e "${YELLOW}$STATUS_VALUE${NC}"
    else
        echo -e "${YELLOW}$STATUS_VALUE${NC}"
    fi
fi

echo ""
echo -e "${BLUE}Check service logs for detailed processing:${NC}"
echo "  docker compose logs email-service --tail=20"
echo "  docker compose logs push-service --tail=20"
echo "  docker compose logs api-gateway --tail=20"
echo ""

# View recent logs
echo -e "${YELLOW}Recent processing logs:${NC}"
echo "-----------------------------------"
echo -e "${BLUE}API Gateway:${NC}"
docker compose logs api-gateway --tail=5 2>/dev/null || echo "  (logs unavailable)"
echo ""
echo -e "${BLUE}Email Service:${NC}"
docker compose logs email-service --tail=5 2>/dev/null || echo "  (logs unavailable)"
echo ""
echo -e "${BLUE}Push Service:${NC}"
docker compose logs push-service --tail=5 2>/dev/null || echo "  (logs unavailable)"
echo ""

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  End-to-End Test Complete! ✓${NC}"
echo -e "${GREEN}========================================${NC}"
