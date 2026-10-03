import os

basedir = os.path.abspath(os.path.dirname(__file__))

class BaseConfig:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'noise-ecommerce-secret-key-2026')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Ranking Engine Integration
    RANKING_ENGINE_URL = os.environ.get('RANKING_ENGINE_URL', 'http://localhost:5000')
    RANKING_COMPANY_ID = int(os.environ.get('RANKING_COMPANY_ID', '1'))
    
    # Storefront settings
    PORT = int(os.environ.get('PORT', '8000'))
    CURRENCY_SYMBOL = "₹"
    FREE_SHIPPING_THRESHOLD = 999.0
    SHIPPING_FEE = 99.0
    GST_PERCENT = 18.0

class DevelopmentConfig(BaseConfig):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'instance', 'noise_ecommerce.db')

class TestingConfig(BaseConfig):
    TESTING = True
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL') or 'sqlite:///:memory:'
    RANKING_ENGINE_URL = os.environ.get('RANKING_ENGINE_URL', 'http://localhost:5000')
    RANKING_COMPANY_ID = int(os.environ.get('RANKING_COMPANY_ID', '1'))

class ProductionConfig(BaseConfig):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'instance', 'noise_ecommerce.db')

config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
