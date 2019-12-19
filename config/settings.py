from datetime import timedelta
import os

from datetime import timedelta
from distutils.util import strtobool

from celery.schedules import crontab


LOG_LEVEL = os.getenv('LOG_LEVEL', 'DEBUG')

SECRET_KEY = os.getenv('SECRET_KEY', None)

SERVER_NAME = os.getenv('SERVER_NAME',
                        'localhost:{0}'.format(os.getenv('DOCKER_WEB_PORT',
                                                         '8000')))

# SQLAlchemy.
pg_user = os.getenv('POSTGRES_USER', 'turboquant')
pg_pass = os.getenv('POSTGRES_PASSWORD', 'password')
pg_host = os.getenv('POSTGRES_HOST', 'postgres')
pg_port = os.getenv('POSTGRES_PORT', '5432')
pg_db = os.getenv('POSTGRES_DB', pg_user)
db = 'postgresql://{0}:{1}@{2}:{3}/{4}'.format(pg_user, pg_pass,
                                               pg_host, pg_port, pg_db)
SQLALCHEMY_DATABASE_URI = db
SQLALCHEMY_TRACK_MODIFICATIONS = False

# Celery.
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://redis:6379/0')
CELERY_RESULT_BACKEND = CELERY_BROKER_URL
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_REDIS_MAX_CONNECTIONS = 5
CELERYBEAT_SCHEDULE = {
    'mark-soon-to-expire-credit-cards': {
        'task': 'turboquant.blueprints.billing.tasks.mark_old_credit_cards',
        'schedule': crontab(hour=0, minute=0)
    },
    'expire-old-coupons': {
        'task': 'turboquant.blueprints.billing.tasks.expire_old_coupons',
        'schedule': crontab(hour=0, minute=1)
    },
}

# Flask-Mail.
MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
MAIL_PORT = os.getenv('MAIL_PORT', 587)
MAIL_USE_TLS = bool(strtobool(os.getenv('MAIL_USE_TLS', 'true')))
MAIL_USE_SSL = bool(strtobool(os.getenv('MAIL_USE_SSL', 'false')))
MAIL_USERNAME = os.getenv('MAIL_USERNAME', None)
MAIL_PASSWORD = os.getenv('MAIL_PASSWORD', None)
MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER', 'smtp.gmail.com')

# Flask-Babel.
LANGUAGES = {
    'en': 'English',
    'kl': 'Klingon',
    'es': 'Spanish'
}
BABEL_DEFAULT_LOCALE = 'en'

# User.
SEED_ADMIN_EMAIL = os.getenv('SEED_ADMIN_EMAIL', 'dev@local.host')
SEED_ADMIN_PASSWORD = os.getenv('SEED_ADMIN_PASSWORD', 'password')
REMEMBER_COOKIE_DURATION = timedelta(days=90)

# Billing.
STRIPE_PUBLISHABLE_KEY = os.getenv('STRIPE_PUBLISHABLE_KEY', None)
STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY', None)
STRIPE_API_VERSION = '2018-02-28'
STRIPE_CURRENCY = 'usd'
STRIPE_PLANS = {
    '0': {
        'id': 'bronze',
        'name': 'Bronze',
        'amount': 100,
        'currency': STRIPE_CURRENCY,
        'interval': 'month',
        'interval_count': 1,
        'trial_period_days': 14,
        'statement_descriptor': 'TURBOQUANT BRONZE',
        'metadata': {
            'coins': 110
        }
    },
    '1': {
        'id': 'gold',
        'name': 'Gold',
        'amount': 500,
        'currency': STRIPE_CURRENCY,
        'interval': 'month',
        'interval_count': 1,
        'trial_period_days': 14,
        'statement_descriptor': 'TURBOQUANT GOLD',
        'metadata': {
            'coins': 600,
            'recommended': True
        }
    },
    '2': {
        'id': 'platinum',
        'name': 'Platinum',
        'amount': 1000,
        'currency': STRIPE_CURRENCY,
        'interval': 'month',
        'interval_count': 1,
        'trial_period_days': 14,
        'statement_descriptor': 'TURBOQUANT PLATINUM',
        'metadata': {
            'coins': 1500
        }
    }
}

COIN_BUNDLES = [
    {'coins': 100, 'price_in_cents': 100, 'label': '100 for $1'},
    {'coins': 1000, 'price_in_cents': 900, 'label': '1,000 for $9'},
    {'coins': 5000, 'price_in_cents': 4000, 'label': '5,000 for $40'},
    {'coins': 10000, 'price_in_cents': 7000, 'label': '10,000 for $70'},
]

# Bet.
DICE_ROLL_PAYOUT = {
    '2': 36.0,
    '3': 18.0,
    '4': 12.0,
    '5': 9.0,
    '6': 7.2,
    '7': 6.0,
    '8': 7.2,
    '9': 9.0,
    '10': 12.0,
    '11': 18.0,
    '12': 36.0
}

# Rate limiting.
RATELIMIT_STORAGE_URL = CELERY_BROKER_URL
RATELIMIT_STRATEGY = 'fixed-window-elastic-expiry'
RATELIMIT_HEADERS_ENABLED = True

# Google Analytics.
ANALYTICS_GOOGLE_UA = os.getenv('ANALYTICS_GOOGLE_UA', None)

