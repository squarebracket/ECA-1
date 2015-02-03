from django.contrib.auth.decorators import login_required
from django.core import serializers
from django.db.models import Q
from django.http import HttpResponseBadRequest, HttpResponse
from django.shortcuts import render
import json

# Create your views here.
from people.models import Student, Person


@login_required()
def search_student(request, info):
    results = []
    if unicode(info).isnumeric():
        for student in Student.objects.filter(student_id__startswith=info):
            results.append({'student_id': student.student_id, 'full_name': student.full_name,
                            'pk': student.pk})

        # print serializers.serialize('json', list(Student.objects.filter(student_id__startswith=info)) +
        #                             list(Person.objects.filter(student__student_id=info)))
        return HttpResponse(json.dumps(results))
    students = Student.objects.all()
    for term in info.split():
        students = students.filter(Q(first_name__icontains=term) | Q(last_name__icontains=term))
    for student in students:
        results.append({'student_id': student.student_id, 'full_name': student.full_name,
                        'pk': student.pk})
    return HttpResponse(json.dumps(results))


@login_required()
def search_person(request, info):
    results = []
    if unicode(info).isnumeric():
        for student in Student.objects.filter(student_id=info):
            results.append({'student_id': student.student_id, 'full_name': student.full_name,
                            'pk': student.pk})
        return HttpResponse(json.dumps(results))
    persons = Person.objects.all()
    for term in info.split():
        persons = persons.filter(Q(first_name__icontains=term) | Q(last_name__icontains=term))
    for person in persons:
        data = {'full_name': person.full_name, 'pk': person.pk}
        if hasattr(person, 'student'):
            data['student_id'] = person.student.student_id
        results.append(data)
    return HttpResponse(json.dumps(results))


@login_required
def get_student(request, sid):
    try:
        student = Student.objects.get(student_id=sid)
        data = {'student_id': student.student_id, 'full_name': student.full_name,
                'pk': student.pk, 'first_name': student.first_name,
                'last_name': student.last_name, 'email': student.email,
                'address': student.address}
    except Student.DoesNotExist:
        return HttpResponseBadRequest('Student does not exist')
    return HttpResponse(json.dumps(data))


@login_required()
def get_person(request, id):
    try:
        person = Person.objects.get(id=id)
        data = {'full_name': person.full_name, 'pk': person.pk,
                'first_name': person.first_name, 'last_name': person.last_name,
                'email': person.email, 'address': person.address}
        if hasattr(person, 'student'):
            data['student_id'] = person.student.student_id
    except Person.DoesNotExist:
        return HttpResponseBadRequest('Person does not exist with id %s' % id)
    return HttpResponse(json.dumps(data))