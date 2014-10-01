from django.core import serializers
from django.http import HttpResponseBadRequest, HttpResponse
from django.shortcuts import render

# Create your views here.
from people.models import Student


def get_student(request, sid):
    try:
        data = serializers.serialize('json', [Student.objects.get(id=sid), ])
    except Student.DoesNotExist:
        return HttpResponseBadRequest('Student does not exist')
    return HttpResponse(data)