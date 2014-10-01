from django.db import models
from django.contrib.auth.models import User
from django.dispatch import receiver
from django.db.models.signals import post_save

FINE_ARTS = 'FA'
ENCS = 'ENCS'
JMSB = 'JMSB'
ART_SCI = 'A+S'
FACULTY_CHOICES = (
    (ENCS, 'Engineering and Computer Science'),
    (JMSB, 'John Molson School of Business'),
    (FINE_ARTS, 'Fine Arts'),
    (ART_SCI, 'Arts and Science'),
)

MALE = 'M'
FEMALE = 'F'
OTHER = 'O'
SEX_CHOICES = (
    (MALE, 'Male'),
    (FEMALE, 'Female'),
    (OTHER, 'Not disclosed')
)

# Create your models here.
class Student(models.Model):
    student_id = models.IntegerField(unique=True, db_index=True, null=True, blank=True)

    first_name = models.CharField(max_length=50, db_index=True)
    last_name = models.CharField(max_length=50, db_index=True)
    sex = models.CharField(max_length=1, null=True, blank=True, choices=SEX_CHOICES)

    email = models.EmailField(max_length=254, unique=True)
    address = models.TextField()
    postal_code = models.CharField(max_length=10)
    phone = models.CharField(max_length=15, null=True, blank=True)

    faculty = models.CharField(max_length=10, choices=FACULTY_CHOICES)
    department = models.CharField(max_length=50, null=True, blank=True)
    program1 = models.CharField(max_length=50)
    program2 = models.CharField(max_length=50, null=True, blank=True)
    program3 = models.CharField(max_length=50, null=True, blank=True)
    year_admitted = models.CharField(max_length=4, null=True, blank=True)

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