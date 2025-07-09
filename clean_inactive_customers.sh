#!/bin/bash

# Set the timestamp for logging
timestamp=$(date "+%Y-%m-%d %H:%M:%S")

# Run the Django shell command to delete inactive customers and count them
deleted_count=$(python manage.py shell << END
from datetime import timedelta
from django.utils import timezone
from crm.models import Customer  # adjust if your model is elsewhere

cutoff = timezone.now() - timedelta(days=365)
inactive_customers = Customer.objects.filter(orders__isnull=True, created_at__lt=cutoff)
count = inactive_customers.count()
inactive_customers.delete()
print(count)
END
)

# Log the result with timestamp
echo "$timestamp - Deleted $deleted_count inactive customers" >> /tmp/customer_cleanup_log.txt

# Run this command to make it executable
chmod +x crm/cron_jobs/clean_inactive_customers.sh
