from .models import UploadedFile
from django.conf import settings
import os, shutil, logging, uuid
import subprocess

logger = logging.getLogger(__name__)

def move_upload_to_storage(source, dst):
    """move uploaded file from nginx module to the storage
    
    Arguments:
        source {str} -- the source file path in nginx module
        dst {str} -- this will be a new path of source after moving to storage. this is must be relevent to MEDIA_ROOT

    Returns:
        str -- the path of source after moving to the storage
    """

    new_path = settings.MEDIA_ROOT + dst
    shutil.move(source, new_path)
    return new_path

def upload_file(owner, name, path, scale_factor, version, size):
    """save uploaded file as UploadedFile Model and move to storage.

    Arguments:
        owner {auth.User} -- file owner
        name {str} -- the name of file from request object
        path {str} -- the path to the file uploaded (in nginx module)
        scale_factor {int} -- the scale factor of SR
        version {str} -- the md5 sum of the file
        size {str} -- the file size.
    
    Returns:
        UploadedFile -- UploadedFile object about uploaded file.
    """
    if os.path.exists(path):
        # 같은 파일에 대해 겹치는 것을 방지하기 위해 uuid로 변환함.
        new_name = os.path.join('uploads', str(owner.pk), str(uuid.uuid4()))
        move_upload_to_storage(path, new_name)
        new_file = UploadedFile.objects.create(owner = owner,
                                               uploaded_file=new_name,
                                               scale_factor=scale_factor,
                                               uploaded_file_size=size,
                                               uploaded_file_version=version,
                                               uploaded_filename=name)
        return new_file
    else:
        return None

def is_valid_file_request(request_post):
    """validate file upload request from nginx
    
    Arguments:
        request_post {HttpRequest.POST} -- POST attributes of file upload request from nginx
    """
    try:
        path = request_post.get('uploaded_file.path')
        size = request_post.get('uploaded_file.size')
        filename = request_post.get('uploaded_file.name')      
        version = request_post.get('uploaded_file.md5')
        scale_factor = request_post.get('scale_factor')

        if not all([path, size, filename, version, scale_factor]):
            return False
        if scale_factor != "2" and scale_factor != "4":
            return False
        if not os.path.isfile(path):
            return False
        if len(filename) > 255:
            return False
        # check video format
        #FIXME: 테스트용으로 해상도제한을 해제함.(성능측정을 위해 subprocess는 남겨둠.)
        video_resolution = subprocess.check_output(
            ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=coded_width,coded_height", "-of", "csv=e=none:p=0", path], universal_newlines=True).split(",")
        #if int(video_resolution[0]) > 858 or int(video_resolution[1]) > 480:
            #logger.error("The resolution of file {} is too large. ({}, {})".format(path, video_resolution[0], video_resolution[1]))
            #return False
    except KeyError:
        return False
    except subprocess.CalledProcessError as e:
        logger.error(e)
        return False
    else:
        return True
    
