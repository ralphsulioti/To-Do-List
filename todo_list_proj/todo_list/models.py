import datetime
from django.db import models
from django.utils import timezone

# Create your models here.
class User(models.Model):
    user_name = models.CharField(max_length=200)

    def __str__(self):
        return self.user_name

class List(models.Model):
    user_id = models.ForeignKey(User, on_delete=models.CASCADE)
    list_name = models.CharField(max_length=200)

    def __str__(self):
        return self.list_name

    def get_items(self):
        return self.get_items()
        #return self.item_set.all()  # Accessing related items through the foreign key relationship

class Item(models.Model):
    list_id = models.ForeignKey(List, on_delete=models.CASCADE)
    item_date_added = models.DateTimeField("date added")
    item_descr = models.CharField(max_length=200)
    item_done = models.BooleanField()

    def __str__(self):
        return self.item_descr

    #def was_published_recently(self):
     #   return self.item_date_added >= timezone.now() - datetime.timedelta(days=1)
