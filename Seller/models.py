import gmail
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

# Create your models here.
from people.models import Student


class Receipt(models.Model):
    CASH = 'CASH'
    CHEQUE = 'CHEQUE'
    DEBIT = 'DEBIT'
    PAYMETH_CHOICES = (
        (CASH, 'Cash'),
        (CHEQUE, 'Cheque'),
        (DEBIT, 'Debit'),
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    seller = models.ForeignKey(User)
    buyer = models.ForeignKey(Student)
    paymeth = models.CharField(max_length=10, choices=PAYMETH_CHOICES)

    def receipt_total(self):
        total = 0.0
        for line_item in self.lineitem_set.all():
            total += line_item.quantity * float(line_item.item.cost)
        return total

    def __unicode__(self):
        return "R%d: %s - $%.2f" % (self.pk, self.buyer.full_name, self.receipt_total())


class Item(models.Model):
    name = models.CharField(max_length=150)
    cost = models.DecimalField(decimal_places=2, max_digits=5)
    item_code = models.CharField(max_length=25)
    income_account = models.IntegerField()
    qb_class = models.CharField(max_length=50)

    def __unicode__(self):
        return self.name


class LineItem(models.Model):
    receipt = models.ForeignKey(Receipt)
    quantity = models.PositiveSmallIntegerField()
    item = models.ForeignKey(Item)

    @property
    def amount(self):
        return float(self.quantity * self.item.cost)

    def item_amount(self):
        return self.item.cost

    def __unicode__(self):
        return "Receipt %d" % (self.receipt.pk, )


class TransactionLog(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    message = models.TextField()

    def __unicode__(self):
        return self.message


@receiver(post_save, sender=Receipt)
def make_receipt(sender, instance=None, update_fields=None, **kwargs):
    from pdf import PDFReceipt
    pdf = PDFReceipt(instance)
    g = gmail.GMail("ECA Office Manager <office@ecaconcordia.ca>", 'ecaeca1234')
    to = "%s <%s>" % (instance.buyer.full_name, instance.buyer.email)
    text = '''
    Hello,

    Attached is your purchase receipt'''
    m = gmail.Message(subject="Receipt", to=to, text=text, attachments=[pdf.filename,])
    # g.send(m)


@receiver(post_save, sender=Receipt)
def add_to_log(sender, created=None, instance=None, update_fields=None, **kwargs):
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