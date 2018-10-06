from .models import UploadedFile
from django.conf import settings
import os, shutil

# move uploaded file from nginx module to storage
# 
# =======parameters========
# source: the source file path in nginx module
# dst: this will be a new path of source after moving to storage. this is must be relevent to MEDIA_ROOT
def move_upload_to_storage(source, dst):
    new_path = settings.MEDIA_ROOT + dst
    shutil.move(source, new_path)
    return new_path

# save uploaded file as UploadedFile Model and move to storage.
#
# =======parameters========
# path: the path to the file uploaded (in nginx module)
# name: the name of file from request object
# version: the md5 sum of the file
# size: the file size.
def upload_file(name, version, path, size):
    if os.path.exists(path):
        
        new_name = os.path.join('uploads', name)
        move_upload_to_storage(path, new_name)
        new_file = UploadedFile.objects.create(uploaded_file=new_name,
                                               uploaded_file_size=size,
                                               uploaded_file_version=version)
        new_file.save()
        return new_file
