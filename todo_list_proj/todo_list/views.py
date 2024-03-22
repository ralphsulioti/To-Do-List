from django.shortcuts import render, redirect, HttpResponse
from django.contrib.auth import logout
from .models import List, Item, User

# Create your views here.
def home(request):
    return render(request, 'home.html')

def logout_view(request):
    logout(request)
    return redirect("/")


def list_view(request, list_id):
    list_obj = List.objects.get(pk=list_id)
    list_items = list_obj.item_set.all()  # Accessing related items through the foreign key relationship
    return render(request, 'list.html', {'list_items': list_items})
