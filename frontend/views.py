from django.shortcuts import render

def custom_404(request, exception):
    return render(request, '404.html', status=404)
def stats(request):
    return render(request, 'stats.html')
def custom_500(request):
    return render(request, '500.html', status=500)