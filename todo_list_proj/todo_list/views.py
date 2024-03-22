from django.shortcuts import render, redirect, HttpResponse, get_object_or_404
from django.contrib.auth import logout
from django.utils import timezone
from .models import List, Item, User

# Create your views here.
def home(request):
    return render(request, 'home.html')

def logout_view(request):
    logout(request)
    return redirect("/")


def list_view(request, list_id):
    list_obj = get_object_or_404(List, pk=list_id)
    list_items = Item.objects.filter(list_id=list_obj)
    return render(request, 'list.html', {'list_obj': list_obj, 'list_items': list_items})


def delete_item(request, item_id):
    item = get_object_or_404(Item, pk=item_id)
    if request.method == 'POST':
        item.delete()
    return redirect('list_view', list_id=item.list_id.id)

def add_item(request, list_id):
    if request.method == 'POST':
        list_obj = get_object_or_404(List, pk=list_id)
        item_descr = request.POST.get('item_descr')
        new_item = Item.objects.create(list_id=list_obj, item_descr=item_descr, item_date_added=timezone.now(), item_done=False)
    return redirect('list_view', list_id=list_id)

def item_details(request, item_id):
    item = get_object_or_404(Item, pk=item_id)
    list_name = item.list_id.list_name
    return render(request, 'item_details.html', {'item': item, 'list_name': list_name})
