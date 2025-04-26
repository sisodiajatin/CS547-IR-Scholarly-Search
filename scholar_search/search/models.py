from django.db import models

# Create your models here.


# test table for user management
class umTester(models.Model):
    # create tables for users management
    username = models.CharField(max_length=32) # username
    password = models.CharField(max_length=64) # password
    major = models.CharField(max_length=64) # major


