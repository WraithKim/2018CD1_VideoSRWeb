from .models import UploadedFile
from .models import Customer
from django.conf import settings
from django.contrib.auth.models import User
from django.db.models.signals import pre_delete, post_save
from django.dispatch import receiver
import os, logging

logger = logging.getLogger(__name__)

@receiver(pre_delete, sender=UploadedFile, dispatch_uid='uploadedfile_delete_signal')
def delete_uploaded_file(sender, instance, *args, **kwargs):
    """delete the file from filesystem
    """
    path = instance.uploaded_file.path
    if os.path.isfile(path):
        os.remove(path)

@receiver(post_save, sender=User, dispatch_uid='create_user_signal')
def create_additional_user_info(sender, instance, created, **kwargs):
    """create customer model and user directory when user is created
    """
    if created:
        Customer.objects.create(user=instance)
        os.mkdir(os.path.join(settings.MEDIA_ROOT, "uploads", str(instance.pk)))