from django.shortcuts import render, redirect

def index(request):
    if request.user.is_authenticated:
        return redirect('dashboard:index')
    else:
        return render(request, 'login/index.html')