#!/bin/bash

# Define the crontab content
CRONTAB_CONTENT="0 * * * * root python /app/src/bucket_tool.py >> /var/log/cron.log 2>&1
"

# Write the crontab content to a file
echo -e "$CRONTAB_CONTENT" > /etc/cron.d/delete_files_cron
