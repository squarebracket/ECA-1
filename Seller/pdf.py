from reportlab.platypus import Paragraph, Frame, Table, PageTemplate, BaseDocTemplate
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.lib.pagesizes import letter
from Seller.models import Receipt
from reportlab.lib import colors
from os.path import join as path_join
from Inventory.settings import RECEIPT_DOCS_DIR
styles = getSampleStyleSheet()

Title = "Hello world"
pageinfo = "platypus example"
receipt_info = []


class PDFReceipt:

    def __init__(self, receipt):
        global receipt_info
        if type(receipt) is not Receipt:
            raise ValueError('receipt passed to PDFReceipt is not, in fact, a Receipt object')
        self.story = []
        self.receipt = receipt
        receipt_info = self.make_receipt_details()
        self.filename = path_join(RECEIPT_DOCS_DIR, 'Receipt %i.pdf') % (int(self.receipt.pk), )
        self.b = BaseDocTemplate(self.filename, pagesize=letter)
        self.f1 = Frame(0.5*inch, 0.5*inch, 7.5*inch, 7.5*inch, showBoundary=1)
        self.p = PageTemplate(id='t1', frames=[self.f1, ], onPage=receipt_details)
        self.b.addPageTemplates(self.p)
        self.make_story()
        self.b.build(self.story)

    def make_story(self):
        rows = [['Item', 'Quantity', 'Unit cost', 'Amount'], ]
        for lineitem in self.receipt.lineitem_set.all():
            rows.append([
                str(lineitem.item.name),
                str(lineitem.quantity),
                "$%.2f" % lineitem.item.cost,
                "$%.2f" % lineitem.amount])
        rows.append(['', '', Paragraph('<b>TOTAL</b>', styles['Normal']), Paragraph("<b>$%.2f</b>" % self.receipt.receipt_total(), styles['Normal'])])
        t = Table(rows, repeatRows=1, splitByRow=True, colWidths=[3.5*inch, 1*inch, 1*inch, 1*inch], style=[('ALIGN', (1, 0), (-1, -1), 'RIGHT'),])
        self.story.append(t)

    def make_receipt_details(self):
        return [
            ['Date', self.receipt.timestamp.strftime('%B %d, %Y')],
            ['Purchaser', Paragraph(self.receipt.buyer.full_name, styles['Normal'])],
            ['Payment method', self.receipt.paymeth],
            ['Employee', Paragraph("%s %s" % (self.receipt.seller.first_name, self.receipt.seller.last_name), styles['Normal'])],
            ['Receipt #', str(self.receipt.pk)],
        ]

def receipt_details(canvas, document):
    import os
    print os.getcwd()
    canvas.bottomUp = 1
    t = Table(receipt_info, repeatRows=1, style=[('GRID', (0, 0), (-1, -1), 0.5, colors.grey), ])
    t.wrap(3.5*inch, 1.5*inch)
    t.drawOn(canvas, 4.5*inch, 8.5*inch)
    canvas.bottomUp = 0
    canvas.saveState()
    canvas.scale(0.10, 0.10)
    canvas.translate(2.5*inch, 85*inch)
    canvas.drawImage(os.path.join('Seller', '05-full-3-colour.png'), 0.5*inch, 8.5*inch, mask=[255, 255, 255, 255, 255, 255])
    canvas.restoreState()
    textObject = canvas.beginText()
    textObject.setTextOrigin(0.5*inch, 9*inch)
    textObject.setFont(styles['Normal'].fontName, styles['Normal'].fontSize, leading=styles['Normal'].leading)

    textObject.textLine('1455 de Maisonneuve Ouest, Suite H-838')
    textObject.textLine('Montreal, QC, Canada')
    textObject.textLine('H3G1M8')
    canvas.drawText(textObject)
