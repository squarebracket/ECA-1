from django import forms
from django.contrib import admin
from Seller.models import ReceiptLineItem, Receipt
from core.models import Item
from Seller.models import TransactionLog
from emails import ReceiptEmail
import gspread
from social.apps.django_app.default.models import UserSocialAuth
from django.db.models.signals import m2m_changed, pre_save, post_save
from django.dispatch import receiver
from Seller import signals


# Register your models here.
from people.models import Student


class ReceiptLineItemInline(admin.TabularInline):
    model = ReceiptLineItem
    extra = 0
    readonly_fields = ('amount', 'unit_cost')
    # template = "admin/seller/tabular_custom.html"
    # form = LineItemForm

    fields = ['quantity', 'item', 'unit_cost', 'amount']

    def amount(self, instance):
        if instance.amount:
            return "$%.2f" % (instance.amount, )
        # return html.escape(self.parent_model.__dict__)
        return '<span id="replace_this_one"><span>'

    def unit_cost(self, instance):
        return "$%.2f" % (instance.item.cost, )


class AdminA(admin.StackedInline):
    model = Student


class ReceiptForm(forms.ModelForm):
    searcher = forms.CharField(max_length=15, required=False)
    buyer = forms.CharField(widget=forms.HiddenInput)

    class Meta:
        model = Receipt
        fields = ['buyer', ]

    def clean_buyer(self):
        return Student.objects.get(id=self.cleaned_data['buyer'])


class ReceiptAdmin(admin.ModelAdmin):
    inlines = [ReceiptLineItemInline]
    # excludes = ['seller']
    form = ReceiptForm
    readonly_fields = ('student_id', 'first_name', 'last_name', 'email', 'address', 'receipt_total')
    search_fields = ['buyer__student_id', 'buyer__last_name', 'buyer__first_name', 'id']
    fields = (('searcher', 'student_id', 'buyer'), ('first_name', 'last_name', 'email', 'address'), ('paymeth', 'receipt_total'))

    # for attr in ['student_id', 'first_name', 'last_name', 'email', 'address']:
    #     setattr('ReceiptAdmin', attr, attr())

    def student_id(self, instance):
        return wrap_in_span('student_id', instance)

    def first_name(self, instance):
        return wrap_in_span('first_name', instance)

    def last_name(self, instance):
        return wrap_in_span('last_name', instance)

    def email(self, instance):
        return wrap_in_span('email', instance)

    def address(self, instance):
        return wrap_in_span('address', instance)

    def save_model(self, request, obj, form, change):
        obj.seller = request.user
        obj.save()

    def save_related(self, request, form, formsets, change):
        # At this point, instance should exist.
        parent_object = form.instance
        super(ReceiptAdmin, self).save_related(request, form, formsets, change)
        signals.post_save_related.send(sender=self.__class__, instance=parent_object, change=change)


    def receipt_total(self, instance):
        if instance is None:
            return '<span id="receipt_total"></span>'
        return '<span id="receipt_total">$%.2f</span>' % instance.receipt_total()

    class Media:
        js = ("seller/get_buyer.js", )


def wrap_in_span(attr, instance):
    if instance.pk is None:
        return '<span id="%s"></span>' % (attr,)
    return '<span id="%s">%s</span>' % (attr, instance.buyer.__getattribute__(attr) or "")


admin.site.register(Receipt, ReceiptAdmin)
admin.site.register(TransactionLog)