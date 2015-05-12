from django.shortcuts import render, redirect
from Requisitions.models import Requisition


# Create your views here.
def approve(request, requisition_number):
    req = Requisition.objects.get(id=requisition_number)
    print type(req)
    redirect('admin/Requisitions/reimbursement/%i' % requisition_number)