from .models import Customer
from django.conf import settings
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
import os, logging

logger = logging.getLogger(__name__)
@receiver(post_save, sender=User, dispatch_uid='create_user_signal')
def create_additional_user_info(sender, instance, created, **kwargs):
    """create customer model and user directory when user is created
    """
    if created:
        Customer.objects.create(user=instance)
        os.mkdir(os.path.join(settings.MEDIA_ROOT, "uploads", str(instance.pk)))
        logger.info("Create Customer and user directory - id: {}".format(instance.pk))