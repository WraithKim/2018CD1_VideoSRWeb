from dashboard.models import UploadedFile
from django.conf import settings
from django.db.models.signals import pre_delete
from django.dispatch import receiver
import os, logging

logger = logging.getLogger(__name__)

@receiver(pre_delete, sender=UploadedFile, dispatch_uid='uploadedfile_delete_signal')
def delete_uploaded_file(sender, instance, *args, **kwargs):
    """delete the file from filesystem
    """
    path = instance.uploaded_file.path
    (dirname, basename) = os.path.split(path)
    sr_path = os.path.join(dirname, "sr_" + basename + ".mp4")
    if os.path.isfile(sr_path):
        logger.info("Delete SR video - id: {} path: {}".format(instance.pk, sr_path))
        os.remove(sr_path)
    if os.path.isfile(path):
        logger.info("Delete Original video - id: {} path: {}".format(instance.pk, path))
        os.remove(path)
