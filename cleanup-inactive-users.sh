#!/bin/bash
# Cleanup inactive users via Docker container
cd /home/hruza/tomikuvzpevnikapp
docker-compose exec -T tomikuvzpevnik python manage.py cleanup_inactive_users
