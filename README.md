# Employee Monitoring System

A complete employee monitoring solution with real-time dashboard, screenshots, activity tracking, and alert system.

## Features

### Core Features
- **Automatic Screenshots** - Capture every 30 minutes (configurable)
- **Activity Tracking** - Mouse clicks, keystrokes, idle time monitoring
- **Real-time Dashboard** - Live updates via WebSocket
- **Alert System** - Idle alerts, input failure alerts
- **Consent-based Monitoring** - Legal compliance with consent forms

### Dashboard Features
- Employee management (Add/Edit/Delete)
- Screenshot gallery with lightbox viewer
- Activity reports with charts (Chart.js)
- CSV export for reports
- Search and filter functionality
- Live notifications
- Settings page

### Agent Features
- System tray icon (optional)
- Auto-start on boot
- Pause/Resume monitoring
- Manual screenshot trigger
- Offline handling

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Backend | Python Flask |
| Database | MySQL (Production) / SQLite (Testing) |
| Frontend | Bootstrap 5 + Chart.js |
| Real-time | Flask-SocketIO |
| Agent | Python (mss, pynput, psutil) |

## Quick Start

### Local Testing

```bash
# Clone or copy project
cd remote/server

# Install dependencies
pip install -r requirements.txt

# Run server
python app.py

# Access dashboard: http://localhost:5000
# Login: admin / admin123
```

### VPS Deployment (Ubuntu 22.04)

```bash
# Upload project to VPS
scp -r server/ root@YOUR_VPS_IP:/opt/employee-monitor

# SSH into VPS
ssh root@YOUR_VPS_IP

# Run deployment script
cd /opt/employee-monitor
chmod +x deploy.sh
sudo ./deploy.sh
```

### Agent Setup (Employee Laptop)

1. Copy `agent/` folder to employee laptop
2. Edit `config.json`:
```json
{
    "server_url": "http://YOUR_VPS_IP:5000",
    "agent_key": "EMPLOYEE_AGENT_KEY"
}
```

3. Install and run:
```bash
cd agent
pip install -r requirements.txt
python main.py
```

#### Agent Options
```bash
# Run with system tray icon
python main.py --tray

# Install auto-start on boot
python main.py --install-autostart

# Run in background (Linux)
nohup python main.py &
```

## Project Structure

```
remote/
├── server/                     # Backend
│   ├── app.py                 # Main Flask app
│   ├── config.py              # Configuration
│   ├── extensions.py          # Flask extensions
│   ├── schema.sql             # Database schema
│   ├── models/                # Database models
│   ├── routes/                # API routes
│   │   ├── auth.py           # Authentication
│   │   ├── employees.py      # Employee management
│   │   ├── screenshots.py    # Screenshot handling
│   │   ├── alerts.py         # Alert system
│   │   ├── reports.py        # Activity reports
│   │   ├── settings.py       # Settings page
│   │   └── agent_api.py      # Agent API endpoints
│   ├── templates/             # HTML templates
│   ├── static/                # CSS, JS
│   └── uploads/               # Screenshot storage
│
├── agent/                      # Employee Laptop
│   ├── main.py                # Agent entry point
│   ├── capture.py             # Screenshot logic
│   ├── activity.py            # Input tracking
│   ├── uploader.py            # Server upload
│   ├── tray.py                # System tray icon
│   └── config.json            # Settings
│
├── installer/                  # Consent form
├── deploy.sh                  # VPS deployment script
├── setup.py                   # Database setup tool
└── README.md
```

## API Endpoints

### Agent API
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/agent/heartbeat | Agent heartbeat |
| POST | /api/agent/screenshot | Upload screenshot |
| POST | /api/agent/activity | Report activity |
| POST | /api/agent/input-status | Report input status |

### Admin API
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/dashboard-data | Dashboard data |
| GET | /api/alerts | Get alerts |
| POST | /api/alerts/<id>/read | Mark alert read |
| GET | /api/reports/activity/<id> | Activity report |
| GET | /api/reports/summary | Summary report |

## Configuration

### Server Config (config.py)
```python
SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://user:pass@localhost/employee_monitor'
SECRET_KEY = 'your-secret-key'
SCREENSHOT_INTERVAL = 1800  # 30 minutes
IDLE_THRESHOLD = 900        # 15 minutes
```

### Agent Config (config.json)
```json
{
    "server_url": "http://YOUR_VPS_IP:5000",
    "agent_key": "EMPLOYEE_KEY",
    "screenshot_interval": 1800,
    "idle_threshold": 900,
    "activity_check_interval": 60,
    "input_test_interval": 300
}
```

## Email Notifications (Optional)

Set environment variables:
```bash
export SMTP_EMAIL=your-email@gmail.com
export SMTP_PASSWORD=your-app-password
```

## Legal Compliance

This system requires employee consent before monitoring. The consent form includes:
- What is being monitored
- How data is used
- Employee rights
- Digital signature

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Agent can't connect | Check server_url and agent_key |
| Screenshots not uploading | Check disk space and MySQL |
| Dashboard not loading | Verify Flask server is running |
| Port 5000 blocked | Open in firewall: `sudo ufw allow 5000` |

## License

MIT License - Free for personal and commercial use.
