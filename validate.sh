#!/bin/bash
# Configuration Validation Script
# Verifies that all nginx and pgbouncer components are properly configured

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Counters
PASSED=0
FAILED=0
WARNINGS=0

# Functions
check_pass() {
    echo -e "${GREEN}✓${NC} $1"
    ((PASSED++))
}

check_fail() {
    echo -e "${RED}✗${NC} $1"
    ((FAILED++))
}

check_warn() {
    echo -e "${YELLOW}⚠${NC} $1"
    ((WARNINGS++))
}

check_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

# Get directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════${NC}"
echo -e "${BLUE}Nginx & PgBouncer Configuration Validation${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════${NC}"
echo ""

# ==================== ENVIRONMENT CHECKS ====================
echo -e "${BLUE}1. Environment Configuration${NC}"
echo "───────────────────────────────────────────────────"

# Check .env file
if [ -f ".env" ]; then
    check_pass ".env file exists"
    
    # Check required variables
    if grep -q "^SECRET_KEY=" .env; then
        check_pass "SECRET_KEY is configured"
    else
        check_fail "SECRET_KEY is not configured in .env"
    fi
    
    if grep -q "^DB_HOST=pgbouncer" .env; then
        check_pass "DB_HOST points to pgbouncer"
    else
        check_warn "DB_HOST may not be set to pgbouncer"
    fi
    
    if grep -q "^DB_PORT=6432" .env; then
        check_pass "DB_PORT is set to 6432 (pgbouncer)"
    else
        check_warn "DB_PORT may not be set to 6432"
    fi
else
    check_fail ".env file not found"
fi

echo ""

# ==================== FILE STRUCTURE CHECKS ====================
echo -e "${BLUE}2. File Structure${NC}"
echo "───────────────────────────────────────────────────"

# Check required files
files=(
    "docker-compose.yml"
    "nginx.conf"
    "pgbouncer.ini"
    "Dockerfile"
    "core/settings.py"
    "files/urls.py"
    "files/secure_links.py"
    "core/converters.py"
)

for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        check_pass "$file exists"
    else
        check_fail "$file not found"
    fi
done

echo ""

# ==================== DOCKER CHECKS ====================
echo -e "${BLUE}3. Docker Configuration${NC}"
echo "───────────────────────────────────────────────────"

# Check Docker command
if command -v docker &> /dev/null; then
    check_pass "Docker is installed"
else
    check_fail "Docker is not installed"
fi

# Check Docker Compose
if command -v docker-compose &> /dev/null; then
    check_pass "Docker Compose is installed"
else
    check_fail "Docker Compose is not installed"
fi

# Check docker-compose.yml syntax
if docker-compose config > /dev/null 2>&1; then
    check_pass "docker-compose.yml is valid"
else
    check_fail "docker-compose.yml has syntax errors"
fi

echo ""

# ==================== NGINX CONFIGURATION CHECKS ====================
echo -e "${BLUE}4. Nginx Configuration${NC}"
echo "───────────────────────────────────────────────────"

# Check for required nginx config elements
if grep -q "upstream django_backend" nginx.conf; then
    check_pass "nginx.conf has upstream definition"
else
    check_fail "nginx.conf missing upstream definition"
fi

if grep -q "location /api/" nginx.conf; then
    check_pass "nginx.conf has API location block"
else
    check_fail "nginx.conf missing API location block"
fi

if grep -q "limit_req" nginx.conf; then
    check_pass "nginx.conf has rate limiting configured"
else
    check_warn "nginx.conf does not have rate limiting"
fi

if grep -q "gzip on" nginx.conf; then
    check_pass "nginx.conf has gzip compression enabled"
else
    check_warn "nginx.conf does not have gzip compression"
fi

if grep -q "X-Frame-Options" nginx.conf; then
    check_pass "nginx.conf has security headers"
else
    check_warn "nginx.conf missing security headers"
fi

echo ""

# ==================== PGBOUNCER CONFIGURATION CHECKS ====================
echo -e "${BLUE}5. PgBouncer Configuration${NC}"
echo "───────────────────────────────────────────────────"

# Check pgbouncer.ini for required settings
if grep -q "pool_mode = transaction" pgbouncer.ini; then
    check_pass "pgbouncer.ini has transaction mode enabled"
else
    check_fail "pgbouncer.ini does not have transaction mode"
fi

if grep -q "default_pool_size" pgbouncer.ini; then
    check_pass "pgbouncer.ini has pool size configured"
else
    check_fail "pgbouncer.ini missing pool size configuration"
fi

if grep -q "max_client_conn" pgbouncer.ini; then
    check_pass "pgbouncer.ini has max client connections configured"
else
    check_fail "pgbouncer.ini missing max client connections"
fi

echo ""

# ==================== DJANGO SETTINGS CHECKS ====================
echo -e "${BLUE}6. Django Settings Configuration${NC}"
echo "───────────────────────────────────────────────────"

# Check settings.py
if grep -q "SECURE_PROXY_SSL_HEADER" core/settings.py; then
    check_pass "Django settings has proxy SSL header"
else
    check_warn "Django settings missing proxy SSL header"
fi

if grep -q "USE_X_FORWARDED_HOST" core/settings.py; then
    check_pass "Django settings has X-Forwarded-Host enabled"
else
    check_warn "Django settings missing X-Forwarded-Host"
fi

if grep -q "CONN_MAX_AGE" core/settings.py; then
    check_pass "Django settings has connection pooling configured"
else
    check_warn "Django settings missing connection pooling"
fi

echo ""

# ==================== DOCKERFILE CHECKS ====================
echo -e "${BLUE}7. Dockerfile Configuration${NC}"
echo "───────────────────────────────────────────────────"

# Check Dockerfile
if grep -q "gunicorn" Dockerfile; then
    check_pass "Dockerfile uses gunicorn"
else
    check_fail "Dockerfile does not use gunicorn"
fi

if grep -q "collectstatic" Dockerfile; then
    check_pass "Dockerfile collects static files"
else
    check_warn "Dockerfile does not collect static files"
fi

if grep -q "HEALTHCHECK" Dockerfile; then
    check_pass "Dockerfile has health check"
else
    check_warn "Dockerfile missing health check"
fi

echo ""

# ==================== DOCUMENTATION CHECKS ====================
echo -e "${BLUE}8. Documentation${NC}"
echo "───────────────────────────────────────────────────"

docs=(
    "NGINX_PGBOUNCER.md"
    "PRODUCTION_DEPLOYMENT.md"
    "QUICK_REFERENCE.md"
    "ARCHITECTURE.md"
)

for doc in "${docs[@]}"; do
    if [ -f "$doc" ]; then
        check_pass "$doc exists"
    else
        check_fail "$doc not found"
    fi
done

echo ""

# ==================== SUMMARY ====================
echo -e "${BLUE}═══════════════════════════════════════════════════${NC}"
echo -e "${BLUE}Validation Summary${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════${NC}"

TOTAL=$((PASSED + FAILED + WARNINGS))

echo ""
echo -e "${GREEN}Passed: $PASSED${NC}"
echo -e "${YELLOW}Warnings: $WARNINGS${NC}"
echo -e "${RED}Failed: $FAILED${NC}"
echo ""
echo "Total checks: $TOTAL"
echo ""

if [ $FAILED -eq 0 ]; then
    if [ $WARNINGS -eq 0 ]; then
        echo -e "${GREEN}✓ All checks passed! Configuration is ready.${NC}"
        echo ""
        echo "Next steps:"
        echo "1. chmod +x deploy.sh"
        echo "2. ./deploy.sh"
        echo "3. Select option 1: Full deployment"
    else
        echo -e "${YELLOW}⚠ All critical checks passed, but there are warnings.${NC}"
        echo ""
        echo "Review the warnings above to ensure optimal configuration."
        echo "The system will still work, but performance may not be optimal."
    fi
else
    echo -e "${RED}✗ Configuration has errors that must be fixed.${NC}"
    echo ""
    echo "Please address the failed checks above before deploying."
fi

echo ""

# Exit with appropriate code
if [ $FAILED -gt 0 ]; then
    exit 1
else
    exit 0
fi
