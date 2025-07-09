from celery.schedules import crontab

CELERY_BROKER_URL = 'redis://localhost:6379/0'

CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'

INSTALLED_APPS = [
    ...
    'graphene_django',
    'crm', 
    'django_filters'
    'django_celery_beat'
    
]
