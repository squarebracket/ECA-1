from django.core import serializers
from django.http import HttpResponse, HttpResponseBadRequest
from reportlab.pdfgen import canvas
from Seller.models import Item
from datetime import datetime
from qb_export import IIFReceiptWrapper
from django.template import RequestContext, loader
from django.contrib.auth.decorators import login_required


# Create your views here.
def get_item(request, sid):
    try:
        data = serializers.serialize('json', [Item.objects.get(id=sid), ])
    except Item.DoesNotExist:
        return HttpResponseBadRequest('Item does not exist')
    return HttpResponse(data)

@login_required()
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


def export(request):
    if request.POST:

        s = datetime.utcfromtimestamp(float(request.POST.get('start')))
        e = datetime.utcfromtimestamp(float(request.POST.get('end')))

        objs = IIFReceiptWrapper.objects.filter(timestamp__range=(s, e))
        c = {
            'receipts': objs,
            'start': s.strftime('%Y-%m-%d'),
            'end': e.strftime('%Y-%m-%d'),
        }
    else:
        c = None
    template = loader.get_template('seller/export.html')
    context = RequestContext(request, c)
    return HttpResponse(template.render(context))
