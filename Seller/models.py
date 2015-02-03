from django.contrib.admin.models import LogEntry
from django.contrib.contenttypes.models import ContentType
import gmail
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

# Create your models here.
from people.models import Student

from core.models import Item, LineItem, Transaction, PaymentMethod, TaxCode


class ReceiptLineItem(LineItem):
    quantity = models.SmallIntegerField()
    item = models.ForeignKey(Item)


    @property
    def receipt(self):
        return self.transaction


    # @property
    # def amount(self):
    #     return float(self.quantity * self.item.cost)

    def item_amount(self):
        return self.item.cost

    # def __unicode__(self):
    #     return "Receipt %d" % (self.transaction.pk, )

    def save(self, *args, **kwargs):
    #     print args, kwargs
        self.account = self.item.income_account
        self.memo = 'Sales Purchase'
    #     TODO: Make this not hardcoded
        self._amount_with_tax = self.item.cost * self.quantity
        # TODO: Make this not hardcoded
        self.tax_code = TaxCode.objects.get(code='S')
        # TODO: Make this not hardcoded
        self.tax_included = True
        self.division = self.item.division
        self.budget_line = self.item.budget_line
        super(ReceiptLineItem, self).save(*args, **kwargs)


class Receipt(Transaction):
    seller = models.ForeignKey(User)
    buyer = models.ForeignKey(Student)
    paymeth = models.ForeignKey(PaymentMethod)

    def receipt_total(self):
        total = 0.0
        receipt_line_items = [l.receiptlineitem for l in self.lineitem_set.all()]
        for receipt_line_item in receipt_line_items:
            total += receipt_line_item.quantity * float(receipt_line_item.item.cost)
        return total

    # @property
    # def receiptlineitem_set(self):
    #     return ReceiptLineItem.objects.filter(transaction=self.pk)

    def __unicode__(self):
        return "%s - $%.2f" % (self.buyer.full_name, self.receipt_total())
        # return "R%d: %s - $%.2f" % (self.pk, self.buyer.full_name, self.receipt_total())

    # def save(self, *args, **kwargs):
    #     super(Receipt, self).save(*args, **kwargs)
    #     print self.lineitem_set.all()
    #     make_receipt2(self)


class TransactionLog(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    message = models.TextField()

    def __unicode__(self):
        return self.message


@receiver(post_save, sender=LogEntry)
def add_to_log(sender, created=None, instance=None, update_fields=None, **kwargs):
    if type(instance) is not Receipt:
        return
    if created is True:
        msg = 'Receipt %i created\n' % (instance.pk, )
        fmt = '%i x %s = %.2f\n'
    if created is False:
        msg = 'Receipt %i EDITED\n' % (instance.pk, )
        fmt = '%i x %s  - %.2f\n'
    for line_item in instance.lineitem_set.all():
        msg += fmt % (line_item.quantity, line_item.item.item_code, line_item.amount)

    t = TransactionLog(message=msg)
    t.save()


# @receiver(post_save, sender=LogEntry)
# def make_receipt(sender, **kwargs):
#     instance = kwargs['instance']
#     ct = ContentType.objects.get_for_model(Receipt)
#     if ct.id == instance.content_type_id:
#         from pdf import PDFReceipt
#         receipt = Receipt.objects.get(id=instance.object_id)
#         pdf = PDFReceipt(receipt)
#         g = gmail.GMail("ECA Office Manager <office@ecaconcordia.ca>", 'ecaeca1234')
#         to = "%s <%s>" % (receipt.buyer.full_name, receipt.buyer.email)
#         text = '''
#         Hello,
#
#         Attached is your purchase receipt'''
#         m = gmail.Message(subject="Receipt", to=to, text=text, attachments=[pdf.filename, ])
#         #g.send(m)