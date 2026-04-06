from datetime import timedelta
from logging import getLogger

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone

logger = getLogger(__name__)

class Command(BaseCommand):
    help = "Delete inactive users older than 1 hour"

    def handle(self, *args, **options):
        cutoff = timezone.now() - timedelta(hours=1)
        deleted, _ = User.objects.filter(is_active=False, date_joined__lt=cutoff).delete()
        logger.info("Deleted %d inactive users", deleted)
