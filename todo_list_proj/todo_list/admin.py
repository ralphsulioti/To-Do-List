from django.contrib import admin
from .models import List, Item, User

# Register your models here.
admin.site.register(List)
admin.site.register(Item)
admin.site.register(User)