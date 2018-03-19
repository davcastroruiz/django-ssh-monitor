from django.db import models
from django.core.urlresolvers import reverse


# Create your models here.
class Connection(models.Model):
    alias = models.CharField(max_length=100)
    username = models.CharField(max_length=1000)
    password = models.CharField(max_length=250)
    port = models.CharField(max_length=4)
    ip = models.CharField(max_length=100)
