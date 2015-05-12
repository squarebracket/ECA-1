from django.contrib import admin
from django import forms
from django.core.urlresolvers import reverse
from Requisitions.models import Approval, ApprovalQueue, Reimbursement, DirectPayment, \
    InvoiceRequest, ReqLineItem, Requisition, ApprovalActions
from people.models import Student, Person
from core.models import Account, TaxCode
from datetime import datetime
from django.conf.urls import patterns
from django.http import HttpResponse
from django.shortcuts import redirect
from django.utils.encoding import force_text
from django.contrib import messages

class ApprovalAdmin(admin.ModelAdmin):
    filter_horizontal = ['persons', ]


class ReqLineItemAdmin(admin.TabularInline):
    model = ReqLineItem
    fields = ['division', 'budget_line', 'memo', 'tax_code', 'tax_included',
              '_amount_entered', 'doc_date', 'doc_file', 'tags', 'amount_with_tax']
    readonly_fields = ['amount_with_tax', ]
    verbose_name = 'Requisition Line Item'
    verbose_name_plural = 'Requisition Line Items'
    extra = 1

    def amount_with_tax(self, instance):
        if instance.amount:
            return "$%.2f" % (instance.amount, )
        return ''


# class RequisitionAdminForm(forms.ModelForm):
#     class Meta:
#         model = Requisition
#         widgets = {'total_amount', forms.HiddenInput}


class RequisitionAdmin(admin.ModelAdmin):
    inlines = [ReqLineItemAdmin, ]
    # filter_horizontal = ['tags', ]
    fieldsets = [
        ['Requisition Info', {
            'fields': [('division_ref_num', 'total'), 'total_amount'],
        }]
    ]
    readonly_fields = ['total', ]

    # def get_form(self, request, obj=None, **kwargs):
    #     form = super(RequisitionAdmin, self).get_form(request, obj, **kwargs)
    #     print form

    def save_model(self, request, obj, form, change):
        # print form
        obj.created_by = Student.objects.get(person_ptr_id=request.user.id)
        obj.approval_queue = ApprovalQueue.objects.get(id=1)
        obj.currently_at = obj.next()
        obj.date = datetime.now().date()
        obj.split_account = Account.objects.get(number=1111)
        obj.save()

    @staticmethod
    def wrap_in_span(attr, instance):
        if instance.pk is None:
            return '<span id="%s"></span>' % (attr,)
        return '<span id="%s">%s</span>' % (attr, getattr(instance.payee, attr) or "")

    def total(self, instance):
        if instance is None:
            return '<span id="total"></span>'
        return '<span id="total">$%.2f</span>' % instance.amount

    def get_urls(self):
        urls = super(RequisitionAdmin, self).get_urls()
        approve_urls = patterns('',
            (r'^(\d+)/approve/$', self.approve),
        )
        return approve_urls + urls

    # TODO: make it actually take the right person for the approval log
    def approve(self, request, id):
        obj = Requisition.objects.get(id=id)
        sent_to = ApprovalActions.approve(obj, request.user.id, 'comment', None)
        model = self.model
        opts = model._meta
        if sent_to:
            msg = 'The %(name)s "%(obj)s" was approved and sent to %(user)s.' % \
                  {'name': force_text(opts.verbose_name), 'obj': force_text(obj), 'user': sent_to.full_name}
        else:
            msg = 'The %(name)s "%(obj)s" was approved.' % {
                'name': force_text(opts.verbose_name), 'obj': force_text(obj)}
        self.message_user(request, msg, messages.SUCCESS)
        return redirect(reverse('admin:%s_%s_changelist' % (opts.app_label, opts.model_name),
                                current_app=self.admin_site.name))

    class Media:
        js = ("requisitions/requisition_utils.js", )


class RequisitionWithPayeeForm(forms.ModelForm):
    searcher = forms.CharField(required=False, max_length=15)
    payee = forms.CharField(widget=forms.HiddenInput)

    class Meta:
        model = Requisition
        fields = ['payee', ]
        widgets = {'total_amount': forms.HiddenInput}

    def clean_payee(self):
        return Student.objects.get(id=self.cleaned_data['payee'])


class RequisitionWithPayeeAdmin(RequisitionAdmin):
    form = RequisitionWithPayeeForm
    fieldsets = [
        ['Payee', {
            'fields': [['searcher', ], ['payee', ], ['first_name', 'last_name', 'email', 'address']],
        }],
    ]
    fieldsets.extend(RequisitionAdmin.fieldsets)

    readonly_fields = ['first_name', 'last_name', 'email', 'address']
    readonly_fields.extend(RequisitionAdmin.readonly_fields)

    def first_name(self, instance):
        return self.wrap_in_span('first_name', instance)

    def last_name(self, instance):
        return self.wrap_in_span('last_name', instance)

    def email(self, instance):
        return self.wrap_in_span('email', instance)

    def address(self, instance):
        return self.wrap_in_span('address', instance)


class ReimbursementAdmin(RequisitionWithPayeeAdmin):
    fieldsets = RequisitionWithPayeeAdmin.fieldsets
    # TODO: This
    fieldsets[0][1]['fields'][1].append('student_id')
    readonly_fields = RequisitionWithPayeeAdmin.readonly_fields
    readonly_fields.extend(['student_id', ])

    def student_id(self, instance):
        if instance.pk is None:
            return '<span id="student_id"></span>'
        return '<span id="student_id">%s</span>' % (getattr(instance.payee.student, 'student_id'))
    
# class ApprovalQueueAdmin(admin.ModelAdmin):
#     filter_horizontal = ['approvals', ]

registers = [ApprovalQueue, DirectPayment, InvoiceRequest]
admin.site.register(registers)
admin.site.register(Approval, ApprovalAdmin)
admin.site.register(Reimbursement, ReimbursementAdmin)