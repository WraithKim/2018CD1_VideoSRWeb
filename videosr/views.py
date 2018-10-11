from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.http import require_POST

from .models import UploadedFile
from .forms import UploadedFileForm
from .utils import upload_file, is_valid_file_request
import urllib.parse, logging, os

logger = logging.getLogger(__name__)

# Create your views here.
def index(request):
    return render(request, 'videosr/index.html', {})

@require_POST
def upload_complete(request):
    if is_valid_file_request(request.POST):
        path = request.POST.get('uploaded_file.path')
        size = request.POST.get('uploaded_file.size')
        filename = request.POST.get('uploaded_file.name')

        # maybe authentication here

        upload_file(name=filename, path=path, size=size)
        # TODO: research for redirect that out of order.
        return redirect('download_test')
    # if validation failed, remove uploaded file
    path = request.POST.get('uploaded_file.path')
    if path and os.path.isfile(path):
        os.remove(path)
    return redirect('upload_test')

def upload_test(request):
    return render(request, 'videosr/upload_test.html', {})

def download_test(request):
    uploaded_files = UploadedFile.objects.all()
    return render(request, 'videosr/download_test.html', { 'files' : uploaded_files })

def download_file(request, pk):
    file_to_download = get_object_or_404(UploadedFile, pk=pk)
    response = HttpResponse()
    response['Content-Disposition'] = 'attachment; filename={0}'.format(urllib.parse.quote(file_to_download.uploaded_filename))
    response['X-Accel-Redirect'] = '/media/{0}'.format(file_to_download.uploaded_file.name)
    return response

def delete_file(request, pk):
    file_to_delete = get_object_or_404(UploadedFile, pk=pk)
    file_to_delete.delete()
    return redirect('download_test')

