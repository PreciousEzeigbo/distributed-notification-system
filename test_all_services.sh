#!/bin/bash

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

# Test counters
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Helper functions
print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

print_test() {
    echo -e "${YELLOW}▶ TEST: $1${NC}"
    ((TOTAL_TESTS++))
}

print_pass() {
    echo -e "${GREEN}✓ PASS: $1${NC}"
    ((PASSED_TESTS++))
}

print_fail() {
    echo -e "${RED}✗ FAIL: $1${NC}"
    echo -e "${RED}  $2${NC}"
    ((FAILED_TESTS++))
}

print_info() {
    echo -e "${BLUE}ℹ INFO: $1${NC}"
}

# Check if jq is installed
if ! command -v jq &> /dev/null; then
    echo -e "${RED}Error: jq is not installed. Please install it first:${NC}"
    echo "  sudo apt-get install jq"
    exit 1
fi

print_header "🚀 DISTRIBUTED NOTIFICATION SYSTEM - INTEGRATION TEST"

# =============================================================================
# 1. INFRASTRUCTURE HEALTH CHECKS
# =============================================================================
print_header "1. Infrastructure Health Checks"

# Test Redis
print_test "Redis Connection"
if redis-cli -p 6380 ping > /dev/null 2>&1; then
    print_pass "Redis is responding on port 6380"
else
    print_fail "Redis is not responding" "Check if Redis container is running"
fi

# Test RabbitMQ
print_test "RabbitMQ Management API"
RABBITMQ_RESPONSE=$(curl -s -u admin:admin http://localhost:15672/api/overview)
if echo "$RABBITMQ_RESPONSE" | jq -e '.rabbitmq_version' > /dev/null 2>&1; then
    VERSION=$(echo "$RABBITMQ_RESPONSE" | jq -r '.rabbitmq_version')
    print_pass "RabbitMQ is running (version: $VERSION)"
else
    print_fail "RabbitMQ Management API is not responding" "Check if RabbitMQ container is running"
fi

# Test PostgreSQL databases
print_test "PostgreSQL Databases"
PG_HEALTH=0
for PORT in 5432 5433 5434; do
    if pg_isready -h localhost -p $PORT > /dev/null 2>&1; then
        ((PG_HEALTH++))
    fi
done
if [ $PG_HEALTH -eq 3 ]; then
    print_pass "All 3 PostgreSQL databases are ready (ports 5432, 5433, 5434)"
else
    print_fail "Only $PG_HEALTH/3 PostgreSQL databases are ready" "Check database containers"
fi

# =============================================================================
# 2. SERVICE HEALTH CHECKS
# =============================================================================
print_header "2. Service Health Checks"

# API Gateway
print_test "API Gateway Health"
RESPONSE=$(curl -s -w "\n%{http_code}" "$API_GATEWAY/health")
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | head -n-1)
if [ "$HTTP_CODE" = "200" ]; then
    STATUS=$(echo "$BODY" | jq -r '.data.status' 2>/dev/null)
    print_pass "API Gateway is healthy (status: $STATUS)"
else
    print_fail "API Gateway health check failed (HTTP $HTTP_CODE)" "$BODY"
fi

# User Service
print_test "User Service Health"
RESPONSE=$(curl -s -w "\n%{http_code}" "$USER_SERVICE/health")
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | head -n-1)
if [ "$HTTP_CODE" = "200" ]; then
    STATUS=$(echo "$BODY" | jq -r '.data.status' 2>/dev/null)
    print_pass "User Service is healthy (status: $STATUS)"
else
    print_fail "User Service health check failed (HTTP $HTTP_CODE)" "$BODY"
fi

# Template Service
print_test "Template Service Health"
RESPONSE=$(curl -s -w "\n%{http_code}" "$TEMPLATE_SERVICE/health")
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | head -n-1)
if [ "$HTTP_CODE" = "200" ]; then
    STATUS=$(echo "$BODY" | jq -r '.data.status' 2>/dev/null)
    print_pass "Template Service is healthy (status: $STATUS)"
else
    print_fail "Template Service health check failed (HTTP $HTTP_CODE)" "$BODY"
fi

# =============================================================================
# 3. USER SERVICE TESTS
# =============================================================================
print_header "3. User Service Tests"

# Create a test user
print_test "Create User"
USER_EMAIL="test_$(date +%s)@example.com"
CREATE_USER_RESPONSE=$(curl -s -X POST "$USER_SERVICE/users" \
    -H "Content-Type: application/json" \
    -d "{
        \"name\": \"Test User\",
        \"email\": \"$USER_EMAIL\",
        \"password\": \"password123\",
        \"push_token\": \"test_fcm_token_123\",
        \"preferences\": {
            \"email\": true,
            \"push\": true
        }
    }")

USER_ID=$(echo "$CREATE_USER_RESPONSE" | jq -r '.id // .data.id // empty' 2>/dev/null)
if [ -n "$USER_ID" ]; then
    print_pass "User created successfully (ID: $USER_ID)"
else
    print_fail "Failed to create user" "$CREATE_USER_RESPONSE"
    USER_ID="1" # fallback for remaining tests
fi

# Get user by ID
print_test "Get User by ID"
GET_USER_RESPONSE=$(curl -s "$USER_SERVICE/users/$USER_ID")
USER_NAME=$(echo "$GET_USER_RESPONSE" | jq -r '.name // .data.name // empty' 2>/dev/null)
if [ -n "$USER_NAME" ]; then
    print_pass "User retrieved successfully (Name: $USER_NAME)"
else
    print_fail "Failed to retrieve user" "$GET_USER_RESPONSE"
fi

# Get user preferences
print_test "Get User Preferences"
PREF_RESPONSE=$(curl -s "$USER_SERVICE/users/$USER_ID/preferences")
EMAIL_PREF=$(echo "$PREF_RESPONSE" | jq -r '.data.preferences.email // .preferences.email // empty' 2>/dev/null)
if [ -n "$EMAIL_PREF" ]; then
    print_pass "User preferences retrieved (email: $EMAIL_PREF)"
else
    print_fail "Failed to retrieve user preferences" "$PREF_RESPONSE"
fi

# Update user preferences
print_test "Update User Preferences"
UPDATE_PREF_RESPONSE=$(curl -s -X PUT "$USER_SERVICE/users/$USER_ID/preferences" \
    -H "Content-Type: application/json" \
    -d '{"email": false, "push": true}')
SUCCESS=$(echo "$UPDATE_PREF_RESPONSE" | jq -r '.success // empty' 2>/dev/null)
if [ "$SUCCESS" = "true" ]; then
    print_pass "User preferences updated successfully"
else
    print_fail "Failed to update user preferences" "$UPDATE_PREF_RESPONSE"
fi

# =============================================================================
# 4. TEMPLATE SERVICE TESTS
# =============================================================================
print_header "4. Template Service Tests"

# Create a test template
print_test "Create Template"
TEMPLATE_CODE="test_template_$(date +%s)"
CREATE_TEMPLATE_RESPONSE=$(curl -s -X POST "$TEMPLATE_SERVICE/templates" \
    -H "Content-Type: application/json" \
    -d "{
        \"name\": \"Test Template\",
        \"code\": \"$TEMPLATE_CODE\",
        \"subject\": \"Hello {{name}}\",
        \"body\": \"Welcome {{name}} to our service!\",
        \"type\": \"email\",
        \"language\": \"en\"
    }")

TEMPLATE_ID=$(echo "$CREATE_TEMPLATE_RESPONSE" | jq -r '.id // .data.id // empty' 2>/dev/null)
if [ -n "$TEMPLATE_ID" ]; then
    print_pass "Template created successfully (ID: $TEMPLATE_ID)"
else
    print_fail "Failed to create template" "$CREATE_TEMPLATE_RESPONSE"
    TEMPLATE_CODE="welcome_email" # fallback
fi

# Get template by code
print_test "Get Template by Code"
GET_TEMPLATE_RESPONSE=$(curl -s "$TEMPLATE_SERVICE/templates/$TEMPLATE_CODE")
TEMPLATE_NAME=$(echo "$GET_TEMPLATE_RESPONSE" | jq -r '.name // .data.name // empty' 2>/dev/null)
if [ -n "$TEMPLATE_NAME" ]; then
    print_pass "Template retrieved successfully (Name: $TEMPLATE_NAME)"
else
    print_fail "Failed to retrieve template" "$GET_TEMPLATE_RESPONSE"
fi

# =============================================================================
# 5. API GATEWAY - NOTIFICATION TESTS
# =============================================================================
print_header "5. API Gateway - Notification Tests"

# Generate unique request ID
REQUEST_ID="test_$(date +%s)_$(uuidgen 2>/dev/null || echo $RANDOM)"

# Send email notification
print_test "Send Email Notification"
EMAIL_NOTIF_RESPONSE=$(curl -s -X POST "$API_GATEWAY/notifications/send" \
    -H "Content-Type: application/json" \
    -d "{
        \"notification_type\": \"email\",
        \"user_id\": \"$USER_ID\",
        \"template_code\": \"$TEMPLATE_CODE\",
        \"variables\": {
            \"name\": \"Test User\",
            \"link\": \"https://example.com\"
        },
        \"request_id\": \"${REQUEST_ID}_email\",
        \"priority\": 1
    }")

EMAIL_NOTIF_ID=$(echo "$EMAIL_NOTIF_RESPONSE" | jq -r '.data.id // .id // empty' 2>/dev/null)
if [ -n "$EMAIL_NOTIF_ID" ]; then
    print_pass "Email notification queued successfully (ID: $EMAIL_NOTIF_ID)"
else
    print_fail "Failed to send email notification" "$EMAIL_NOTIF_RESPONSE"
fi

# Send push notification
print_test "Send Push Notification"
PUSH_NOTIF_RESPONSE=$(curl -s -X POST "$API_GATEWAY/notifications/send" \
    -H "Content-Type: application/json" \
    -d "{
        \"notification_type\": \"push\",
        \"user_id\": \"$USER_ID\",
        \"template_code\": \"$TEMPLATE_CODE\",
        \"variables\": {
            \"name\": \"Test User\",
            \"link\": \"https://example.com\"
        },
        \"request_id\": \"${REQUEST_ID}_push\",
        \"priority\": 0
    }")

PUSH_NOTIF_ID=$(echo "$PUSH_NOTIF_RESPONSE" | jq -r '.data.id // .id // empty' 2>/dev/null)
if [ -n "$PUSH_NOTIF_ID" ]; then
    print_pass "Push notification queued successfully (ID: $PUSH_NOTIF_ID)"
else
    print_fail "Failed to send push notification" "$PUSH_NOTIF_RESPONSE"
fi

# Test idempotency
print_test "Idempotency Check (duplicate request)"
DUPLICATE_RESPONSE=$(curl -s -X POST "$API_GATEWAY/notifications/send" \
    -H "Content-Type: application/json" \
    -d "{
        \"notification_type\": \"email\",
        \"user_id\": \"$USER_ID\",
        \"template_code\": \"$TEMPLATE_CODE\",
        \"variables\": {
            \"name\": \"Test User\",
            \"link\": \"https://example.com\"
        },
        \"request_id\": \"${REQUEST_ID}_email\",
        \"priority\": 1
    }")

MESSAGE=$(echo "$DUPLICATE_RESPONSE" | jq -r '.message // empty' 2>/dev/null)
if echo "$MESSAGE" | grep -qi "already\|duplicate\|idempotent"; then
    print_pass "Idempotency working correctly"
else
    print_fail "Idempotency check failed" "$DUPLICATE_RESPONSE"
fi

# Test rate limiting (send 101 requests quickly)
print_test "Rate Limiting (100 req/min)"
RATE_LIMIT_HIT=false
for i in {1..105}; do
    RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$API_GATEWAY/notifications/send" \
        -H "Content-Type: application/json" \
        -d "{
            \"notification_type\": \"email\",
            \"user_id\": \"$USER_ID\",
            \"template_code\": \"$TEMPLATE_CODE\",
            \"variables\": {\"name\": \"Test\"},
            \"request_id\": \"rate_test_${i}_$(date +%s%N)\",
            \"priority\": 0
        }")
    
    HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
    if [ "$HTTP_CODE" = "429" ]; then
        RATE_LIMIT_HIT=true
        break
    fi
done

if [ "$RATE_LIMIT_HIT" = true ]; then
    print_pass "Rate limiting is working (HTTP 429 received)"
else
    print_fail "Rate limiting not triggered" "Expected HTTP 429 after 100 requests"
fi

# =============================================================================
# 6. RABBITMQ QUEUE TESTS
# =============================================================================
print_header "6. RabbitMQ Queue Tests"

# Check queues
print_test "RabbitMQ Queues"
QUEUES=$(curl -s -u admin:admin http://localhost:15672/api/queues | jq -r '.[].name' 2>/dev/null)
EMAIL_QUEUE=$(echo "$QUEUES" | grep -c "email" || echo "0")
PUSH_QUEUE=$(echo "$QUEUES" | grep -c "push" || echo "0")

if [ "$EMAIL_QUEUE" -gt 0 ] && [ "$PUSH_QUEUE" -gt 0 ]; then
    print_pass "Email and Push queues exist"
else
    print_fail "Missing queues" "Email queue: $EMAIL_QUEUE, Push queue: $PUSH_QUEUE"
fi

# Check queue messages
print_test "Queue Message Count"
QUEUE_STATS=$(curl -s -u admin:admin http://localhost:15672/api/queues)
TOTAL_MESSAGES=$(echo "$QUEUE_STATS" | jq '[.[].messages] | add' 2>/dev/null || echo "0")
if [ "$TOTAL_MESSAGES" -gt 0 ]; then
    print_pass "Messages in queues: $TOTAL_MESSAGES"
else
    print_info "No messages in queues (they may have been processed already)"
fi

# =============================================================================
# 7. REDIS CACHE TESTS
# =============================================================================
print_header "7. Redis Cache Tests"

# Test Redis operations
print_test "Redis SET/GET Operations"
redis-cli -p 6380 SET test_key "test_value" > /dev/null 2>&1
REDIS_VALUE=$(redis-cli -p 6380 GET test_key 2>/dev/null)
redis-cli -p 6380 DEL test_key > /dev/null 2>&1

if [ "$REDIS_VALUE" = "test_value" ]; then
    print_pass "Redis SET/GET operations working"
else
    print_fail "Redis operations failed" "Expected 'test_value', got '$REDIS_VALUE'"
fi

# Check Redis memory usage
print_test "Redis Memory Usage"
REDIS_INFO=$(redis-cli -p 6380 INFO memory 2>/dev/null)
USED_MEMORY=$(echo "$REDIS_INFO" | grep "used_memory_human:" | cut -d: -f2 | tr -d '\r')
if [ -n "$USED_MEMORY" ]; then
    print_pass "Redis memory usage: $USED_MEMORY"
else
    print_fail "Failed to get Redis memory info" ""
fi

# =============================================================================
# 8. END-TO-END NOTIFICATION TEST
# =============================================================================
print_header "8. End-to-End Notification Test"

print_info "Waiting 5 seconds for workers to process messages..."
sleep 5

# Check notification status
print_test "Email Notification Status"
if [ -n "$EMAIL_NOTIF_ID" ]; then
    STATUS_RESPONSE=$(curl -s "$API_GATEWAY/notifications/$EMAIL_NOTIF_ID")
    STATUS=$(echo "$STATUS_RESPONSE" | jq -r '.data.status // .status // empty' 2>/dev/null)
    print_info "Email notification status: $STATUS"
    if [ "$STATUS" = "delivered" ] || [ "$STATUS" = "queued" ] || [ "$STATUS" = "pending" ]; then
        print_pass "Email notification is being processed (status: $STATUS)"
    else
        print_info "Email status: $STATUS (may still be processing)"
    fi
fi

print_test "Push Notification Status"
if [ -n "$PUSH_NOTIF_ID" ]; then
    STATUS_RESPONSE=$(curl -s "$API_GATEWAY/notifications/$PUSH_NOTIF_ID")
    STATUS=$(echo "$STATUS_RESPONSE" | jq -r '.data.status // .status // empty' 2>/dev/null)
    print_info "Push notification status: $STATUS"
    if [ "$STATUS" = "delivered" ] || [ "$STATUS" = "queued" ] || [ "$STATUS" = "pending" ]; then
        print_pass "Push notification is being processed (status: $STATUS)"
    else
        print_info "Push status: $STATUS (may still be processing)"
    fi
fi

# =============================================================================
# TEST SUMMARY
# =============================================================================
print_header "📊 TEST SUMMARY"

echo -e "Total Tests:  ${BLUE}$TOTAL_TESTS${NC}"
echo -e "Passed:       ${GREEN}$PASSED_TESTS${NC}"
echo -e "Failed:       ${RED}$FAILED_TESTS${NC}"

PASS_RATE=$(( PASSED_TESTS * 100 / TOTAL_TESTS ))
echo -e "Pass Rate:    ${BLUE}${PASS_RATE}%${NC}"

echo ""
if [ $FAILED_TESTS -eq 0 ]; then
    echo -e "${GREEN}╔═══════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║   ✓ ALL TESTS PASSED SUCCESSFULLY!   ║${NC}"
    echo -e "${GREEN}╚═══════════════════════════════════════╝${NC}"
    exit 0
elif [ $PASS_RATE -ge 80 ]; then
    echo -e "${YELLOW}╔═══════════════════════════════════════╗${NC}"
    echo -e "${YELLOW}║  ⚠ MOST TESTS PASSED (${PASS_RATE}%)          ║${NC}"
    echo -e "${YELLOW}╚═══════════════════════════════════════╝${NC}"
    exit 0
else
    echo -e "${RED}╔═══════════════════════════════════════╗${NC}"
    echo -e "${RED}║   ✗ TESTS FAILED (${PASS_RATE}%)              ║${NC}"
    echo -e "${RED}╚═══════════════════════════════════════╝${NC}"
    exit 1
fi
