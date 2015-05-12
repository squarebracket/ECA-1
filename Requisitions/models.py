from django.db import models
from sortedm2m.fields import SortedManyToManyField

from people.models import Person, Student
from core.models import LineItem, Transaction, FiscalYear


# from django.contrib.auth.models import
class ApprovalActions(object):
    APPROVE = 1
    APPROVE_SEND = 2
    REJECT = 3
    DEFER = 4

    choices = (
        (APPROVE, 'Approve'),
        (APPROVE_SEND, 'Approved and sent'),
        (REJECT, 'Reject'),
        (DEFER, 'Defer to'),
    )

    @staticmethod
    def approve(requisition, person_id, comment, highlight, send_to=None):
        """Approve a requisition and send to next approver (if there is one)."""
        next_person = requisition.next()
        requisition.currently_at = next_person
        requisition.save()
        log = ApprovalLog(person_id=person_id, sent_to=next_person, action=ApprovalActions.APPROVE,
                          requisition=requisition, comment=comment, highlight=highlight)
        log.save()
        return next_person

    @staticmethod
    def approve_send(requisition, person_id, comment, highlight, send_to):
        """Approve a requisition and send to a specific person."""
        requisition.currently_at = send_to
        log = ApprovalLog(perso_idn=person_id, sent_to=send_to, action=ApprovalActions.APPROVE_SEND,
                          requisition=requisition, comment=comment, highlight=highlight)
        log.save()
        return send_to

    @staticmethod
    def reject(requisition, person_id, comment, highlight):
        """Reject a requisition."""
        log = ApprovalLog(person_id=person_id, sent_to=None, action=ApprovalActions.REJECT,
                          requisition=requisition, comment=comment, highlight=highlight)
        log.save()

    @staticmethod
    def defer(requisition, person_id, comment, highlight, send_to):
        requisition.currently_at = send_to
        log = ApprovalLog(person_id=person_id, sent_to=send_to, action=ApprovalActions.DEFER,
                          requisition=requisition, comment=comment, highlight=highlight)
        log.save()

    methods = (
        (APPROVE, approve),
        (APPROVE_SEND, approve_send),
        (REJECT, reject),
        (DEFER, defer),
    )


class Requisition(Transaction):
    created_by = models.ForeignKey(Student, related_name='requisitions_created')
    division_ref_num = models.CharField(max_length=50, null=True, blank=True)
    currently_at = models.ForeignKey(Person, related_name='requisition_queue')
    _approval_index = models.PositiveSmallIntegerField(default=0)
    approval_queue = models.ForeignKey('ApprovalQueue')

    def __init__(self, *args, **kwargs):
        super(Requisition, self).__init__(*args, **kwargs)
        for (code, method) in ApprovalActions.methods:
            setattr(self, "_%s" % method.__func__.__name__, method.__func__)
            setattr(self, method.__func__.__name__, self.__dict__["_%s" % method.__func__.__name__].__get__(self, Requisition))

    def next(self):
        return self.approval_queue.approvals.all()[self._approval_index+1].persons.get()


class RequisitionStatus(object):
    ENTERED = 1
    CLEARED = 2
    AWAITING_APPROVAL = 3
    AWAITING_PRINT = 4
    AWAITING_SIGNATURES = 5
    SENT = 6
    WAITING_DELIVERY = 7
    RECEIVED = 8
    DEPOSITED_NOT_TRANSFERRED = 9
    EMAILED = 10

    StatusChoices = (
        (ENTERED, 'Submitted'),
        (CLEARED, 'Cleared bank account'),
        (AWAITING_APPROVAL, 'Awaiting approval'),
        (AWAITING_PRINT, 'Approved; Awaiting print'),
        (AWAITING_SIGNATURES, 'Printed; Awaiting signatures'),
        (SENT, 'Mailed to recipient'),
        (WAITING_DELIVERY, 'Waiting for delivery'),
        (RECEIVED, 'Payment received'),
        (DEPOSITED_NOT_TRANSFERRED, 'Deposited to main account; awaiting transfer'),
        (EMAILED, 'Emailed; awaiting reply'),
    )


class StatusLog(models.Model):
    person = models.ForeignKey(Person)
    requisition = models.ForeignKey(Requisition)
    timestamp = models.DateTimeField(auto_now_add=True)
    status = models.PositiveSmallIntegerField(choices=RequisitionStatus.StatusChoices)


class ReqLineItem(LineItem):
    doc_file = models.FileField(upload_to='requisitions')
    doc_date = models.DateField()
    # requisition = models.ForeignKey(Requisition)


class Reimbursement(Requisition):
    payee = models.ForeignKey(Person)

    def __unicode__(self):
        return "To %s for %s" % (self.payee.full_name, self.total_amount)


class DirectPayment(Requisition):
    payee = models.ForeignKey(Person)
    payee_ref_num = models.CharField(max_length=50)
    payee_ref_date = models.DateField()


class InvoiceRequest(Requisition):
    payee = models.ForeignKey(Person)
    payee_ref_num = models.CharField(max_length=50)


class ApprovalQueue(models.Model):
    name = models.CharField(max_length=50)
    approvals = SortedManyToManyField('Approval')


# TODO: Add string representation
class Approval(models.Model):
    SINGLE_PERSON = 0
    ONE_OF_MANY = 1

    TYPE_CHOICES = (
        (SINGLE_PERSON, 'Only one person'),
        (ONE_OF_MANY, 'One of many'),
    )

    type = models.PositiveSmallIntegerField(choices=TYPE_CHOICES)
    persons = models.ManyToManyField(Person)
    year = models.ForeignKey(FiscalYear)

    def __unicode__(self):
        peeps = ", ".join([str(p) for p in self.persons.all()])
        return "%s: %s" % (Approval.TYPE_CHOICES[self.type][1], peeps)


class ApprovalLog(models.Model):
    
    person = models.ForeignKey(Person)
    sent_to = models.ForeignKey(Person, related_name='sent_to', null=True)
    action = models.PositiveSmallIntegerField(choices=ApprovalActions.choices)
    timestamp = models.DateTimeField(auto_now_add=True)
    requisition = models.ForeignKey(Requisition)
    comment = models.TextField(blank=True, null=True)
    highlight = models.TextField(blank=True, null=True)

    def __unicode__(self):
        return "%s by %s" % (self.action, self.person.full_name)