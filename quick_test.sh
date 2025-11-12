#!/bin/bash
set -e

echo "🚀 Starting Notification System Test Suite"
echo "==========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Generate unique identifiers to avoid conflicts
TIMESTAMP=$(date +%s)
RANDOM_EMAIL="quicktest${TIMESTAMP}@example.com"
REQUEST_ID_PREFIX="quicktest-${TIMESTAMP}"

# 1. Register user
echo -e "${BLUE}1️⃣ Registering user...${NC}"
USER_RESPONSE=$(curl -s -X POST http://localhost:8001/users/register \
  -H "Content-Type: application/json" \
  -d "{
    \"name\": \"Test User\",
    \"email\": \"$RANDOM_EMAIL\",
    \"password\": \"test123\",
    \"preferences\": {\"email\": true, \"push\": true}
  }")

USER_ID=$(echo $USER_RESPONSE | jq -r '.data.id')
if [ "$USER_ID" != "null" ] && [ -n "$USER_ID" ]; then
    echo -e "${GREEN}✅ User created: $USER_ID${NC}"
else
    echo -e "${RED}❌ Failed to create user${NC}"
    echo $USER_RESPONSE | jq .
    exit 1
fi

# 2. Login
echo -e "${BLUE}2️⃣ Logging in...${NC}"
TOKEN=$(curl -s -X POST http://localhost:8001/users/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=$RANDOM_EMAIL&password=test123" | jq -r '.access_token')

if [ "$TOKEN" != "null" ] && [ -n "$TOKEN" ]; then
    echo -e "${GREEN}✅ Token received${NC}"
else
    echo -e "${RED}❌ Failed to login${NC}"
    exit 1
fi

# 3. Register FCM token
echo -e "${BLUE}3️⃣ Registering FCM token...${NC}"
FCM_RESPONSE=$(curl -s -X POST http://localhost:8001/users/me/fcm-token \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"fcm_token": "test_device_token_xyz"}')

FCM_TOKEN=$(echo $FCM_RESPONSE | jq -r '.data.push_token')
if [ "$FCM_TOKEN" != "null" ] && [ -n "$FCM_TOKEN" ]; then
    echo -e "${GREEN}✅ FCM token registered${NC}"
else
    echo -e "${RED}❌ Failed to register FCM token${NC}"
    echo $FCM_RESPONSE | jq .
    exit 1
fi

# 4. Create email template (if not exists)
echo -e "${BLUE}4️⃣ Checking/creating email template...${NC}"
TEMPLATE_CHECK=$(curl -s "http://localhost:8002/templates/name/welcome_email?language=en")
if echo $TEMPLATE_CHECK | jq -e '.success == true' > /dev/null; then
    echo -e "${YELLOW}⚠️  Template already exists, skipping creation${NC}"
else
    curl -s -X POST http://localhost:8002/templates/ \
      -H "Content-Type: application/json" \
      -d '{
        "name": "welcome_email",
        "channel": "email",
        "language": "en",
        "subject": "Welcome {{name}}!",
        "body": "<html><body><h1>Hello {{name}}</h1><p>Email: {{email}}</p><p><a href=\"{{link}}\">Click here</a></p></body></html>",
        "variables": ["name", "email", "link"]
      }' > /dev/null
    echo -e "${GREEN}✅ Email template created${NC}"
fi

# 5. Create push template (if not exists)
echo -e "${BLUE}5️⃣ Checking/creating push template...${NC}"
PUSH_TEMPLATE_CHECK=$(curl -s "http://localhost:8002/templates/name/order_shipped?language=en")
if echo $PUSH_TEMPLATE_CHECK | jq -e '.success == true' > /dev/null; then
    echo -e "${YELLOW}⚠️  Template already exists, skipping creation${NC}"
else
    curl -s -X POST http://localhost:8002/templates/ \
      -H "Content-Type: application/json" \
      -d '{
        "name": "order_shipped",
        "channel": "push",
        "language": "en",
        "subject": "Order #{{order_id}} Shipped!",
        "body": "Your order has been shipped! Track: {{tracking_url}}",
        "variables": ["order_id", "tracking_url"]
      }' > /dev/null
    echo -e "${GREEN}✅ Push template created${NC}"
fi

# 6. Send email notification
echo -e "${BLUE}6️⃣ Sending email notification...${NC}"
EMAIL_NOTIF=$(curl -s -X POST http://localhost:8000/notifications/send \
  -H "Content-Type: application/json" \
  -H "X-Correlation-ID: quicktest-email" \
  -d "{
    \"notification_type\": \"email\",
    \"user_id\": \"$USER_ID\",
    \"template_code\": \"welcome_email\",
    \"variables\": {
      \"name\": \"Test User\",
      \"email\": \"quicktest@example.com\",
      \"link\": \"https://example.com\"
    },
    \"request_id\": \"${REQUEST_ID_PREFIX}-email\"
  }")

EMAIL_ID=$(echo $EMAIL_NOTIF | jq -r '.data.id')
if [ "$EMAIL_ID" != "null" ] && [ -n "$EMAIL_ID" ]; then
    echo -e "${GREEN}✅ Email notification queued (ID: $EMAIL_ID)${NC}"
else
    echo -e "${RED}❌ Failed to queue email notification${NC}"
    echo $EMAIL_NOTIF | jq .
    exit 1
fi

# 7. Send push notification
echo -e "${BLUE}7️⃣ Sending push notification...${NC}"
PUSH_NOTIF=$(curl -s -X POST http://localhost:8000/notifications/send \
  -H "Content-Type: application/json" \
  -H "X-Correlation-ID: quicktest-push" \
  -d "{
    \"notification_type\": \"push\",
    \"user_id\": \"$USER_ID\",
    \"template_code\": \"order_shipped\",
    \"variables\": {
      \"order_id\": \"TEST-123\",
      \"tracking_url\": \"https://track.example.com/123\"
    },
    \"request_id\": \"${REQUEST_ID_PREFIX}-push\"
  }")

PUSH_ID=$(echo $PUSH_NOTIF | jq -r '.data.id')
if [ "$PUSH_ID" != "null" ] && [ -n "$PUSH_ID" ]; then
    echo -e "${GREEN}✅ Push notification queued (ID: $PUSH_ID)${NC}"
else
    echo -e "${RED}❌ Failed to queue push notification${NC}"
    echo $PUSH_NOTIF | jq .
    exit 1
fi

# 8. Test idempotency
echo -e "${BLUE}8️⃣ Testing idempotency...${NC}"
IDEMPOTENT_1=$(curl -s -X POST http://localhost:8000/notifications/send \
  -H "Content-Type: application/json" \
  -d "{
    \"notification_type\": \"email\",
    \"user_id\": \"$USER_ID\",
    \"template_code\": \"welcome_email\",
    \"variables\": {
      \"name\": \"Test\",
      \"email\": \"test@example.com\",
      \"link\": \"https://example.com\"
    },
    \"request_id\": \"${REQUEST_ID_PREFIX}-idempotent\"
  }" | jq -r '.data.id')

IDEMPOTENT_2=$(curl -s -X POST http://localhost:8000/notifications/send \
  -H "Content-Type: application/json" \
  -d "{
    \"notification_type\": \"email\",
    \"user_id\": \"$USER_ID\",
    \"template_code\": \"welcome_email\",
    \"variables\": {
      \"name\": \"Test\",
      \"email\": \"test@example.com\",
      \"link\": \"https://example.com\"
    },
    \"request_id\": \"${REQUEST_ID_PREFIX}-idempotent\"
  }" | jq -r '.data.id')

if [ "$IDEMPOTENT_1" == "$IDEMPOTENT_2" ]; then
    echo -e "${GREEN}✅ Idempotency works (both returned ID: $IDEMPOTENT_1)${NC}"
else
    echo -e "${RED}❌ Idempotency failed (ID1: $IDEMPOTENT_1, ID2: $IDEMPOTENT_2)${NC}"
fi

# 9. Check notification status
echo ""
echo -e "${BLUE}9️⃣ Waiting 5 seconds for processing...${NC}"
sleep 5

echo ""
echo "📊 Checking notification statuses..."
echo "─────────────────────────────────────"

EMAIL_STATUS=$(curl -s "http://localhost:8000/notifications/$EMAIL_ID" | jq -r '.data.status')
echo -e "📧 Email notification: ${GREEN}$EMAIL_STATUS${NC}"

PUSH_STATUS=$(curl -s "http://localhost:8000/notifications/$PUSH_ID" | jq -r '.data.status')
echo -e "📱 Push notification:  ${GREEN}$PUSH_STATUS${NC}"

# 10. Test preferences
echo ""
echo -e "${BLUE}🔟 Testing notification preferences...${NC}"
PREFS=$(curl -s "http://localhost:8001/users/$USER_ID/preferences" | jq -r '.data | length')
echo -e "${GREEN}✅ User has $PREFS notification preferences${NC}"

# 11. Health checks
echo ""
echo -e "${BLUE}1️⃣1️⃣ Running health checks...${NC}"
API_HEALTH=$(curl -s http://localhost:8000/health | jq -r '.success')
USER_HEALTH=$(curl -s http://localhost:8001/health | jq -r '.success')
TEMPLATE_HEALTH=$(curl -s http://localhost:8002/health | jq -r '.success')

echo -e "API Gateway:      $([ "$API_HEALTH" == "true" ] && echo -e "${GREEN}✅ Healthy${NC}" || echo -e "${RED}❌ Unhealthy${NC}")"
echo -e "User Service:     $([ "$USER_HEALTH" == "true" ] && echo -e "${GREEN}✅ Healthy${NC}" || echo -e "${RED}❌ Unhealthy${NC}")"
echo -e "Template Service: $([ "$TEMPLATE_HEALTH" == "true" ] && echo -e "${GREEN}✅ Healthy${NC}" || echo -e "${RED}❌ Unhealthy${NC}")"

# Summary
echo ""
echo "==========================================="
echo -e "${GREEN}🎉 Test Suite Completed Successfully!${NC}"
echo "==========================================="
echo ""
echo "📝 Summary:"
echo "  • User ID: $USER_ID"
echo "  • Email Notification ID: $EMAIL_ID (Status: $EMAIL_STATUS)"
echo "  • Push Notification ID: $PUSH_ID (Status: $PUSH_STATUS)"
echo ""
echo "💡 Next steps:"
echo "  • Check logs: docker-compose logs -f"
echo "  • View queues: http://localhost:15672 (admin/admin)"
echo "  • Monitor notifications: curl http://localhost:8000/notifications/user/$USER_ID | jq ."
echo ""
echo "📚 Full guide: See API_TESTING.md"
echo ""
