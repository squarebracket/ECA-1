__author__ = 'chuck'
from Seller.models import Receipt, Item
from datetime import datetime, timedelta
import csv
import django.template.base

types = {
    'HDI': 'Store Apparel:Sweater:Hoodie',
    'ZIP': 'Store Apparel:Sweater:Zip-up - no hood',
    'ZPH': 'Store Apparel:Sweater:Zip-up hoodie',
    'KZPH': 'Store Apparel:NON-STOCK:Sweater:Zip-up hoodie',
    'GHDI': 'Store Apparel:NON-STOCK:Sweater:Hoodie',
    'KZIP': 'Store Apparel:NON-STOCK:Sweater:Zip-up - no hood',
    'GZPH': 'Store Apparel:NON-STOCK:Sweater:Zip-up hoodie',
    'WMN': 'Store Apparel:T-shirt:I\'m in it for the women',
    'IMG': 'Store Apparel:T-shirt:Keep it real',
    'RGD': 'Store Apparel:T-shirt:Rigid members',
    'STY': 'Store Apparel:T-shirt:Safety first',
    'SIN': 'Store Apparel:T-shirt:SOH CAH TOA',
    'EPL': 'Store Apparel:Polo:Embroidered Polo',
    'UPL': 'Store Apparel:NON-STOCK:Polo:Unembroidered Polo',
    'TUQ': 'Store Apparel:Headwear:Tuque',
    'SPA': 'Store Apparel:Pants:Sweat Pants',
    'SPG': 'Store Apparel:Pants:Sweat Pants',
    'SPAN': 'Store Apparel:NON-STOCK:Pants:Sweat Pants',
    'SPGN': 'Store Apparel:NON-STOCK:Pants:Sweat Pants',
    'BXR': 'Store Apparel:Other:Boxers',
    'KIL': 'Store Apparel:Pants:Kilts',
    'TKT': 'Event Ticket',
}


class IIFReceiptWrapper(Receipt):

    class Meta:
        proxy = True

    def make_trns_row(self):
        writerow = {}
        writerow['type'] = 'TRNS'
        writerow['ID'] = ''
        writerow['trnstype'] = 'CASH SALE'
        writerow['date'] = self.timestamp.date()
        if self.paymeth == 'CASH':
            writerow['account'] = '1161'
        elif self.paymeth == 'CHEQUE':
            writerow['account'] = '1499'
        elif self.paymeth == 'DEBIT':
            writerow['account'] = '1111'
        writerow['name'] = ''
        writerow['class'] = ''
        writerow['amount'] = self.receipt_total()
        writerow['docnum'] = ''
        writerow['memo'] = 'Items sold to %s (by %s)' % (self.buyer.full_name, self.seller.get_full_name())
        writerow['clear'] = 'N'
        writerow['f1'] = 'N'

        return writerow

    def make_spl_rows(self):
        rows = []
        for lineitem in self.lineitem_set.all():
            writerow = {}
            writerow['type'] = 'SPL'
            writerow['ID'] = ''
            writerow['trnstype'] = 'CASH SALE'
            writerow['date'] = self.timestamp.date()
            writerow['account'] = lineitem.item.income_account
            writerow['name'] = ''
            writerow['class'] = lineitem.item.qb_class
            writerow['amount'] = -1 * lineitem.amount
            writerow['docnum'] = ''
            writerow['memo'] = 'Items sold to %s (by %s)' % (self.buyer.full_name, self.seller.get_full_name())
            writerow['clear'] = 'N'
            writerow['f1'] = -1 * lineitem.quantity
            writerow['f2'] = lineitem.item.cost
            prefix = types[lineitem.item.item_code[0:lineitem.item.item_code.find('-')]]
            writerow['f3'] = "%s:%s" % (prefix, lineitem.item.item_code)
            writerow['f4'] = self.paymeth
            writerow['f5'] = ''

            rows.append(writerow)

        return rows



class QBImportFile:

    naming_format = 'Sales receipt import - %Y-%m-%d @ %H-%M-%S.iif'

    def __init__(self):
        now = datetime.now().strftime(QBImportFile.naming_format)
        self.iif_file = open(now, 'wb')
        self.iif_file.write("!TRNS	TRNSID	TRNSTYPE	DATE	ACCNT	NAME	CLASS	AMOUNT	DOCNUM	MEMO	CLEAR	TOPRINT	NAMEISTAXABLE	ADDR1	ADDR2	ADDR3	ADDR4	ADDR5\n")
        self.iif_file.write("!SPL	SPLID	TRNSTYPE	DATE	ACCNT	NAME	CLASS	AMOUNT	DOCNUM	MEMO	CLEAR	QNTY	PRICE	INVITEM	PAYMETH	TAXABLE	VALADJ	REIMBEXP	EXTRA\n")
        self.iif_file.write("!ENDTRNS\n")
        fields = ['type', 'ID', 'trnstype', 'date', 'account', 'name', 'class', 'amount', 'docnum', 'memo', 'clear',
                  'f1', 'f2', 'f3', 'f4', 'f5', 'f6', 'f7', 'f8']
        self.writer = csv.DictWriter(self.iif_file, fields, delimiter="	", quoting=csv.QUOTE_NONE)
        self.receipts = []

    def add_receipt(self, receipt):
        if type(receipt) is IIFReceiptWrapper:
            self.receipts.append(receipt)
        elif type(receipt) is Receipt:
            self.receipts.append(IIFReceiptWrapper.objects.get(receipt.pk))
        else:
            raise ValueError('Receipt must be either Receipt or IIFReceiptWrapper')

    def process_receipts(self):
        for iif_receipt in self.receipts:
            self.writer.writerow(iif_receipt.make_trns_row())
            self.writer.writerows(iif_receipt.make_spl_rows())
            self.writer.writerow({'type': 'ENDTRNS'})

    def do_receipts_for_today(self):
        today = datetime.now()
        yesterday = today - timedelta(days=1)
        for receipt in IIFReceiptWrapper.objects.filter(timestamp__range=(yesterday, today)):
            self.receipts.append(receipt)
        self.process_receipts()
        self.close()

    def close(self):
        self.iif_file.close()