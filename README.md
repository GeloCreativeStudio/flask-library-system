# 🗳️ Student Government Voting System

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Flask 2.3.3](https://img.shields.io/badge/flask-2.3.3-green.svg)](https://flask.palletsprojects.com/)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0.23-orange.svg)](https://www.sqlalchemy.org/)
[![MIT License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

A secure and user-friendly web-based voting system built with Flask, specifically designed for Student Government elections in educational institutions. This system streamlines the process of student body elections while ensuring security and transparency.

## Features

- **Secure Student Authentication** - Secure login and registration system for students and administrators
- **Real-time Election Results** - Live vote counting with visual displays for election transparency
- **Administrative Control** - Comprehensive dashboard for faculty to manage elections and monitor voting
- **Student-Friendly Interface** - Modern, responsive design that works on all devices
- **Fair Election Process** - Ensures one vote per student with verification systems

## Quick Start

### Prerequisites

| Software | Version | Description | Installation Guide |
|----------|---------|-------------|-------------------|
| Python   | 3.8+    | Core runtime environment | [Python Downloads](https://www.python.org/downloads/) |
| pip      | Latest  | Package installer (included with Python) | Included with Python |
| Git      | Latest  | Version control | [Git Downloads](https://git-scm.com/downloads) |

> **Note**: When installing Python, check "Add Python to PATH" in the installer

### Setup

1. **Clone and enter project**
```bash
git clone https://github.com/GeloCreativeStudio/flask-voting-system.git
```
```bash
cd flask-voting-system
```

2. **Set up virtual environment**
```bash
python -m venv venv
```

3. **Activate virtual environment**

Windows:
```bash
venv\Scripts\activate
```

Unix/MacOS:
```bash
source venv/bin/activate
```

4. **Install dependencies**
```bash
pip install -r requirements.txt
```

5. **Configure environment**
```bash
cp .env.example .env
```

Edit `.env` with your settings:
```ini
# Required Settings
FLASK_APP=run.py
FLASK_ENV=development    # Use 'production' in production
DEBUG=True              # Set to False in production

# Security (Change these!)
SECRET_KEY=your-secure-secret-key-here
WTF_CSRF_SECRET_KEY=your-secure-csrf-key-here

# Database
DATABASE_URL=sqlite:///instance/app.db

# Admin Account (Change these!)
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your-secure-password
ADMIN_EMAIL=admin@example.com
```

6. **Initialize database**

First time setup:
```bash
flask db init
```
```bash
flask db migrate -m "Initial migration"
```
```bash
flask db upgrade
```

7. **Run the application**
```bash
python run.py
```

Once running, open [http://localhost:5000](http://localhost:5000) in your browser.

### Common Issues

- **Error: No module named 'flask_login'** - Run `pip install flask-login flask-migrate` to install missing dependencies
- **Error: No such command 'db'** - Make sure you've installed `flask-migrate` and activated your virtual environment
- **Database errors** - Check if your `DATABASE_URL` is correct and the specified directory exists
- **Import errors** - Ensure all dependencies are installed with `pip install -r requirements.txt`
- **Environment errors** - Make sure `.env` file exists and contains all required settings

## Security Tips

- Keep `.env` file private and never commit it
- Use strong admin passwords (minimum 12 characters)
- Keep dependencies updated regularly
- Enable HTTPS in production environment
- Regularly backup your database
- Set `DEBUG=False` in production
- Use secure session cookies in production

## License

[MIT License](LICENSE) - Feel free to use this project for your own purposes.

---
<p align="center">Made with ❤️ by <a href="https://github.com/GeloCreativeStudio">GeloCreativeStudio</a></p>