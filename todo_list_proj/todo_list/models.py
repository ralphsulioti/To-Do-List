import datetime
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User

class List(models.Model):
    user_id = models.ForeignKey(User, on_delete=models.CASCADE)
    list_name = models.CharField(max_length=200)

class Item(models.Model):
    list_id = models.ForeignKey(List, on_delete=models.CASCADE)
    item_date_added = models.DateTimeField("date added")
    item_descr = models.CharField(max_length=200)
    item_done = models.BooleanField()
