from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect
from django.db import DatabaseError, transaction
from django.db.models import F

from social_django.models import UserSocialAuth
from payment.models import Customer
from .models import UploadedFile
from .utils import upload_file, is_valid_file_request
import urllib.parse, logging, os, pika
from pika.exceptions import AMQPError

logger = logging.getLogger(__name__)

@login_required
def index(request):
    uploaded_files = UploadedFile.objects.filter(owner=request.user)
    return render(request, 'dashboard/index.html', {
        'activate': "dashboard",
        'credit': request.user.customer.credit,
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
    scale_factor = int(request.POST.get('scale_factor'))
    # 동영상 SR처리 비용, 이 계산은 chunk-size-upload.js에도 영향을 미침
    product_price = (size * scale_factor / 1000)
    # 크레딧 감소, 파일 업로드, 업로드된 동영상을 SR모듈에 전달하는 작업 중 하나라도 실패할 시,
    # rollback을 해야 함.
    try:
        with transaction.atomic():
            # 크레딧이 부족하면 업로드를 거부함.
            if request.user.customer.credit < product_price:
                return HttpResponse("크레딧이 부족합니다.", status=400)
            # 만약 이미 업로드 된 파일이 존재하면 업로드를 거부함
            if UploadedFile.objects.filter(owner__pk=request.user.pk).exists():
                return HttpResponse("모든 사용자는 파일 하나만 업로드 가능합니다.", status=400)
            
            # create new UploadedFile
            new_file = upload_file(owner=request.user,
                        name=filename,
                        scale_factor=scale_factor,
                        version=version,
                        path=path,
                        size=size)
            # 만약 업로드된 파일을 찾을 수 없을 때는 서버 에러를 반환
            if new_file is None:
                return HttpResponse(status=500)
                
            new_file_path = settings.MEDIA_ROOT + new_file.uploaded_file.name
            # enqueue this file in message queue
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
        
            Customer.objects.filter(user=request.user).update(credit = F('credit') - product_price)
    
    # 데이터베이스 트랜잭션 에러 또는 pika의 AMQP 에러가 발생시 서버 에러를 반환
    except (DatabaseError, AMQPError) as e:
        logger.error(e)
        return HttpResponse(status=500)
    else:
        return HttpResponse(status=200)

@login_required
def download_file(request, pk):
    file_to_download = get_object_or_404(UploadedFile, pk=pk, owner=request.user)
    (dirname, basename) = os.path.split(file_to_download.uploaded_file.name)
    basename = "sr_" + basename + ".mp4"
    sr_relative_path = os.path.join(dirname, basename)
    if not os.path.isfile(settings.MEDIA_ROOT + sr_relative_path):
        logger.warn("Download file - file not found. pk: {}".format(pk))
        return HttpResponse(status=404)
    response = HttpResponse()
    root,ext = os.path.splitext(file_to_download.uploaded_filename)
    response['Content-Disposition'] = 'attachment; filename={0}'.format(urllib.parse.quote(root + ".mp4"))
    response['X-Accel-Redirect'] = '/media/{0}'.format(sr_relative_path)
    return response

@login_required
def delete_file(request, pk):
    file_to_delete = get_object_or_404(UploadedFile, pk=pk, owner=request.user)
    if file_to_delete.progress_status != UploadedFile.FINISHED:
        return HttpResponse(status=400)
    file_to_delete.delete()
    return redirect('dashboard:index')

### functions in menu "dashboard" end ###

@login_required
def user_settings(request):
    return render(request, 'dashboard/settings.html', {
        'activate': "settings",
        'credit': request.user.customer.credit
    })

@login_required
def delete_account(request):
    try:
        with transaction.atomic():
            # 반드시 SocialAuth객체를 먼저 삭제해야 함. 그렇지 않으면 참조 오류 발생.
            # (확인하고 싶으면 관리자 페이지에서 삭제해보셈...)
            UserSocialAuth.objects.filter(user=request.user).delete()
            User.objects.filter(pk=request.user.pk).delete()
    except DatabaseError as de:
        logger.error(de)
        return HttpResponse(status=400)
    else:
        return redirect('login:index')

### functions in menu "settings" end ###
