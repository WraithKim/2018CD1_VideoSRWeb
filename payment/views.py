from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.db import DatabaseError, transaction
from django.db.models import F
from .models import Customer, Order
import logging, json, requests, datetime, uuid

logger = logging.getLogger(__name__)

##### request handling function #######
@login_required
def index(request):
    # activate는 왼쪽 네비게이션바에서 class="active"라는 css속성을 넣어줄 메뉴를 가리킴
    # credit정보는 오른쪽위에 프로필정보에 뜨기 때문에 전달해줘야 함.
    return render(request, 'payment/index.html', {
        "activate": "payment",
        "credit": request.user.customer.credit
    })

@login_required
def payment_request(request, amount):
    url = "https://pay.toss.im/api/v1/payments"
    orderNo = str(uuid.uuid4())
    amount = str(amount)
    params = {
        "orderNo": orderNo,
        "amount": amount,
        "amountTaxFree": 0,
        "productDesc":"테스트 결제",
        "apiKey": "sk_test_apikey1234567890",
        "resultCallback": "https://myshop.com/toss/result.php",
        "retUrl": "https://videosr.koreacentral.cloudapp.azure.com"
        + reverse('payment:payment_success', kwargs={'amount': amount}),
        "cashRecipt": False
    }

    r = requests.post(url, data=params)
    d = json.loads(r.text)
    if d['code'] == 0:
        # 디비에 값 업데이트
        Order.objects.create(payToken=d['payToken'],orderNo=orderNo)
        return HttpResponseRedirect(d['checkoutPage'])
    else:
        return redirect('payment:payment_fail')

@login_required
def payment_success(request, amount):

    # orderNo로 payToken가져와서 check
    orderNo = request.GET['orderNo']
    payToken = get_object_or_404(Order, orderNo=orderNo).payToken
    # 결제를 제대로 시도하지 않았을 때
    if "PAY_APPROVED" != payment_check(payToken):
        return redirect('payment:payment_fail')
        
    # DB에 amount에 해당하는 값 만큼 update
    try:
        Customer.objects.filter(user=request.user).update(credit = F('credit') + int(amount))
        pay_complete(payToken,orderNo,amount)
    except DatabaseError as de:
        logger.error(de)
        return redirect('payment:payment_fail')
    else:
        return render(request, 'payment/payment_success.html', {
            "activate": "payment",
            "credit": request.user.customer.credit
        })

@login_required
def payment_fail(request):
    return render(request, 'payment/payment_fail.html', {
        "activate": "payment",
        "credit": request.user.customer.credit
    })
    
##### request-handling function end #######
###### non-request-handling function ######
def payment_check(token):
    url = "https://pay.toss.im/api/v1/status"
    params = {
        "payToken": token,
        "apiKey": "sk_test_apikey1234567890",
    }
    r = requests.post(url, data=params)
    d = json.loads(r.text)
    if d['code'] == 0:
        return d['payStatus']
    else:
        return None

def pay_complete(payToken,orderNo,amount):
    url = "https://pay.toss.im/api/v1/execute"
    params = {
        "payToken": payToken,
        "orderNo" : orderNo,
        "apiKey": "sk_test_apikey1234567890",
        "amount": amount
    }
    r = requests.post(url, data=params)
    
###### non-request-handling function end #######
