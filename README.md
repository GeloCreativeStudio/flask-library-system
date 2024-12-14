# 📚 Flask Library System

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Flask 2.3.3](https://img.shields.io/badge/flask-2.3.3-green.svg)](https://flask.palletsprojects.com/)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0.23-orange.svg)](https://www.sqlalchemy.org/)
[![MIT License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

A modern web-based library management system built with Flask. This system helps librarians and users manage books, track borrowings, and handle library operations efficiently.

## 🌟 Features

### For Librarians (Admin)
- **Book Management**
  - Add, edit, and remove books from the catalog
  - Track book quantities and availability
  - Manage book categories
  - Upload book cover images
  - Generate unique local IDs for books
  - Track book locations (shelf/section)

- **User Management**
  - View and manage library members
  - Track borrowing history
  - Handle overdue books and fines

### For Library Members
- **Book Browsing**
  - Browse books by category
  - View book details and availability
  - Check borrowing history

- **Account Management**
  - Personal dashboard
  - View borrowed books
  - Track due dates
  - View fine calculations

### System Features
- **Authentication System**
  - Secure login for admins and users
  - Password hashing
  - Session management

- **Automated Processing**
  - Automatic fine calculation
  - Due date tracking
  - Book availability updates
  - Local ID generation for books

## 🚀 Quick Start

### Prerequisites

| Software | Version | Description | Installation Guide |
|----------|---------|-------------|-------------------|
| Python   | 3.8+    | Core runtime environment | [Python Downloads](https://www.python.org/downloads/) |
| pip      | Latest  | Package installer | Included with Python |
| Git      | Latest  | Version control | [Git Downloads](https://git-scm.com/downloads) |

> **Note**: When installing Python on Windows, check "Add Python to PATH" in the installer

### Detailed Setup Guide

1. **Clone the Repository**
```bash
git clone https://github.com/GeloCreativeStudio/flask-library-system.git
cd flask-library-system
```

2. **Set up Virtual Environment**
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Unix/MacOS:
source venv/bin/activate
```

3. **Install Dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure Environment Variables**
```bash
# Copy example environment file
cp .env.example .env
```

Edit `.env` with your settings:
```ini
# Flask Configuration
FLASK_APP=run.py
FLASK_ENV=development    # Use 'production' in production
DEBUG=True              # Set to False in production

# Security
SECRET_KEY=your-secure-secret-key-here

# Database
DATABASE_URL=sqlite:///instance/app.db

# Admin Account
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123

# Email Configuration (Optional)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-specific-password
```

5. **Initialize the Database**
```bash
# Initialize migrations directory
flask db init

# Create initial migration
flask db migrate -m "Initial migration"

# Apply the migration
flask db upgrade
```

6. **Run the Application**
```bash
flask run
```

The application will be available at `http://127.0.0.1:5000`

### Default Admin Credentials
```
Username: admin
Password: admin123
```
> ⚠️ **Important**: Change these credentials immediately after first login for security!

## 🔍 Troubleshooting

### Common Issues and Solutions

1. **ModuleNotFoundError: No module named 'flask_login'**
   ```bash
   pip install flask-login
   ```

2. **Database Migration Issues**
   ```bash
   # Remove existing migrations
   rm -rf migrations/
   
   # Reinitialize migrations
   flask db init
   flask db migrate
   flask db upgrade
   ```

3. **Port Already in Use**
   ```bash
   # Windows:
   netstat -ano | findstr :5000
   taskkill /PID <PID> /F
   ```

## 🧪 Testing

### Manual Testing Steps
1. Access the application at `http://127.0.0.1:5000`
2. Log in with admin credentials
3. Test core functionalities:
   - Add a new book
   - Register a new user
   - Process a book borrowing
   - Check due dates and fines

### Automated Testing
```bash
python -m pytest tests/
```

## 📦 Project Structure
```
flask-library-system/
├── app/
│   ├── __init__.py
│   ├── models/
│   ├── routes/
│   ├── static/
│   └── templates/
├── migrations/
├── instance/
├── tests/
├── .env
├── .env.example
├── .gitignore
├── requirements.txt
└── run.py
```

## 🔐 Security Considerations
- Change default admin credentials immediately
- Use strong passwords
- Keep SECRET_KEY secure and unique
- Update dependencies regularly
- Use HTTPS in production
- Implement rate limiting
- Enable CSRF protection

## 🤝 Contributing
1. Fork the repository from [GeloCreativeStudio/flask-library-system](https://github.com/GeloCreativeStudio/flask-library-system)
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## 📄 License

[MIT License](LICENSE) - Feel free to use this project for your own purposes.

---
<p align="center">Made with ❤️ by <a href="https://github.com/GeloCreativeStudio">GeloCreativeStudio</a></p>