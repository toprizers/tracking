#!/bin/bash
# Employee Monitor - VPS Deployment Script
# Run this on your VPS (Ubuntu 22.04)

set -e

echo "========================================="
echo "  Employee Monitor - VPS Setup"
echo "========================================="

echo "[1/9] Updating system..."
sudo apt update && sudo apt upgrade -y

echo "[2/9] Installing Python and dependencies..."
sudo apt install -y python3 python3-pip python3-venv mysql-server nginx certbot python3-certbot-nginx

echo "[3/9] Setting up MySQL..."
sudo mysql -e "CREATE DATABASE IF NOT EXISTS employee_monitor;"
sudo mysql -e "CREATE USER IF NOT EXISTS 'monitor_user'@'localhost' IDENTIFIED BY 'CHANGE_THIS_PASSWORD';"
sudo mysql -e "GRANT ALL PRIVILEGES ON employee_monitor.* TO 'monitor_user'@'localhost';"
sudo mysql -e "FLUSH PRIVILEGES;"

echo "[4/9] Creating project directory..."
sudo mkdir -p /opt/employee-monitor
sudo cp -r server/* /opt/employee-monitor/
cd /opt/employee-monitor

echo "[5/9] Setting up Python virtual environment..."
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

echo "[6/9] Configuring environment..."
cat > .env << 'EOF'
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
DATABASE_URL=mysql+pymysql://monitor_user:CHANGE_THIS_PASSWORD@localhost/employee_monitor
FLASK_APP=app.py
FLASK_ENV=production
SMTP_EMAIL=
SMTP_PASSWORD=
EOF

echo "[7/9] Creating uploads directory..."
mkdir -p uploads
chmod 755 uploads

echo "[8/9] Creating systemd service..."
sudo tee /etc/systemd/system/employee-monitor.service > /dev/null << EOF
[Unit]
Description=Employee Monitor Server
After=network.target mysql.service

[Service]
User=root
WorkingDirectory=/opt/employee-monitor
Environment="PATH=/opt/employee-monitor/venv/bin"
ExecStart=/opt/employee-monitor/venv/bin/python app.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

echo "[9/9] Starting service..."
sudo systemctl daemon-reload
sudo systemctl enable employee-monitor
sudo systemctl start employee-monitor

echo ""
echo "========================================="
echo "  Setup Complete!"
echo "========================================="
echo ""
echo "Server is running at: http://YOUR_VPS_IP:5000"
echo ""
echo "Default login:"
echo "  Username: admin"
echo "  Password: admin123"
echo ""
echo "IMPORTANT:"
echo "1. Change MySQL password in /opt/employee-monitor/.env"
echo "2. Change admin password in dashboard"
echo "3. Open port 5000 in firewall"
echo ""
echo "To check status: sudo systemctl status employee-monitor"
echo "To restart: sudo systemctl restart employee-monitor"
echo "To view logs: sudo journalctl -u employee-monitor -f"
echo ""
echo "For SSL (optional):"
echo "  sudo certbot --nginx -d yourdomain.com"
