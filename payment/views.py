from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect
from django.db import DatabaseError, transaction
from .models import Customer, Order
import logging, random, json, requests, datetime, uuid

logger = logging.getLogger(__name__)

@login_required
def index(request):
    return render(request, 'payment/index.html')

@login_required
def payment_request(request, amount):
    url = "https://pay.toss.im/api/v1/payments"
    orderNo = str(uuid.uuid4())
    params = {
        "orderNo": orderNo,
        #"orderNo": "2015072012411",
        "amount": amount,
        "amountTaxFree": 0,
        "productDesc":"테스트 결제",
        "apiKey": "sk_test_apikey1234567890",
        "resultCallback": "https://myshop.com/toss/result.php",
        "retUrl": "https://videosr.koreacentral.cloudapp.azure.com/payment/"+ amount + "/success/",
        "cashRecipt": False
    }

    r = requests.post(url, data=params)
    d = json.loads(r.text)
    if d['code'] == 0:
        # 디비에 값 업데이트
        Order.objects.create(payToken=d['payToken'],orderNo=orderNo)
        return HttpResponseRedirect(d['checkoutPage'])
    else:
        return redirect('test:payment_fail')

def payment_check(token):
    url = "https://pay.toss.im/api/v1/status"
    params = {
        "payToken": token,
        "apiKey": "sk_test_apikey1234567890",
    }
    r = requests.post(url, data=params)
    dict = json.loads(r.text)
    if d['code'] == 0:
        return dict['payStatus']
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

@login_required
def payment_success(request, amount):

    # orderNo로 payToken가져와서 check
    orderNo = request.GET['orderNo']
    #TODO : orderNo가 없을 때 예외처리
    payToken = Order.objects.filter(orderNo=orderNo).fisrt().payToken

    if "PAY_APPROVED" == payment_check(payToken):
        # DB에 amount에 해당하는 값 만큼 update
        try:
            pay_complete(payToken,orderNo,amount)
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
    # 결제를 제대로 시도하지 않았을 때
    else:
        return redirect('test:payment_fail')

@login_required
def payment_fail(request):
    return render(request, 'payment/payment_fail.html')
