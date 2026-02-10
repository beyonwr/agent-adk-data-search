#!/bin/bash

# ADK Data Search Production Deployment Script
# This script should be run on the production server

set -e

echo "======================================="
echo "ADK Data Search Deployment Script"
echo "======================================="

# Configuration
APP_DIR="/opt/agent-adk-data-search"
SERVICE_NAME="adk-web"
PYTHON_VERSION="3.10"

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Please run as root or with sudo"
    exit 1
fi

# Step 1: Install system dependencies
echo ""
echo "Step 1: Installing system dependencies..."
apt-get update
apt-get install -y python${PYTHON_VERSION} python${PYTHON_VERSION}-venv python3-pip git

# Step 2: Create application directory
echo ""
echo "Step 2: Setting up application directory..."
mkdir -p ${APP_DIR}

# Step 3: Clone or update repository
echo ""
echo "Step 3: Cloning/Updating repository..."
if [ -d "${APP_DIR}/.git" ]; then
    echo "Repository exists, pulling latest changes..."
    cd ${APP_DIR}
    git pull
else
    echo "Cloning repository..."
    # Replace with your repository URL
    read -p "Enter your git repository URL: " REPO_URL
    git clone ${REPO_URL} ${APP_DIR}
    cd ${APP_DIR}
fi

# Step 4: Create virtual environment
echo ""
echo "Step 4: Creating virtual environment..."
if [ ! -d "${APP_DIR}/venv" ]; then
    python${PYTHON_VERSION} -m venv ${APP_DIR}/venv
fi

# Step 5: Install Python dependencies
echo ""
echo "Step 5: Installing Python dependencies..."
${APP_DIR}/venv/bin/pip install --upgrade pip
${APP_DIR}/venv/bin/pip install -r ${APP_DIR}/requirements.txt

# Step 6: Setup environment file
echo ""
echo "Step 6: Setting up environment file..."
if [ ! -f "${APP_DIR}/.env" ]; then
    echo "Creating .env file from template..."
    cp ${APP_DIR}/env.sample ${APP_DIR}/.env
    echo ""
    echo "IMPORTANT: Please edit ${APP_DIR}/.env with your production settings"
    echo "Press Enter after you've configured the .env file..."
    read
fi

# Step 7: Setup systemd service
echo ""
echo "Step 7: Setting up systemd service..."
cp ${APP_DIR}/adk-web.service /etc/systemd/system/${SERVICE_NAME}.service

# Step 8: Configure permissions
echo ""
echo "Step 8: Configuring permissions..."
chown -R www-data:www-data ${APP_DIR}

# Step 9: Enable and start service
echo ""
echo "Step 9: Enabling and starting service..."
systemctl daemon-reload
systemctl enable ${SERVICE_NAME}.service
systemctl restart ${SERVICE_NAME}.service

# Step 10: Check service status
echo ""
echo "Step 10: Checking service status..."
sleep 2
systemctl status ${SERVICE_NAME}.service --no-pager

echo ""
echo "======================================="
echo "Deployment completed!"
echo "======================================="
echo ""
echo "Service commands:"
echo "  - Check status: sudo systemctl status ${SERVICE_NAME}"
echo "  - Start service: sudo systemctl start ${SERVICE_NAME}"
echo "  - Stop service: sudo systemctl stop ${SERVICE_NAME}"
echo "  - Restart service: sudo systemctl restart ${SERVICE_NAME}"
echo "  - View logs: sudo journalctl -u ${SERVICE_NAME} -f"
echo "  - View log file: tail -f /var/log/adk-web.log"
echo ""
echo "Your service is now running at http://YOUR_SERVER_IP:8000"
echo ""
