from django.shortcuts import render
from django.core import serializers
from django.http import HttpResponse, HttpResponseBadRequest
from reportlab.pdfgen import canvas
from Seller.models import Item



# Create your views here.
def get_item(request, sid):
    try:
        data = serializers.serialize('json', [Item.objects.get(id=sid), ])
    except Item.DoesNotExist:
        return HttpResponseBadRequest('Item does not exist')
    return HttpResponse(data)


def some_view(request):
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'filename="somefilename.pdf"'

    # Create the PDF object, using the response object as its "file."
    p = canvas.Canvas(response)

    # Draw things on the PDF. Here's where the PDF generation happens.
    # See the ReportLab documentation for the full list of functionality.
    p.drawString(100, 100, "Hello world.")

    # Close the PDF object cleanly, and we're done.
    p.showPage()
    p.save()
    return response