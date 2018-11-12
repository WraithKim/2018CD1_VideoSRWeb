from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect
from django.db import DatabaseError, transaction

from social_django.models import UserSocialAuth
from payment.models import Customer
from .models import UploadedFile
from .utils import upload_file, is_valid_file_request
import urllib.parse, logging, os, pika

logger = logging.getLogger(__name__)

@login_required
def index(request):
    customer = Customer.objects.get(user=request.user)
    uploaded_files = UploadedFile.objects.filter(owner=request.user)
    return render(request, 'dashboard/index.html', {
        'activate': "dashboard",
        'credit': customer.credit,
        'files': uploaded_files
    })

@require_POST
def upload_complete(request):
    # Use raw logged-in user access, because @login_required only redirect setting.LOGIN_URL
    # We need to send http error status code to JS upload module.
    if not request.user.is_authenticated:
        return HttpResponse(status=401)
    if not is_valid_file_request(request.POST):
        # if validation failed, remove uploaded file
        return HttpResponse(status=400)

    path = request.POST.get('uploaded_file.path')
    size = int(request.POST.get('uploaded_file.size'))
    # Filename is encoded to url when jQuery-File-Upload send the file.
    filename = urllib.parse.unquote(request.POST.get('uploaded_file.name'))
    version = request.POST.get('uploaded_file.md5')
    # FIXME: 테스트용으로 scale_factor를 2배로만 설정함.
    scale_factor = 2
    #scale_factor = int(request.POST.get('scale_factor'))
    
    try:
        with transaction.atomic():
            customer = Customer.objects.get(user=request.user)
            product_price = (size * scale_factor / 1000)
            if customer.credit < product_price:
                return HttpResponse("크레딧이 부족합니다.", status=400)
            if UploadedFile.objects.filter(owner__pk=request.user.pk).exists():
                # alreay file uploaded. reject.
                return HttpResponse("모든 사용자는 파일 하나만 업로드 가능합니다.", status=400)
            customer.credit -= product_price 
            customer.save()
            # create new UploadedFile
            new_file = upload_file(owner=request.user,
                        name=filename,
                        scale_factor=scale_factor,
                        version=version,
                        path=path,
                        size=size)
    except DatabaseError as de:
        logger.error(de)
        return HttpResponse(status=500)
    else:
        if new_file is not None:
            new_file_path = settings.MEDIA_ROOT + new_file.uploaded_file.name
            # enqueue this file in message queue
            # FIXME: 큐 전송 부분에도 예외처리는 필요함.
            message_body = "{} {} {} {}".format(
                new_file.pk,
                new_file_path,
                os.path.dirname(new_file_path) + os.sep,
                scale_factor)
            connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
            channel = connection.channel()
            channel.queue_declare(queue='sr_queue', durable=True)
            channel.basic_publish(exchange='',
                            routing_key='sr_queue',
                            body=message_body,
                            properties=pika.BasicProperties(
                                delivery_mode = 2, # make message persistent
                                content_type = 'text/plain',
                                content_encoding='utf-8',
                            ))
            logger.debug("Send MQ: '{}'".format(message_body))
            connection.close()
        return HttpResponse(status=200)

@login_required
def download_file(request, pk):
    file_to_download = get_object_or_404(UploadedFile, pk=pk, owner=request.user)
    (dirname, basename) = os.path.split(file_to_download.uploaded_file.name)
    basename = "sr_" + basename
    if not os.path.exists(settings.MEDIA_ROOT+dirname + basename):
        return HttpResponse(status=404)
    response = HttpResponse()
    response['Content-Disposition'] = 'attachment; filename={0}'.format(urllib.parse.quote(file_to_download.uploaded_filename))
    response['X-Accel-Redirect'] = '/media/{0}'.format(dirname + basename)
    return response

@login_required
def delete_file(request, pk):
    file_to_delete = get_object_or_404(UploadedFile, pk=pk, owner=request.user)
    if file_to_delete.progress_status != UploadedFile.FINISHED:
        return HttpResponse(status=400)
    file_to_delete.delete()
    return redirect('dashboard:index')

### dashboard:index end ###

@login_required
def user_settings(request):
    return render(request, 'dashboard/settings.html', {
        'activate': "settings"
    })

@login_required
def delete_account(request):
    try:
        with transaction.atomic():
            # 반드시 SocialAuth객체를 먼저 삭제해야 함. 그렇지 않으면 참조 오류 발생.
            # (확인하고 싶으면 관리자 페이지에서 삭제해보셈...)
            UserSocialAuth.objects.filter(user=request.user).delete()
            User.objects.filter(pk=request.user.pk).delete()
            return redirect('login:index')
    except DatabaseError as de:
        logger.error(de)
        return HttpResponse(status=400)

### dashboard:user_settings end ###
