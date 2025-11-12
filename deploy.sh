#!/bin/bash

# Quick Deployment Script for Distributed Notification System
# Usage: ./deploy.sh [dev|prod]

set -e

MODE=${1:-dev}
COMPOSE_FILE="docker-compose.yml"

if [ "$MODE" = "prod" ]; then
    COMPOSE_FILE="docker-compose.prod.yml"
    echo "🚀 Deploying in PRODUCTION mode..."
    
    # Check if .env exists
    if [ ! -f .env ]; then
        echo "❌ Error: .env file not found!"
        echo "📋 Copy .env.example to .env and configure it first:"
        echo "   cp .env.example .env"
        echo "   nano .env"
        exit 1
    fi
    
    # Warn about production
    echo "⚠️  WARNING: You are deploying to PRODUCTION!"
    echo "Have you:"
    echo "  - Changed all default passwords?"
    echo "  - Set up SSL/TLS?"
    echo "  - Configured SMTP credentials?"
    echo "  - Added Firebase credentials?"
    read -p "Continue? (yes/no): " CONFIRM
    if [ "$CONFIRM" != "yes" ]; then
        echo "Deployment cancelled."
        exit 0
    fi
else
    echo "🔧 Deploying in DEVELOPMENT mode..."
fi

# Check Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Build images
echo "📦 Building Docker images..."
docker-compose -f $COMPOSE_FILE build

# Stop existing containers
echo "🛑 Stopping existing containers..."
docker-compose -f $COMPOSE_FILE down

# Start services
echo "🚀 Starting services..."
docker-compose -f $COMPOSE_FILE up -d

# Wait for services to be healthy
echo "⏳ Waiting for services to be healthy..."
sleep 20

# Check status
echo ""
echo "📊 Service Status:"
docker-compose -f $COMPOSE_FILE ps

# Health checks
echo ""
echo "🏥 Running health checks..."

check_service() {
    local name=$1
    local url=$2
    if curl -sf $url > /dev/null; then
        echo "✅ $name is healthy"
        return 0
    else
        echo "❌ $name is not responding"
        return 1
    fi
}

check_service "API Gateway" "http://localhost:8000/health"
check_service "User Service" "http://localhost:8001/health"
check_service "Template Service" "http://localhost:8002/health"

echo ""
echo "🎉 Deployment complete!"
echo ""
echo "📝 Next steps:"
echo "  1. View logs: docker-compose -f $COMPOSE_FILE logs -f"
echo "  2. Run tests: ./test_all_services.sh"
echo "  3. Access API: http://localhost:8000"
echo ""

if [ "$MODE" = "prod" ]; then
    echo "🔒 Production reminders:"
    echo "  - Set up SSL/TLS with Nginx or Traefik"
    echo "  - Configure firewall rules"
    echo "  - Set up monitoring and backups"
    echo "  - Review DEPLOYMENT.md for details"
fi
