from django import forms
from django.contrib import admin
from Seller.models import LineItem, Receipt, Item
from Seller.models import TransactionLog


# Register your models here.
from people.models import Student


class ReceiptLineItemInline(admin.TabularInline):
    model = LineItem
    extra = 0
    readonly_fields = ('amount', 'unit_cost', )
    # template = "admin/seller/tabular_custom.html"
    # form = LineItemForm

    fields = ['receipt', 'quantity', 'item', 'unit_cost', 'amount']

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
    buyer = forms.CharField(max_length=15)

    class Meta:
        model = Receipt
        fields = ['buyer', ]

    def clean_buyer(self):
        return Student.objects.get(id=self.cleaned_data['buyer'])


class ReceiptAdmin(admin.ModelAdmin):
    inlines = [ReceiptLineItemInline]
    excludes = ['seller']
    form = ReceiptForm
    readonly_fields = ('student_id', 'first_name', 'last_name', 'email', 'address', 'receipt_total')

    fields = (('buyer', 'student_id'), ('first_name', 'last_name', 'email', 'address'), ('paymeth', 'receipt_total'))

    def wrap_in_span(self, attr, instance):
        if instance.pk is None:
            return '<span id="%s"></span>' % (attr,)
        return '<span id="%s">%s</span>' % (attr, instance.buyer.__getattribute__(attr) or "")

    def student_id(self, instance):
        return self.wrap_in_span('student_id', instance)

    def first_name(self, instance):
        return self.wrap_in_span('first_name', instance)

    def last_name(self, instance):
        return self.wrap_in_span('last_name', instance)

    def email(self, instance):
        return self.wrap_in_span('email', instance)

    def address(self, instance):
        return self.wrap_in_span('address', instance)

    def save_model(self, request, obj, form, change):
        obj.seller = request.user
        # obj.buyer = Student.objects.get(pk=form.cleaned_data['buyer'])
        obj.save()

    def receipt_total(self, instance):
        if instance is None:
            return '<span id="receipt_total"></span>'
        return '<span id="receipt_total">$%.2f</span>' % instance.receipt_total()


    class Media:
        js = ("seller/get_buyer.js", )


class ItemAdmin(admin.ModelAdmin):
    list_display = ['name', 'cost', 'item_code', 'income_account', 'qb_class']

admin.site.register(Item, ItemAdmin)
admin.site.register(Receipt, ReceiptAdmin)
admin.site.register(TransactionLog)