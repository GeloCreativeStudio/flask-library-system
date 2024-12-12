import os
import logging
from datetime import timedelta
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    # Get the base directory of the application
    basedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    
    # Basic Flask Configuration
    FLASK_APP = os.environ.get('FLASK_APP', 'run.py')
    FLASK_ENV = os.environ.get('FLASK_ENV', 'development')
    DEBUG = FLASK_ENV == 'development'
    TESTING = False
    
    # Security
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-replace-in-production')
    WTF_CSRF_SECRET_KEY = os.environ.get('WTF_CSRF_SECRET_KEY', 'csrf-key-replace-in-production')
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///' + os.path.join(basedir, 'app.db'))
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Database Logging Configuration
    SQLALCHEMY_ECHO = os.environ.get('SQLALCHEMY_ECHO', 'True').lower() == 'true'
    SQLALCHEMY_ENGINE_OPTIONS = {
        'echo': SQLALCHEMY_ECHO,
        'echo_pool': DEBUG,
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }
    
    # Custom Database Logging
    SQLALCHEMY_RECORD_QUERIES = DEBUG
    DATABASE_QUERY_TIMEOUT = 0.5  # Log slow queries (>0.5s)
    DB_LOG_LEVEL = os.environ.get('DB_LOG_LEVEL', 'INFO')
    DB_LOG_TO_FILE = os.environ.get('DB_LOG_TO_FILE', 'True').lower() == 'true'
    DB_LOG_FILE = os.path.join(basedir, 'logs', 'database.log')
    
    @staticmethod
    def init_db_logging():
        if not os.path.exists('logs'):
            os.makedirs('logs')
            
        # Set up SQLAlchemy logging
        logging.basicConfig()
        db_logger = logging.getLogger('sqlalchemy')
        db_logger.setLevel(getattr(logging, Config.DB_LOG_LEVEL))
        
        if Config.DB_LOG_TO_FILE:
            handler = logging.FileHandler(Config.DB_LOG_FILE)
            handler.setLevel(getattr(logging, Config.DB_LOG_LEVEL))
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            db_logger.addHandler(handler)
    
    # Session/Cookie Settings
    SESSION_COOKIE_NAME = 'voting_system_session'
    PERMANENT_SESSION_LIFETIME = timedelta(days=1 if DEBUG else 1)
    SESSION_PROTECTION = 'strong'
    SESSION_COOKIE_SECURE = not DEBUG
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    REMEMBER_COOKIE_SECURE = not DEBUG
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_DURATION = timedelta(days=14)
    
    # Admin Account
    ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'admin')
    ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL', 'admin@example.com')
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin123')  # Change in production!
    
    # Email Configuration
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'localhost')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 25))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'False').lower() == 'true'
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@localhost')
    MAIL_MAX_EMAILS = 5
    MAIL_ASCII_ATTACHMENTS = False
    
    # Development Specific
    TEMPLATES_AUTO_RELOAD = DEBUG
    SEND_FILE_MAX_AGE_DEFAULT = 0 if DEBUG else 31536000
    
    # Voting System Specific
    VOTES_PER_USER = int(os.environ.get('VOTES_PER_USER', 1))
    VOTING_ENABLED = os.environ.get('VOTING_ENABLED', 'True').lower() == 'true'
    REGISTRATION_ENABLED = os.environ.get('REGISTRATION_ENABLED', 'True').lower() == 'true'
    
    # Security Headers (relaxed in development)
    SECURITY_HEADERS = {} if DEBUG else {
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'SAMEORIGIN',
        'X-XSS-Protection': '1; mode=block',
        'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';"
    }
