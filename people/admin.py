from django.contrib import admin
from people.models import Student
from Inventory.settings import DEFAULT_PASSWORD


# Register your models here.
def create_user_from_student(modeladmin, request, queryset):
    for student in queryset:
        student.create_user(DEFAULT_PASSWORD)

class StudentAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'id', 'email', 'address']
    search_fields = ['first_name', 'last_name', 'id']
    exclude = ['edited', ]
    actions = [create_user_from_student]

    def save_model(self, request, obj, form, change):
        obj.edited = True
        obj.save()


admin.site.register(Student, StudentAdmin)