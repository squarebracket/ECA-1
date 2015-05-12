from django.dispatch import receiver
from Seller.signals import post_save_related
from Seller.admin import ReceiptAdmin
from QB.qb2 import SalesReceipt
from QB import QuickbooksConnection as qbc
import pythoncom


@receiver(post_save_related)
def save_to_quickbooks(sender, **kwargs):
    print 'signal intercepted'
    if sender is ReceiptAdmin:
        print 'signal processing'
        instance = kwargs['instance']
        s = SalesReceipt.from_receipt(instance)
        try:
            s.add()
            instance.qb_id = s.list_id
            print s.list_id
            instance.save()
            print 'added things to instance'
        except:
            print 'failure.'
            raise

