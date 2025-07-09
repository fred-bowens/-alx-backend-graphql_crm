from celery.schedules import crontab

CELERY_BROKER_URL = 'redis://localhost:6379/0'

CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'
CELERY_BEAT_SCHEDULE = {
    'generate-crm-report': {
        'task': 'crm.tasks.generate_crm_report',
        'schedule': crontab(day_of_week='mon', hour=6, minute=0),
    },
}


INSTALLED_APPS = [
    ...
    'graphene_django',
    'crm', 
    'django_filters'
    'django_celery_beat'
    
]
