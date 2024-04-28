from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('logout', views.logout_view, name='logout_view'),
    path('<int:list_id>/', views.list_view, name='list_view'),
    path('delete/<int:item_id>/', views.delete_item, name='delete_item'),
    path('add/<int:list_id>/', views.add_item, name='add_item'),
    path('details/<int:item_id>/', views.item_details, name='item_details'),
    path('done/<int:item_id>/', views.item_done, name='item_done'),
    path('lists_index', views.lists_index, name='lists_index'),
    path('add_list/', views.add_list, name='add_list'),
    path('delete_list/<int:list_id>/', views.delete_list, name='delete_list'),
]
