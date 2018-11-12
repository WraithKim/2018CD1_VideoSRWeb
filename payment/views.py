from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect
from django.db import DatabaseError, transaction
from .models import Customer
import logging, random, json, requests, datetime

logger = logging.getLogger(__name__)

@login_required
def index(request):
    return render(request, 'payment/index.html')
    
@login_required
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
            # TODO: User에서 Customer를 불러올 수 있나?(user.customer)
            # curCustomer = Customer.objects.get(user=request.user)
            curCustomer = request.user.customer
            # TODO: 상한선 설정
            curCustomer.credit += int(amount)
            curCustomer.save()
    except DatabaseError as e:
        logger.error(e)
        return redirect('test:payment_fail')
    else:
        return render(request, 'payment/payment_success.html', {'credit' : curCustomer.credit})

@login_required
def payment_fail(request):
    return render(request, 'payment/payment_fail.html')
