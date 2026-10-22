from urllib.parse import urlencode

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse, QueryDict
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from .forms import ItemForm, ListForm
from .models import Item, List

# Sort option (the `sort` parameter) -> ordering. The first entry is the
# default, and an unknown option falls back to it. Each order ends in `id`, so
# ties always come out the same way.
ITEM_SORT_ORDERS: dict[str, tuple[str, ...]] = {
    "normal": ("item_date_added", "id"),
    "date_added": ("-item_date_added", "-id"),
    "description": ("item_descr", "id"),
    "completed": ("item_done", "item_date_added", "id"),
}
# Lists have no creation date; `id` is creation order.
LIST_SORT_ORDERS: dict[str, tuple[str, ...]] = {
    "oldToNew": ("id",),
    "list_name": ("list_name", "id"),
}


def get_sort_option(params: QueryDict, sort_orders: dict[str, tuple[str, ...]]) -> str:
    """Return `params["sort"]` if it's in `sort_orders`, else the first option."""
    sort = params.get("sort", "")
    return sort if sort in sort_orders else next(iter(sort_orders))


def url_keeping_sort(
    url: str, request: HttpRequest, sort_orders: dict[str, tuple[str, ...]]
) -> str:
    """Return `url` with the form's posted sort option added, unless it's the default."""
    sort = get_sort_option(request.POST, sort_orders)
    if sort == next(iter(sort_orders)):
        return url
    return f"{url}?{urlencode({'sort': sort})}"


def redirect_to_list(request: HttpRequest, list_id: int) -> HttpResponse:
    """Redirect to a list's page, keeping the item sort the form was posted from."""
    url = reverse("list_view", kwargs={"list_id": list_id})
    return redirect(url_keeping_sort(url, request, ITEM_SORT_ORDERS))


def redirect_to_lists_index(request: HttpRequest) -> HttpResponse:
    """Redirect to the lists page, keeping the list sort the form was posted from."""
    return redirect(url_keeping_sort(reverse("lists_index"), request, LIST_SORT_ORDERS))


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
    sort = get_sort_option(request.GET, ITEM_SORT_ORDERS)
    list_items = Item.objects.filter(list_id=list_obj).order_by(*ITEM_SORT_ORDERS[sort])
    return render(
        request,
        "list.html",
        {"list_obj": list_obj, "list_items": list_items, "sort": sort},
    )


@login_required
@require_POST
def delete_item(request: HttpRequest, item_id: int) -> HttpResponse:
    item = get_user_item(request, item_id)
    item.delete()
    return redirect_to_list(request, item.list_id.id)


@login_required
@require_POST
def add_item(request: HttpRequest, list_id: int) -> HttpResponse:
    list_obj = get_user_list(request, list_id)
    form = ItemForm(request.POST)
    if form.is_valid():
        item: Item = form.save(commit=False)
        item.list_id = list_obj
        item.save()
    else:
        messages.error(request, form.errors["item_descr"][0])
    return redirect_to_list(request, list_obj.id)


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
    return redirect_to_list(request, item.list_id.id)


@login_required
def lists_index(request: HttpRequest) -> HttpResponse:
    sort = get_sort_option(request.GET, LIST_SORT_ORDERS)
    lists = List.objects.filter(user_id=request.user).order_by(*LIST_SORT_ORDERS[sort])
    return render(request, "lists_index.html", {"lists": lists, "sort": sort})


@login_required
@require_POST
def add_list(request: HttpRequest) -> HttpResponse:
    form = ListForm(request.POST)
    if form.is_valid():
        list_obj: List = form.save(commit=False)
        list_obj.user_id = request.user
        list_obj.save()
    else:
        messages.error(request, form.errors["list_name"][0])
    return redirect_to_lists_index(request)


@login_required
@require_POST
def delete_list(request: HttpRequest, list_id: int) -> HttpResponse:
    get_user_list(request, list_id).delete()
    return redirect_to_lists_index(request)
