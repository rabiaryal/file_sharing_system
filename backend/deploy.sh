#!/bin/bash
# File Sharing System - Nginx & PgBouncer Deployment Script
# This script helps deploy and manage the services with proper ordering

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
log_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

log_success() {
    echo -e "${GREEN}✓${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}⚠${NC} $1"
}

log_error() {
    echo -e "${RED}✗${NC} $1"
}

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Main menu
show_menu() {
    echo ""
    echo -e "${BLUE}File Sharing System - Docker Services Manager${NC}"
    echo "================================================"
    echo "1. Full deployment (build and start all services)"
    echo "2. Start services (without rebuild)"
    echo "3. Stop all services"
    echo "4. Restart services"
    echo "5. View service status"
    echo "6. View logs"
    echo "7. Run health checks"
    echo "8. View PgBouncer stats"
    echo "9. View Nginx config"
    echo "10. Exit"
    echo ""
}

# Deploy services with proper ordering
deploy_full() {
    log_info "Starting full deployment..."
    
    # Check if .env file exists
    if [ ! -f .env ]; then
        log_error ".env file not found. Please create it first."
        return 1
    fi
    
    # Build all images
    log_info "Building Docker images..."
    docker-compose build --no-cache
    
    # Start PostgreSQL first
    log_info "Starting PostgreSQL..."
    docker-compose up -d db
    
    # Wait for PostgreSQL to be healthy
    log_info "Waiting for PostgreSQL to be ready..."
    sleep 10
    for i in {1..30}; do
        if docker-compose exec -T db pg_isready -U $(grep POSTGRES_USER .env | cut -d= -f2) >/dev/null 2>&1; then
            log_success "PostgreSQL is ready"
            break
        fi
        if [ $i -eq 30 ]; then
            log_error "PostgreSQL failed to start"
            return 1
        fi
        echo -n "."
        sleep 2
    done
    
    # Start Redis
    log_info "Starting Redis..."
    docker-compose up -d redis
    
    # Wait for Redis
    sleep 3
    
    # Start PgBouncer
    log_info "Starting PgBouncer..."
    docker-compose up -d pgbouncer
    
    # Wait for PgBouncer
    sleep 3
    
    # Start Django web server
    log_info "Starting Django web server..."
    docker-compose up -d web
    
    # Wait for Django to be ready
    log_info "Waiting for Django to be ready..."
    for i in {1..30}; do
        if docker-compose exec -T web curl -f http://localhost:8000/health >/dev/null 2>&1; then
            log_success "Django is ready"
            break
        fi
        if [ $i -eq 30 ]; then
            log_warn "Django is taking longer than expected, continuing anyway..."
            break
        fi
        echo -n "."
        sleep 2
    done
    
    # Start Celery worker
    log_info "Starting Celery worker..."
    docker-compose up -d celery_worker
    
    # Start frontend
    log_info "Starting frontend..."
    docker-compose up -d frontend
    
    # Start Nginx last
    log_info "Starting Nginx reverse proxy..."
    docker-compose up -d nginx
    
    # Final status
    log_info "Waiting for all services to stabilize..."
    sleep 5
    
    log_success "Full deployment complete!"
    show_service_status
}

# Start services without rebuild
start_services() {
    log_info "Starting services..."
    
    # Start in order
    docker-compose up -d db
    sleep 5
    
    docker-compose up -d redis pgbouncer
    sleep 3
    
    docker-compose up -d web celery_worker
    sleep 3
    
    docker-compose up -d frontend nginx
    
    log_success "Services started"
    show_service_status
}

# Stop all services
stop_services() {
    log_info "Stopping all services..."
    docker-compose down
    log_success "All services stopped"
}

# Restart services
restart_services() {
    log_info "Restarting services..."
    docker-compose restart
    sleep 3
    log_success "Services restarted"
    show_service_status
}

# Show service status
show_service_status() {
    echo ""
    log_info "Service Status:"
    echo "================================================"
    docker-compose ps
    echo ""
}

# View logs
view_logs() {
    echo ""
    echo -e "${BLUE}Select service to view logs:${NC}"
    echo "1. All services"
    echo "2. Django (web)"
    echo "3. Nginx"
    echo "4. PgBouncer"
    echo "5. PostgreSQL (db)"
    echo "6. Redis"
    echo "7. Celery worker"
    echo "8. Frontend"
    echo "9. Go back"
    echo ""
    read -p "Enter choice: " log_choice
    
    case $log_choice in
        1) docker-compose logs -f ;;
        2) docker-compose logs -f web ;;
        3) docker-compose logs -f nginx ;;
        4) docker-compose logs -f pgbouncer ;;
        5) docker-compose logs -f db ;;
        6) docker-compose logs -f redis ;;
        7) docker-compose logs -f celery_worker ;;
        8) docker-compose logs -f frontend ;;
        9) return ;;
        *) log_error "Invalid choice" ;;
    esac
}

# Run health checks
run_health_checks() {
    echo ""
    log_info "Running health checks..."
    echo "================================================"
    
    # Check PostgreSQL
    log_info "Checking PostgreSQL..."
    if docker-compose exec -T db pg_isready -U $(grep POSTGRES_USER .env | cut -d= -f2) >/dev/null 2>&1; then
        log_success "PostgreSQL is healthy"
    else
        log_error "PostgreSQL is not responding"
    fi
    
    # Check PgBouncer
    log_info "Checking PgBouncer..."
    if docker-compose exec -T pgbouncer psql -h localhost -p 6432 -U postgres -d postgres -c "SELECT 1;" >/dev/null 2>&1; then
        log_success "PgBouncer is healthy"
    else
        log_error "PgBouncer is not responding"
    fi
    
    # Check Redis
    log_info "Checking Redis..."
    if docker-compose exec -T redis redis-cli ping >/dev/null 2>&1; then
        log_success "Redis is healthy"
    else
        log_error "Redis is not responding"
    fi
    
    # Check Django
    log_info "Checking Django..."
    if docker-compose exec -T web curl -f http://localhost:8000/health >/dev/null 2>&1; then
        log_success "Django is healthy"
    else
        log_error "Django is not responding"
    fi
    
    # Check Nginx
    log_info "Checking Nginx..."
    if docker-compose exec -T nginx wget --quiet --tries=1 --spider http://localhost/ 2>/dev/null; then
        log_success "Nginx is healthy"
    else
        log_error "Nginx is not responding"
    fi
    
    echo ""
}

# Show PgBouncer stats
show_pgbouncer_stats() {
    echo ""
    log_info "PgBouncer Statistics"
    echo "================================================"
    
    echo ""
    log_info "Connection Pool Status:"
    docker-compose exec -T pgbouncer psql -h localhost -p 6432 -U postgres -d pgbouncer -c "SHOW POOLS;" 2>/dev/null || log_error "Failed to get pool status"
    
    echo ""
    log_info "Connection Statistics:"
    docker-compose exec -T pgbouncer psql -h localhost -p 6432 -U postgres -d pgbouncer -c "SHOW STATS;" 2>/dev/null || log_error "Failed to get statistics"
    
    echo ""
    log_info "Client Connections:"
    docker-compose exec -T pgbouncer psql -h localhost -p 6432 -U postgres -d pgbouncer -c "SHOW CLIENTS;" 2>/dev/null || log_error "Failed to get clients"
    
    echo ""
}

# Show Nginx config
show_nginx_config() {
    echo ""
    log_info "Nginx Configuration"
    echo "================================================"
    cat nginx.conf
    echo ""
}

# Main loop
while true; do
    show_menu
    read -p "Enter your choice: " choice
    
    case $choice in
        1) deploy_full ;;
        2) start_services ;;
        3) stop_services ;;
        4) restart_services ;;
        5) show_service_status ;;
        6) view_logs ;;
        7) run_health_checks ;;
        8) show_pgbouncer_stats ;;
        9) show_nginx_config ;;
        10) 
            log_info "Exiting..."
            exit 0
            ;;
        *)
            log_error "Invalid choice. Please try again."
            ;;
    esac
done
