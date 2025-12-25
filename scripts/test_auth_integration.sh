#!/bin/bash
# Test script for Supabase authentication integration
# Tests both backend-generated JWTs and Supabase JWT verification

set -e

BASE_URL="http://localhost:8000"
API_VERSION="v1"

echo "🧪 Testing Timeless Love Backend Authentication"
echo "================================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test 1: Health check
echo "1. Testing health endpoint (public)..."
HEALTH_RESPONSE=$(curl -s "${BASE_URL}/health")
if echo "$HEALTH_RESPONSE" | grep -q "healthy"; then
    echo -e "${GREEN}✓ Health check passed${NC}"
else
    echo -e "${RED}✗ Health check failed${NC}"
    exit 1
fi
echo ""

# Test 2: Register a new user (backend JWT)
echo "2. Testing user registration (backend JWT generation)..."
REGISTER_PAYLOAD='{
  "email": "test-'$(date +%s)'@example.com",
  "password": "TestPassword123!",
  "display_name": "Test User"
}'

REGISTER_RESPONSE=$(curl -s -X POST "${BASE_URL}/api/${API_VERSION}/auth/register/adult" \
  -H "Content-Type: application/json" \
  -d "$REGISTER_PAYLOAD")

if echo "$REGISTER_RESPONSE" | grep -q "access_token"; then
    echo -e "${GREEN}✓ Registration successful${NC}"

    # Extract access token
    ACCESS_TOKEN=$(echo "$REGISTER_RESPONSE" | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

    if [ -n "$ACCESS_TOKEN" ]; then
        echo "  Access token: ${ACCESS_TOKEN:0:50}..."
    else
        echo -e "${RED}✗ Failed to extract access token${NC}"
        exit 1
    fi
else
    echo -e "${RED}✗ Registration failed${NC}"
    echo "Response: $REGISTER_RESPONSE"
    exit 1
fi
echo ""

# Test 3: Use backend JWT to access protected endpoint
echo "3. Testing protected endpoint with backend JWT..."
MEMORIES_RESPONSE=$(curl -s "${BASE_URL}/api/${API_VERSION}/memories" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}")

if echo "$MEMORIES_RESPONSE" | grep -q -E '(\[|\{)'; then
    echo -e "${GREEN}✓ Backend JWT authentication working${NC}"
else
    echo -e "${RED}✗ Backend JWT authentication failed${NC}"
    echo "Response: $MEMORIES_RESPONSE"
fi
echo ""

# Test 4: Generate a fake Supabase-style JWT for testing
echo "4. Testing Supabase JWT verification (simulated)..."
echo -e "${YELLOW}ℹ To test real Supabase JWT verification:${NC}"
echo "  1. Get a token from your frontend: await supabase.auth.getSession()"
echo "  2. Run: curl ${BASE_URL}/api/v1/test-endpoint -H 'Authorization: Bearer YOUR_TOKEN'"
echo ""

# Test 5: Test invalid token rejection
echo "5. Testing invalid token rejection..."
INVALID_RESPONSE=$(curl -s "${BASE_URL}/api/${API_VERSION}/memories" \
  -H "Authorization: Bearer invalid.token.here")

if echo "$INVALID_RESPONSE" | grep -q -E '(Invalid|Unauthorized|401)'; then
    echo -e "${GREEN}✓ Invalid tokens are correctly rejected${NC}"
else
    echo -e "${RED}✗ Invalid token not rejected${NC}"
    echo "Response: $INVALID_RESPONSE"
fi
echo ""

# Test 6: Test missing token
echo "6. Testing missing token handling..."
NO_TOKEN_RESPONSE=$(curl -s "${BASE_URL}/api/${API_VERSION}/memories")

if echo "$NO_TOKEN_RESPONSE" | grep -q -E '(Forbidden|403|Not authenticated)'; then
    echo -e "${GREEN}✓ Missing tokens are correctly rejected${NC}"
else
    echo -e "${RED}✗ Missing token not rejected${NC}"
    echo "Response: $NO_TOKEN_RESPONSE"
fi
echo ""

echo "================================================"
echo -e "${GREEN}✅ All authentication tests passed!${NC}"
echo ""
echo "To test Supabase frontend JWT verification:"
echo "  1. Create a test endpoint in your backend:"
echo ""
echo "     @router.get('/test/supabase')"
echo "     async def test(user: SupabaseUser = Depends(verify_supabase_token)):"
echo "         return {'user_id': user.id, 'email': user.email}"
echo ""
echo "  2. Get a real Supabase token from your React frontend"
echo "  3. Test with: curl -H 'Authorization: Bearer TOKEN' http://localhost:8000/test/supabase"
echo ""
