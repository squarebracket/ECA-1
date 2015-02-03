from django.db import models
from django.contrib.auth.models import User
from django.dispatch import receiver
from django.db.models.signals import post_save
from social.backends.google import GoogleOAuth2
from core.models import Division, FiscalYear
from datetime import datetime

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


class Person(models.Model):
    full_name = models.CharField(max_length=256)
    first_name = models.CharField(max_length=50, db_index=True, null=True, blank=True)
    last_name = models.CharField(max_length=50, db_index=True, null=True, blank=True)
    email = models.EmailField(max_length=254, unique=True)
    address = models.TextField()
    # address_street = models.CharField(max_length=100)
    # address_suite = models.CharField(max_length=25)
    # address_city = models.CharField(max_length=100)
    # address_province = models.CharField(max_length=50)
    # address_country = models.CharField(max_length=70)
    postal_code = models.CharField(max_length=10)
    phone = models.CharField(max_length=15, null=True, blank=True)
    qb_list_id = models.CharField(max_length=36, null=True, blank=True)
    qb_edit_sequence = models.CharField(max_length=36, null=True, blank=True)

    # @property
    # def address(self):
    #     address = self.address_suite
    #     if self.address_suite:
    #         address += "\nSuite %s" % self.address_suite
    #     address += "\n%s" % self.address_city
    #     if self.address_province:
    #         address += ", %s" % self.address_province
    #     address += "\n%s" % self.address_country
    #     return address
    #
    # @property
    # def address_line(self):
    #     address = self.address_suite
    #     if self.address_suite:
    #         address += "\nSuite %s" % self.address_suite
    #     return address

    def save(self, *args, **kwargs):
        if not self.full_name and self.first_name and self.last_name:
            self.full_name = "%s %s" % (self.first_name, self.last_name)
        super(Person, self).save(*args, **kwargs)

    def __unicode__(self):
        return self.full_name


# Create your models here.
class Student(Person):
    student_id = models.IntegerField(unique=True, db_index=True, null=True, blank=True)

    sex = models.CharField(max_length=1, null=True, blank=True, choices=SEX_CHOICES)

    faculty = models.CharField(max_length=10, choices=FACULTY_CHOICES)
    department = models.CharField(max_length=50, null=True, blank=True)
    program1 = models.CharField(max_length=50)
    program2 = models.CharField(max_length=50, null=True, blank=True)
    program3 = models.CharField(max_length=50, null=True, blank=True)
    year_admitted = models.CharField(max_length=4, null=True, blank=True)

    edited = models.BooleanField(default=False)

    def create_user(self, password=None):
        newuser = User.objects.create_superuser(self.email, email=self.email, password=password,
                                                first_name=self.first_name, last_name=self.last_name)
        return newuser

    def __unicode__(self):
        if not self.student_id:
            return self.full_name
        return "%s (%s)" % (self.full_name, self.student_id)

    # def __getattr__(self, item):
    #     if hasattr(self.person, item):
    #         return getattr(self.person, item)
    #     raise

    class Meta:
        ordering = ['last_name', 'first_name']


class DivisionPerson(models.Model):
    division = models.ForeignKey(Division)
    student = models.ForeignKey(Student)
    position = models.CharField(max_length=50)
    year = models.ForeignKey(FiscalYear, null=True)
    division_email = models.EmailField()
    user = models.ForeignKey(User, null=True, blank=True)

    def __unicode__(self):
        return "%s %s %s: %s" % (self.year, self.division, self.position, self.student.full_name)


class CustomGoogleOAuth2(GoogleOAuth2):
    DEFAULT_SCOPE = ['openid', 'email', 'profile', 'https://spreadsheets.google.com/feeds',
                     'https://docs.google.com/feeds']


def create_user_from_oauth(strategy, details, user=None, *args, **kwargs):

    if user:
        return {'is_new': False}

    email = details['email']
    try:
        dp = DivisionPerson.objects.get(division_email=email)
        if dp.user:
            user = dp.user
        else:
            user = User(email=dp.division_email, first_name=dp.student.first_name,
                        last_name=dp.student.last_name, username=dp.division_email,
                        is_staff=True)
            user.save()
    except DivisionPerson.DoesNotExist:
        user = None
    return {
        'is_new': True,
        'user': user
    }