from django.contrib import admin
from django.contrib.auth.models import User
from people.models import Student, Person, DivisionPerson
from Inventory.settings import DEFAULT_PASSWORD


# Register your models here.
def create_user_from_student(modeladmin, request, queryset):
    for student in queryset:
        student.create_user(DEFAULT_PASSWORD)


class StudentAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'student_id', 'email', 'address']
    search_fields = ['first_name', 'last_name', 'student_id']
    exclude = ['edited', ]
    actions = [create_user_from_student]

    def save_model(self, request, obj, form, change):
        obj.edited = True
        obj.save()


class DivisionPersonAdmin(admin.ModelAdmin):
    def save_model(self, request, obj, form, change):
        try:
            user = User.objects.get(email=obj.division_email)
        except User.DoesNotExist:
            user = None
        obj.user = user
        obj.save()


admin.site.register(Student, StudentAdmin)
admin.site.register(Person)
admin.site.register(DivisionPerson)