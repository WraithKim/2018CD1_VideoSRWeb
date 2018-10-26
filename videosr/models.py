from django.db import models
from django.utils import timezone

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
    # Currently, This file version field is not using since resumable upload didn't calculate md5 hash.
    uploaded_file_version = models.CharField(max_length=255, null=True)
    # This field is real file name. Be aware of that 'uploaded_file.name' is '/path/to/file/uploaded_file_version'
    uploaded_filename = models.CharField(max_length=255)
    progress_status = models.CharField(
        max_length=2,
        choices=STATUS_CODES,
        default=IN_PROGRESS,
    )

    def __str__(self):
        return self.uploaded_filename


class Customer(models.Model):
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    credit = models.PositiveIntegerField()

    def __str__(self):
        return self.user + ',' + self.credit
