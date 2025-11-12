#!/bin/bash

# Quick EC2 Setup Script for Notification System
# Run this on your EC2 instance after cloning the repo

set -e  # Exit on error

echo "========================================="
echo "🚀 Notification System - EC2 Quick Setup"
echo "========================================="
echo ""

# Install Docker Compose v2 (recommended)
echo "📦 Installing Docker Compose v2..."
sudo apt-get update
sudo apt-get install -y docker-compose-plugin

echo ""
echo "✅ Docker Compose installed!"
docker compose version

echo ""
echo "========================================="
echo "✅ Setup Complete!"
echo "========================================="
echo ""
echo "Next steps:"
echo "1. Create .env file: cp .env.example .env"
echo "2. Edit .env: nano .env"
echo "3. Deploy: docker compose -f docker-compose.prod.yml up -d --build"
echo ""
