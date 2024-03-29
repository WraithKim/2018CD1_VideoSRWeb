from django.db import models
from django.utils import timezone

class UploadedFile(models.Model):
    PENDING = 'PE'
    IN_PROGRESS = 'IP'
    FINISHED = 'FI'
    STATUS_CODES = (
        (PENDING, '대기중'),
        (IN_PROGRESS, '처리중'),
        (FINISHED, '처리 완료'),
    )

    SCALE_2 = 2
    SCALE_4 = 4
    SCALE_FACTORS = (
        (SCALE_2, 'x2'),
        (SCALE_4, 'x4')
    )

    owner = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    uploaded_file = models.FileField()
    uploaded_date = models.DateTimeField(auto_now_add=True)
    uploaded_file_size = models.BigIntegerField()
    uploaded_file_version = models.CharField(max_length=255, null=True)
    # This field is real file name. Be aware of that 'uploaded_file.name' is '/path/to/file/uploaded_file_version'
    uploaded_filename = models.CharField(max_length=255)
    scale_factor = models.SmallIntegerField(
        choices=SCALE_FACTORS,
        default=SCALE_2,
    )
    progress_status = models.CharField(
        max_length=2,
        choices=STATUS_CODES,
        default=PENDING,
    )

    def __str__(self):
        return self.uploaded_filename