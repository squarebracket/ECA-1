from django.dispatch import receiver, Signal
from django.db.models.signals import post_save, m2m_changed
from Seller.pdf import PDFReceipt
from Seller.models import Receipt
from Seller.emails import ReceiptEmail

post_save_related = Signal(providing_args=['instance', 'change'])


@receiver(post_save_related)
def generate_pdf(sender, **kwargs):
    receipt = kwargs['instance']
    pdf = PDFReceipt(receipt)
    email = ReceiptEmail(receipt, pdf)