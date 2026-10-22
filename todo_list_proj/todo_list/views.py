from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .models import Item, List


def get_user_list(request: HttpRequest, list_id: int) -> List:
    """Return the requesting user's list with this id, or raise Http404."""
    return get_object_or_404(List, pk=list_id, user_id=request.user)


def get_user_item(request: HttpRequest, item_id: int) -> Item:
    """Return an item on one of the requesting user's lists, or raise Http404."""
    return get_object_or_404(Item, pk=item_id, list_id__user_id=request.user)


def home(request: HttpRequest) -> HttpResponse:
    return render(
        request,
        "home.html",
        {"google_login_enabled": settings.GOOGLE_LOGIN_ENABLED},
    )


@login_required
def list_view(request: HttpRequest, list_id: int) -> HttpResponse:
    list_obj = get_user_list(request, list_id)
    filter_option = request.GET.get("filter")

    if filter_option == "date_added":
        list_items = Item.objects.filter(list_id=list_obj).order_by("-item_date_added")
    elif filter_option == "description":
        list_items = Item.objects.filter(list_id=list_obj).order_by("item_descr")
    elif filter_option == "completed":
        list_items = Item.objects.filter(list_id=list_obj).order_by("item_done")
    else:
        list_items = Item.objects.filter(list_id=list_obj)

    return render(
        request, "list.html", {"list_obj": list_obj, "list_items": list_items}
    )


@login_required
@require_POST
def delete_item(request: HttpRequest, item_id: int) -> HttpResponse:
    item = get_user_item(request, item_id)
    item.delete()
    return redirect("list_view", list_id=item.list_id.id)


@login_required
@require_POST
def add_item(request: HttpRequest, list_id: int) -> HttpResponse:
    list_obj = get_user_list(request, list_id)
    Item.objects.create(
        list_id=list_obj,
        item_descr=request.POST.get("item_descr"),
        item_date_added=timezone.now(),
        item_done=False,
    )
    return redirect("list_view", list_id=list_obj.id)


@login_required
def item_details(request: HttpRequest, item_id: int) -> HttpResponse:
    item = get_user_item(request, item_id)
    list_name = item.list_id.list_name
    return render(request, "item_details.html", {"item": item, "list_name": list_name})


@login_required
@require_POST
def item_done(request: HttpRequest, item_id: int) -> HttpResponse:
    item = get_user_item(request, item_id)
    item.item_done = not item.item_done
    item.save()
    return redirect("list_view", list_id=item.list_id.id)


@login_required
def lists_index(request: HttpRequest) -> HttpResponse:
    filter_option = request.GET.get("filter")

    if filter_option == "list_name":
        lists = List.objects.filter(user_id=request.user).order_by("list_name")
    else:
        lists = List.objects.filter(user_id=request.user)
    return render(request, "lists_index.html", {"lists": lists})


@login_required
@require_POST
def add_list(request: HttpRequest) -> HttpResponse:
    List.objects.create(user_id=request.user, list_name=request.POST.get("list_name"))
    return redirect("lists_index")


@login_required
@require_POST
def delete_list(request: HttpRequest, list_id: int) -> HttpResponse:
    get_user_list(request, list_id).delete()
    return redirect("lists_index")
