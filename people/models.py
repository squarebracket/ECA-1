from django.db import models
from django.contrib.auth.models import User
from django.dispatch import receiver
from django.db.models.signals import post_save

# Create your models here.
class Student(models.Model):
    id = models.IntegerField(primary_key=True)
    first_name = models.CharField(max_length=50, db_index=True)
    last_name = models.CharField(max_length=50, db_index=True)
    email = models.EmailField(max_length=254, unique=True)
    address = models.TextField()
    postal_code = models.CharField(max_length=10)
    program = models.CharField(max_length=15)
    edited = models.BooleanField()

    def create_user(self, password=None):
        newuser = User.objects.create_superuser(self.email, email=self.email, password=password, first_name=self.first_name,
                                                last_name=self.last_name)
        return newuser

    def __unicode__(self):
        return self.full_name

    @property
    def full_name(self):
        return "%s %s" % (self.first_name, self.last_name)

    class Meta:
        ordering = ['last_name', 'first_name']