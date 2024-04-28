from django.shortcuts import render, redirect, HttpResponse, get_object_or_404
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from .models import List, Item
from django.contrib.auth.models import User


def home(request):
    return render(request, 'home.html')

def logout_view(request):
    logout(request)
    return redirect("/")

@login_required
def list_view(request, list_id):
    list_obj = get_object_or_404(List, pk=list_id)
    filter_option = request.GET.get('filter')


    if filter_option == 'date_added':
        list_items = Item.objects.filter(list_id=list_obj).order_by('-item_date_added')
    elif filter_option == 'description':
        list_items = Item.objects.filter(list_id=list_obj).order_by('item_descr')
    elif filter_option == 'completed':
        list_items = Item.objects.filter(list_id=list_obj).order_by('item_done')
    else:
        list_items = Item.objects.filter(list_id=list_obj)

    return render(request, 'list.html', {'list_obj': list_obj, 'list_items': list_items})


@login_required
def delete_item(request, item_id):
    item = get_object_or_404(Item, pk=item_id)
    if request.method == 'POST' and item.list_id.user_id == request.user:
        item.delete()
    return redirect('list_view', list_id=item.list_id.id)

@login_required
def add_item(request, list_id):
    list_obj = get_object_or_404(List, pk=list_id)
    if request.method == 'POST':
        item_descr = request.POST.get('item_descr')
        if list_obj.user_id == request.user:
            new_item = Item.objects.create(list_id=list_obj, item_descr=item_descr, item_date_added=timezone.now(), item_done=False)
    return redirect('list_view', list_id=list_id)

@login_required
def item_details(request, item_id):
    item = get_object_or_404(Item, pk=item_id)
    list_name = item.list_id.list_name
    return render(request, 'item_details.html', {'item': item, 'list_name': list_name})

@login_required
def item_done(request, item_id):
    item = get_object_or_404(Item, pk=item_id)
    item.item_done = not item.item_done
    item.save()
    return redirect('list_view', list_id = item.list_id.id)

@login_required
def lists_index(request):
    filter_option = request.GET.get('filter')

    if filter_option == 'list_name':
        lists = List.objects.filter(user_id=request.user).order_by('list_name')
    else:
        lists = List.objects.filter(user_id=request.user)
    return render(request, 'lists_index.html', {'lists': lists})


@login_required
def add_list(request):
    if request.method == 'POST':
        user_fk = request.user
        list_name = request.POST.get('list_name')
        new_list = List.objects.create(user_id=user_fk, list_name = list_name)
    return redirect('lists_index')

@login_required
def delete_list(request, list_id):
    list_obj = get_object_or_404(List, pk=list_id)
    if request.method == 'POST' and request.user == list_obj.user_id:
        list_obj.delete()
    return redirect('lists_index')