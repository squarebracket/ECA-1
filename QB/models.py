from django.db import models
from people.models import Person

# class Transaction(models.Model):
#
#     QB_CHEQUE = 0
#     QB_DEPOSIT = 1
#     QB_BILL = 2
#     QB_INVOICE = 3
#     QB_BILL_PAYMENT = 4
#     QB_INVOICE_PAYMENT = 5
#
#     QB_TXN_TYPES = (
#         QB_CHEQUE,
#         QB_DEPOSIT,
#         QB_BILL,
#         QB_INVOICE,
#         QB_BILL_PAYMENT,
#         QB_INVOICE_PAYMENT
#     )
#
#     txn_line_id = models.CharField(max_length=36, unique=True)
#     txn_parent_id = models.CharField(max_length=36)
#     date = models.DateField()
#     ref_num = models.CharField(max_length=32)
#     society = models.ForeignKey(Division)
#     budget_line = models.ForeignKey(BudgetLine, null=True, blank=True)
#     memo = models.CharField(max_length=512)
#     name = models.ForeignKey(Person)
