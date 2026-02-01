import os
from datetime import timedelta
from dotenv import load_dotenv

# بارگذاری متغیرهای محیطی از فایل .env
load_dotenv()


class Config:
    """کلاس پایه پیکربندی - تنظیمات مشترک بین همه محیط‌ها"""
    
    # Flask Core Configuration
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-please-change')
    FLASK_APP = os.getenv('FLASK_APP', 'app.py')
    
    # Database Configuration
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URI', 
        'sqlite:///instance/voting.db'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False
    
    # Upload Configuration
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'uploads')
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_CONTENT_LENGTH', 5242880))  # 5MB
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    
    # Session Configuration
    SESSION_COOKIE_SECURE = os.getenv('SESSION_COOKIE_SECURE', 'False') == 'True'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = timedelta(
        seconds=int(os.getenv('PERMANENT_SESSION_LIFETIME', 3600))
    )
    
    # Blockchain Configuration
    BLOCKCHAIN_DIFFICULTY = int(os.getenv('BLOCKCHAIN_DIFFICULTY', 4))
    BLOCKCHAIN_REWARD = int(os.getenv('BLOCKCHAIN_REWARD', 1))
    
    # Admin Default Credentials
    ADMIN_NATIONAL_ID = os.getenv('ADMIN_NATIONAL_ID', '0000000000')
    ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'admin123')
    ADMIN_NAME = os.getenv('ADMIN_NAME', 'مدیر سیستم')
    ADMIN_EMAIL = os.getenv('ADMIN_EMAIL', 'admin@entekhablock.ir')
    
    # Application Settings
    APP_NAME = os.getenv('APP_NAME', 'انتخاب‌بلاک')
    APP_VERSION = os.getenv('APP_VERSION', '1.0.0')
    TIMEZONE = os.getenv('TIMEZONE', 'Asia/Tehran')
    LANGUAGE = os.getenv('LANGUAGE', 'fa')
    
    # Security Headers
    CONTENT_SECURITY_POLICY = os.getenv(
        'CONTENT_SECURITY_POLICY',
        "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'"
    )
    X_FRAME_OPTIONS = 'DENY'
    X_CONTENT_TYPE_OPTIONS = 'nosniff'
    
    # Logging Configuration
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'logs/app.log')
    LOG_MAX_BYTES = int(os.getenv('LOG_MAX_BYTES', 10485760))  # 10MB
    LOG_BACKUP_COUNT = int(os.getenv('LOG_BACKUP_COUNT', 5))
    
    # Email Configuration (Optional)
    MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.getenv('MAIL_PORT', 587))
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'True') == 'True'
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER', 'noreply@entekhablock.ir')
    
    # Rate Limiting Configuration (Optional)
    RATELIMIT_ENABLED = os.getenv('RATELIMIT_ENABLED', 'True') == 'True'
    RATELIMIT_DEFAULT = os.getenv('RATELIMIT_DEFAULT', '100 per hour')
    RATELIMIT_STORAGE_URL = os.getenv('RATELIMIT_STORAGE_URL', 'memory://')
    
    @staticmethod
    def init_app(app):
        """مقداردهی اولیه برنامه"""
        pass


class DevelopmentConfig(Config):
    """پیکربندی محیط توسعه (Development)"""
    
    DEBUG = True
    TESTING = False
    SQLALCHEMY_ECHO = True  # نمایش کوئری‌های SQL در کنسول
    
    @classmethod
    def init_app(cls, app):
        Config.init_app(app)
        
        # لاگ گذاری با جزئیات بیشتر
        import logging
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )


class ProductionConfig(Config):
    """پیکربندی محیط تولید (Production)"""
    
    DEBUG = False
    TESTING = False
    
    # امنیت بالاتر در محیط تولید
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    
    # استفاده از دیتابیس واقعی (PostgreSQL توصیه می‌شود)
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URI',
        'postgresql://user:password@localhost/voting_db'
    )
    
    @classmethod
    def init_app(cls, app):
        Config.init_app(app)
        
        # لاگ گذاری فایلی با Rotation
        import logging
        from logging.handlers import RotatingFileHandler
        
        # ایجاد دایرکتوری logs در صورت عدم وجود
        os.makedirs('logs', exist_ok=True)
        
        file_handler = RotatingFileHandler(
            cls.LOG_FILE,
            maxBytes=cls.LOG_MAX_BYTES,
            backupCount=cls.LOG_BACKUP_COUNT,
            encoding='utf-8'
        )
        
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('انتخاب‌بلاک استارت شد')


class TestingConfig(Config):
    """پیکربندی محیط تست (Testing)"""
    
    TESTING = True
    DEBUG = True
    
    # استفاده از دیتابیس In-Memory برای تست‌ها
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    
    # غیرفعال کردن CSRF برای تست‌های ساده‌تر
    WTF_CSRF_ENABLED = False
    
    @classmethod
    def init_app(cls, app):
        Config.init_app(app)


# دیکشنری نگاشت نام محیط به کلاس پیکربندی
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}


def get_config(config_name=None):
    """
    دریافت کلاس پیکربندی بر اساس نام محیط
    
    Args:
        config_name (str): نام محیط ('development', 'production', 'testing')
    
    Returns:
        Config: کلاس پیکربندی مناسب
    """
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')
    
    return config.get(config_name, DevelopmentConfig)
