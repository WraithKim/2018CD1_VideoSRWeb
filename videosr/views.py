from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect
from django.db import DatabaseError, transaction

from social_django.models import UserSocialAuth
from .models import UploadedFile, Customer
from .forms import UploadedFileForm
from .utils import upload_file, is_valid_file_request
import urllib.parse, logging, os
import random, json, requests, pika, datetime

logger = logging.getLogger(__name__)

# Create your views here.
def index(request):
    return render(request, 'videosr/index.html', {})

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
    size = request.POST.get('uploaded_file.size')
    # Filename is encoded to url when jQuery-File-Upload send the file.
    filename = urllib.parse.unquote(request.POST.get('uploaded_file.name'))
    version = request.POST.get('uploaded_file.md5')
    scale_factor = int(request.POST.get('scale_factor'))
    
    try:
        with transaction.atomic():
            if UploadedFile.objects.filter(owner__pk=request.user.pk).exists():
                # alreay file uploaded. reject.
                return HttpResponse("All user can upload only one video.", status=400)
            else:
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
        return HttpResponse("Upload complete", status=200)

def upload_test(request):
    return render(request, 'videosr/upload_test.html')

@login_required
def download_test(request):
    uploaded_files = UploadedFile.objects.filter(owner=request.user)
    return render(request, 'videosr/download_test.html', { 'files' : uploaded_files })

@login_required
def download_file(request, pk):
    file_to_download = get_object_or_404(UploadedFile, pk=pk, owner=request.user)
    response = HttpResponse()
    response['Content-Disposition'] = 'attachment; filename={0}'.format(urllib.parse.quote(file_to_download.uploaded_filename))
    response['X-Accel-Redirect'] = '/media/{0}'.format(file_to_download.uploaded_file.name)
    return response

@login_required
def delete_file(request, pk):
    file_to_delete = get_object_or_404(UploadedFile, pk=pk, owner=request.user)
    file_to_delete.delete()
    return redirect('test:download_test')

def login_test(request):
    logined_user_credit = None
    try:
        logined_user_credit = Customer.objects.get(user=request.user).credit
    except Customer.DoesNotExist:
        # if user's credit doesn't exist, render login test page with logined_user_credit = None
        pass
    finally:
        return render(request, 'videosr/login_test.html', {'logined_user_credit': logined_user_credit})

def delete_account(request):
    # TODO: objects.filter가 찾지 못했을 때, 예외처리
    UserSocialAuth.objects.filter(user=request.user).delete()
    User.objects.filter(pk=request.user.pk).delete()
    return redirect('test:login_test')

def payment_test(request):
    return render(request, 'videosr/payment_test.html')

def payment_request(request, amount):
    url = "https://pay.toss.im/api/v1/payments"
    params = {
        "orderNo": random.random(),
        #"orderNo": "2015072012411",
        "amount": amount,
        "amountTaxFree": 0,
        "productDesc":"테스트 결제",
        "apiKey": "sk_test_apikey1234567890",
        "expiredTime":"2015-07-20 16:21:00",
        "resultCallback": "https://myshop.com/toss/result.php",
        "retUrl": "https://videosr.koreacentral.cloudapp.azure.com/payment/"+ amount + "/success/",
        "retCancelUrl": "https://videosr.koreacentral.cloudapp.azure.com/payment/fail/",
        "cashRecipt": False
    }

    r = requests.post(url, data=params)
    d = json.loads(r.text)

    return HttpResponseRedirect(d['checkoutPage'])

@login_required
def payment_success(request, amount):

    # DB에 amount에 해당하는 값 만큼 update
    try:
        with transaction.atomic():
            curCustomer = Customer.objects.get(user=request.user)
            curCustomer.credit += int(amount)
            curCustomer.save()
    except DatabaseError as e:
        logger.error(e)
        return redirect('test:payment_fail')
    else:
        return render(request, 'videosr/payment_success.html', {'credit' : curCustomer.credit})

def mq_test(request):
    return render(request, 'videosr/mq_test.html')

def mq_send(request):
    nowtime = datetime.datetime.now()
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()
    channel.queue_declare(queue='task_queue', durable=True)
    channel.basic_publish(exchange='',
                    routing_key='task_queue',
                    body='{}'.format(str(nowtime),
                    properties=pika.BasicProperties(
                         delivery_mode = 2, # make message persistent
                    ))
    )
    logger.debug("[x] Sent '{}'".format(str(nowtime)))
    connection.close()

def payment_fail(request):
    return render(request, 'videosr/payment_fail.html')
