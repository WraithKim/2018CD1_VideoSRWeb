from django.shortcuts import render, redirect

def index(request):
    if request.user.is_authenticated:
        return render(request, 'login/index.html')
    else:
        return render(request, 'login/index.html')