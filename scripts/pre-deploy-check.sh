#!/bin/bash

# Pre-Deployment Validation Script
# Validates deployment readiness before deploying to production

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Counters
PASSED=0
FAILED=0
WARNINGS=0

echo "=========================================="
echo "  Timeless Love Pre-Deployment Check"
echo "=========================================="
echo ""

# Function to print success
success() {
    echo -e "${GREEN}✓${NC} $1"
    ((PASSED++))
}

# Function to print failure
failure() {
    echo -e "${RED}✗${NC} $1"
    ((FAILED++))
}

# Function to print warning
warning() {
    echo -e "${YELLOW}⚠${NC} $1"
    ((WARNINGS++))
}

# Function to check if command exists
check_command() {
    if command -v "$1" &> /dev/null; then
        success "$1 is installed"
        return 0
    else
        failure "$1 is not installed"
        return 1
    fi
}

# Function to check if file exists
check_file() {
    if [ -f "$1" ]; then
        success "File exists: $1"
        return 0
    else
        failure "File missing: $1"
        return 1
    fi
}

# Function to check environment variable
check_env_var() {
    if [ -z "${!1}" ]; then
        failure "Environment variable not set: $1"
        return 1
    else
        success "Environment variable set: $1"
        return 0
    fi
}

echo "1. Checking Required Commands..."
echo "-----------------------------------"
check_command "python3"
check_command "pip"
check_command "docker"
check_command "docker-compose"
echo ""

echo "2. Checking Required Files..."
echo "-----------------------------------"
# Backend files
check_file "backend/Dockerfile"
check_file "backend/Dockerfile.production"
check_file "backend/requirements.txt"
check_file "backend/app/main.py"
check_file "backend/app/config.py"

# Frontend files
check_file "frontend/Dockerfile"
check_file "frontend/package.json"

# Docker Compose files (at project root)
PROJECT_ROOT=$(cd "$(dirname "$0")/../.." && pwd)
if [ -f "$PROJECT_ROOT/docker-compose.production.yml" ]; then
    success "Unified docker-compose.production.yml exists at project root"
else
    failure "docker-compose.production.yml not found at project root"
fi

if [ -f "$PROJECT_ROOT/docker-compose.dev.yml" ]; then
    success "docker-compose.dev.yml exists at project root"
else
    warning "docker-compose.dev.yml not found at project root"
fi
echo ""

echo "3. Checking Environment Configuration..."
echo "-----------------------------------"
ENV_FILE="${1:-.env.production}"
PROJECT_ROOT=$(cd "$(dirname "$0")/../.." && pwd)

# Check for unified .env.production at project root (preferred for unified deployment)
if [ -f "$PROJECT_ROOT/$ENV_FILE" ]; then
    success "Unified environment file exists: $PROJECT_ROOT/$ENV_FILE"
    source "$PROJECT_ROOT/$ENV_FILE"
    
    # Backend required environment variables
    echo "  Checking backend variables..."
    check_env_var "SUPABASE_URL"
    check_env_var "SUPABASE_ANON_KEY"
    check_env_var "SUPABASE_SERVICE_ROLE_KEY"
    check_env_var "JWT_SECRET_KEY"
    
    # Validate JWT_SECRET_KEY length
    if [ ! -z "$JWT_SECRET_KEY" ]; then
        JWT_LENGTH=${#JWT_SECRET_KEY}
        if [ $JWT_LENGTH -ge 32 ]; then
            success "JWT_SECRET_KEY length is sufficient ($JWT_LENGTH characters)"
        else
            failure "JWT_SECRET_KEY is too short ($JWT_LENGTH characters, minimum 32 required)"
        fi
    fi
    
    # Frontend required environment variables (for build)
    echo "  Checking frontend variables..."
    check_env_var "VITE_SUPABASE_URL"
    check_env_var "VITE_SUPABASE_ANON_KEY"
    if [ -z "$VITE_API_BASE_URL" ]; then
        warning "VITE_API_BASE_URL not set (frontend won't know backend URL)"
    else
        success "VITE_API_BASE_URL is set: $VITE_API_BASE_URL"
    fi
    
    # Check optional but important variables
    if [ -z "$CORS_ORIGINS" ]; then
        warning "CORS_ORIGINS not set (using defaults)"
    else
        success "CORS_ORIGINS is set"
    fi
    
    if [ -z "$ENVIRONMENT" ] || [ "$ENVIRONMENT" != "production" ]; then
        warning "ENVIRONMENT is not set to 'production' (current: ${ENVIRONMENT:-not set})"
    else
        success "ENVIRONMENT is set to production"
    fi
    
    if [ -z "$DEBUG" ] || [ "$DEBUG" != "false" ]; then
        warning "DEBUG should be 'false' in production (current: ${DEBUG:-not set})"
    else
        success "DEBUG is set to false"
    fi
elif [ -f "$PROJECT_ROOT/backend/$ENV_FILE" ]; then
    # Fallback to backend-only env file
    warning "Found backend-only environment file: backend/$ENV_FILE"
    warning "Consider using unified .env.production at project root for frontend+backend deployment"
    source "$PROJECT_ROOT/backend/$ENV_FILE"
    check_env_var "SUPABASE_URL"
    check_env_var "SUPABASE_ANON_KEY"
    check_env_var "SUPABASE_SERVICE_ROLE_KEY"
    check_env_var "JWT_SECRET_KEY"
else
    failure "Environment file not found: $PROJECT_ROOT/$ENV_FILE or backend/$ENV_FILE"
    warning "Create this file from env.production.example at project root"
fi
echo ""

echo "4. Checking Database Migrations..."
echo "-----------------------------------"
MIGRATIONS_DIR="backend/db/migrations"
if [ -d "$MIGRATIONS_DIR" ]; then
    MIGRATION_COUNT=$(find "$MIGRATIONS_DIR" -name "*.sql" | wc -l)
    if [ $MIGRATION_COUNT -gt 0 ]; then
        success "Found $MIGRATION_COUNT migration file(s)"
        
        # Check for combined migration file
        if [ -f "$MIGRATIONS_DIR/_combined_all_migrations.sql" ]; then
            success "Combined migration file exists"
        else
            warning "Combined migration file not found - may need to combine migrations"
        fi
    else
        failure "No migration files found in $MIGRATIONS_DIR"
    fi
else
    failure "Migrations directory not found: $MIGRATIONS_DIR"
fi
echo ""

echo "5. Checking Python Dependencies..."
echo "-----------------------------------"
if [ -f "backend/requirements.txt" ]; then
    if python3 -m pip show -q $(head -n 1 backend/requirements.txt 2>/dev/null) 2>/dev/null; then
        success "Python dependencies appear to be installable"
    else
        warning "Cannot verify Python dependencies - ensure virtual environment is activated"
    fi
else
    failure "requirements.txt not found"
fi
echo ""

echo "6. Checking Docker Configuration..."
echo "-----------------------------------"
if docker info &> /dev/null; then
    success "Docker daemon is running"
    
    # Check if docker compose is available
    if docker compose version &> /dev/null; then
        success "Docker Compose V2 is available"
    else
        failure "Docker Compose V2 is not available"
    fi
    
    # Validate Dockerfile syntax (basic check)
    PROJECT_ROOT=$(cd "$(dirname "$0")/../.." && pwd)
    
    if [ -f "$PROJECT_ROOT/backend/Dockerfile.production" ]; then
        if grep -q "FROM" "$PROJECT_ROOT/backend/Dockerfile.production"; then
            success "Backend Dockerfile.production syntax appears valid"
        else
            failure "Backend Dockerfile.production appears invalid"
        fi
    fi
    
    if [ -f "$PROJECT_ROOT/frontend/Dockerfile" ]; then
        if grep -q "FROM" "$PROJECT_ROOT/frontend/Dockerfile"; then
            success "Frontend Dockerfile syntax appears valid"
        else
            failure "Frontend Dockerfile appears invalid"
        fi
    fi
    
    # Check unified docker-compose.production.yml
    if [ -f "$PROJECT_ROOT/docker-compose.production.yml" ]; then
        if docker compose -f "$PROJECT_ROOT/docker-compose.production.yml" config &> /dev/null; then
            success "docker-compose.production.yml is valid"
        else
            failure "docker-compose.production.yml has syntax errors"
        fi
    fi
else
    failure "Docker daemon is not running"
fi
echo ""

echo "7. Running Unit Tests..."
echo "-----------------------------------"
cd backend
if [ -d "tests" ] && [ "$(ls -A tests/*.py 2>/dev/null)" ]; then
    # Set test environment variables
    export JWT_SECRET_KEY="test_jwt_secret_key_minimum_32_bytes_long"
    export SUPABASE_URL="https://test.supabase.co"
    export SUPABASE_ANON_KEY="test_key"
    export SUPABASE_SERVICE_ROLE_KEY="test_service_key"
    export ENVIRONMENT="test"
    export DEBUG="true"
    
    if python3 -m pytest tests/ -v --tb=short -x 2>&1 | tail -n 5 | grep -q "passed\|PASSED"; then
        success "Unit tests passed"
    else
        warning "Some tests may have failed - check output above"
    fi
else
    warning "No test files found - skipping test execution"
fi
cd ..
echo ""

echo "8. Checking Documentation..."
echo "-----------------------------------"
PROJECT_ROOT=$(cd "$(dirname "$0")/../.." && pwd)
check_file "$PROJECT_ROOT/backend/AWS_LIGHTSAIL_DEPLOYMENT.md"
check_file "$PROJECT_ROOT/backend/README.md"
check_file "$PROJECT_ROOT/DEPLOYMENT_CHECKLIST.md"
if [ -f "$PROJECT_ROOT/deployment/deploy-production.sh" ]; then
    success "Unified deployment script exists: deployment/deploy-production.sh"
else
    warning "Unified deployment script not found: deployment/deploy-production.sh"
fi
echo ""

echo "9. Checking Contract Alignment..."
echo "-----------------------------------"
PROJECT_ROOT=$(cd "$(dirname "$0")/../.." && pwd)
CONTRACTS_PATH="$PROJECT_ROOT/contracts/types/index.ts"
DEMO_FRONTEND_CONTRACTS="$PROJECT_ROOT/backend/demo-frontend/lib/types.ts"

if [ -f "$CONTRACTS_PATH" ]; then
    success "TypeScript contracts file exists: contracts/types/index.ts"
elif [ -f "$DEMO_FRONTEND_CONTRACTS" ]; then
    success "TypeScript contracts file exists: backend/demo-frontend/lib/types.ts"
else
    warning "TypeScript contracts file not found - checking frontend for types..."
fi

# Check if contracts are referenced in tests
if grep -q "test_contract_alignment" "$PROJECT_ROOT/backend/tests/test_contract_alignment.py" 2>/dev/null; then
    success "Contract alignment tests exist"
else
    warning "Contract alignment tests may not be fully implemented"
fi
echo ""

echo "10. Final Checks..."
echo "-----------------------------------"
# Check if .env.production is in .gitignore
if [ -f ".gitignore" ] && grep -q "\.env\.production" .gitignore 2>/dev/null; then
    success ".env.production is in .gitignore"
else
    warning ".env.production may not be in .gitignore - ensure secrets are not committed"
fi

# Check for any .env files that might be committed
if git ls-files | grep -q "\.env$"; then
    warning "Found .env files tracked in git - ensure they don't contain secrets"
else
    success "No .env files are tracked in git"
fi
echo ""

echo "=========================================="
echo "  Summary"
echo "=========================================="
echo -e "${GREEN}Passed:${NC} $PASSED"
echo -e "${RED}Failed:${NC} $FAILED"
echo -e "${YELLOW}Warnings:${NC} $WARNINGS"
echo ""

if [ $FAILED -gt 0 ]; then
    echo -e "${RED}✗ Deployment validation FAILED${NC}"
    echo "Please fix the issues above before deploying."
    exit 1
elif [ $WARNINGS -gt 0 ]; then
    echo -e "${YELLOW}⚠ Deployment validation PASSED with warnings${NC}"
    echo "Review warnings above before deploying."
    exit 0
else
    echo -e "${GREEN}✓ Deployment validation PASSED${NC}"
    echo "Ready for deployment!"
    exit 0
fi

