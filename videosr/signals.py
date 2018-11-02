from .models import UploadedFile
from .models import Customer
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
def create_customer_model(sender, instance, created, **kwargs):
    """create customer model when user is created
    """
    if created:
        Customer.objects.create(user=instance)
