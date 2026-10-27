from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


class List(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    list_name = models.CharField(max_length=200)


class Item(models.Model):
    list = models.ForeignKey(List, on_delete=models.CASCADE)
    item_date_added = models.DateTimeField("date added", default=timezone.now)
    item_descr = models.CharField(max_length=200)
    item_done = models.BooleanField(default=False)
