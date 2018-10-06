from django.db import models
from django.utils import timezone
import os

# Create your models here.

class UploadedFile(models.Model):
    IN_PROGRESS = 'IP'
    FINISHED = 'FI'
    STATUS_CODES = (
        (IN_PROGRESS, 'In progress'),
        (FINISHED, 'Finished'),
    )

    uploaded_file = models.FileField()
    uploaded_date = models.DateTimeField(auto_now_add=True)
    uploaded_file_size = models.BigIntegerField()
    uploaded_file_version = models.CharField(max_length=255)
    # This field is real file name. Be aware of that 'uploaded_file.name' is '/path/to/file/uploaded_file_version'
    uploaded_filename = models.CharField(max_length=255)
    progress_status = models.CharField(
        max_length=2,
        choices=STATUS_CODES,
        default=IN_PROGRESS,
    )

    def __str__(self):
        return self.uploaded_filename

    # delete the file and make sure to also delete from storage
    def delete(self, delete_file=True, *args, **kwargs):
        if self.uploaded_file:
            storage, path = self.uploaded_file.storage, self.uploaded_file.path
        super(UploadedFile, self).delete(*args, **kwargs)
        if self.uploaded_file and delete_file:
            storage.delete(path)