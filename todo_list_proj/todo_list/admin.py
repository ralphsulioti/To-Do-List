from django.contrib import admin
from .models import List, Item
from django.contrib.auth.models import User

# Register your models here.
admin.site.register(List)
admin.site.register(Item)