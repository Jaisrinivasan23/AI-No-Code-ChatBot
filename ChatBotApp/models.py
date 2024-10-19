from django.db import models
from django.contrib.auth.models import User
# Create your models here.


class User_ChatData(models.Model):
    Business_name = models.CharField(null=False,max_length=100)
    Business_Hours = models.CharField(null=False,max_length=100)
    Business_type = models.CharField(null=False,max_length=100)
    Business_Location = models.CharField(null=False,max_length=200)
    services = models.TextField(null=False)
    About_business = models.TextField(null=False)
    
    
    def __str__(self):
        return self.Business_name
    
    
    