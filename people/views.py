from django.core import serializers
from django.db.models import Q
from django.http import HttpResponseBadRequest, HttpResponse
from django.shortcuts import render

# Create your views here.
from people.models import Student


def search_student(request, info):

    if unicode(info).isnumeric():
        return HttpResponse(serializers.serialize('json', Student.objects.filter(id__startswith=info)))
    students = Student.objects.all()
    for term in info.split():
        students = students.filter(Q(first_name__icontains=term) | Q(last_name__icontains=term))
    return HttpResponse(serializers.serialize('json', students))


def get_student(request, sid):
    try:
        data = serializers.serialize('json', [Student.objects.get(id=sid), ])
    except Student.DoesNotExist:
        return HttpResponseBadRequest('Student does not exist')
    return HttpResponse(data)