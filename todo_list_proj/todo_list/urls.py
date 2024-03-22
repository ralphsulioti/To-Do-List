from django.urls import path
from . import views

urlpatterns = [
    path('', views.home),
    path('logout', views.logout_view),
    path('<int:list_id>/', views.list_view, name='list_view'),
    path('delete/<int:item_id>/', views.delete_item, name='delete_item'),
    path('add/<int:list_id>/', views.add_item, name='add_item'),
    path('details/<int:item_id>/', views.item_details, name='item_details'),
]
