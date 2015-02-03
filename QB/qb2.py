#!usr/bin/python
import xml.etree.ElementTree
from datetime import datetime

from django.template import Template, Context
from django.template.loader import get_template
from django.conf import settings

from UnicodeCSV import UnicodeDictWriter
import bs4
from core.models import Account
from people.models import Person, Student
from Seller.models import Receipt, ReceiptLineItem
from core.models import Transaction as CoreTransaction, LineItem as CoreLineItem, BudgetLine
from Requisitions.models import Reimbursement, DirectPayment, InvoiceRequest
import re
import time
import QuickbooksConnection as qbc


# TEMPLATE_DIRS=('C:\\Users\\chuck\\Py', )
# settings.configure(TEMPLATE_DEBUG=True, )

if __name__ == "__main__":
    settings.configure(TEMPLATE_DEBUG=True, )


template_files = ['sales_receipt', 'person_change', 'find_person', 'create_customer', 'find_account', 'custom_report',
                  'bill_query', 'bill_payment_check_query', 'check_query', 'payment_query', 'txn_query', 'a_query',
                  'cheques_and_deposits_query', 'host_query', 'custom_report2', 'data_ext_def_ref',
                  'account_query']

templates = {}
import os
os.chdir(r'C:\Users\chuck\PycharmProjects\Inventory\QB\templates')

for template in template_files:
    f = open('%s.xml' % template, 'r')
    templates[template] = Template(f.read())
    f.close()

os.chdir(r'C:\Users\chuck\PycharmProjects\Inventory')
EHD_BLK_L = "Store Apparel:Sweater - with logo:Hoodie:EHD-BLK-L"


class QBTxnRet(object):

    def __init__(self, xml_string):
        self.qb_xml = xml.etree.ElementTree.fromstring(xml_string)


class QBAddress(object):

    def __init__(self, xml=None):
        if xml is not None:
            # TODO: typechecking on xml
            self.addr1 = xml.find('Addr1').string
            self.addr2 = xml.find('Addr2').string
            self.city = xml.find('City').string
            self.state = xml.find('State').string
            self.postal_code = xml.find('PostalCode').string
            if xml.find('Country'):
                self.country = xml.find('Country').string
        else:
            self.addr1 = None
            self.addr2 = None
            self.city = None
            self.state = None
            self.postal_code = None
            self.country = None


class QBPerson(object):

    def __init__(self, person_object_or_xml):
        if isinstance(person_object_or_xml, Person):
            person = person_object_or_xml
            self.person_type = 'Customer'
            self.name = person.full_name
            self.first_name = person.first_name
            self.last_name = person.last_name
            self.address = QBAddress()
            self.address.addr1 = person.full_name
            addr2, addr3, addr5 = person.address.rsplit('\n', 2)

            # self.address.addr2 = person.address_line
            # self.address.city = person.address_city
            # self.address.state = person.address_province
            # self.address.country = person.address_country
            # self.address.postal_code = person.postal_code
            self.phone = person.phone
            self.email = person.email
        else:
            xml = person_object_or_xml
            # Todo: typechecking
            self.person_type = xml.name[:-3]
            self.name = xml.find('Name').string
            self.list_id = xml.find('ListID').string
            self.edit_sequence = xml.find('EditSequence').string
            address_xml = xml.find('PostalCode')
            self.phone = None
            self.email = None
            self.address = None
            # print xml.find_all(re.compile('(.*)Address'))
            if address_xml is not None:
                self.address = QBAddress(xml.find(re.compile('(.*)Address')))
            phone_xml = xml.find('Phone')
            if phone_xml is not None:
                self.phone = phone_xml.string
            email_xml = xml.find('Email')
            if email_xml is not None:
                self.email = email_xml.text
            self.soup = xml

    def to_context(self):
        d = self.__dict__
        if 'address' in d:
            d['address'] = self.address.__dict__
        return d

    def rename(self, to_name):
        # query_string = self._change(to_name)
        a = QBRqRs('person_change.xml', list_id=self.list_id, edit_sequence=self.edit_sequence,
                   to_name=to_name, person_type=self.person_type).add()
        return a

    def rename_with_type(self):
        if self.person_type != 'Customer' and self.name[-2:] != ';%s' % self.person_type[0:1]:
            new_name = "%s;%s" % (self.name, self.person_type[0:1])
            a = QBRqRs('person_change.xml', list_id=self.list_id, edit_sequence=self.edit_sequence,
                       name=new_name, person_type=self.person_type).add()
            return a
        else:
            return None

    def create_customer(self):
        # TODO: do error checking (i.e. check to see if name exists)
        # query_string = self._add_customer()
        # print query_string
        # a = QBRqRs(template=None, query_string=query_string).add()
        # return QBPerson(a)
        a = QBRqRs('create_customer.xml', **self.__dict__)
        return a

    # TODO: make generic
    def _change(self, to_name):
        soup_copy = bs4.BeautifulSoup(self.soup.prettify(), 'xml')
        soup_copy.find('%sRet' % self.person_type).name = '%sMod' % self.person_type
        soup_copy.Name.string = to_name
        soup_copy.TimeCreated.decompose()
        soup_copy.TimeModified.decompose()
        soup_copy.VendorAddressBlock.decompose()
        wrap_tag = soup_copy.new_tag('%sModRq' % self.person_type)
        return soup_copy.find('%sMod' % self.person_type).wrap(wrap_tag).prettify()

    def _add_customer(self):
        soup_copy = bs4.BeautifulSoup(self.soup.prettify(), 'xml')
        soup_copy.find('%sRet' % self.person_type).name = 'CustomerAdd'
        if self.person_type != 'Customer' and soup_copy.find('%sAddress' % self.person_type):
            soup_copy.find('%sAddress' % self.person_type).name = 'BillAddress'
        soup_copy.find('ListID').decompose()
        soup_copy.TimeCreated.decompose()
        soup_copy.TimeModified.decompose()
        soup_copy.EditSequence.decompose()
        wrap_tag = soup_copy.new_tag('CustomerAddRq')
        return soup_copy.CustomerAdd.wrap(wrap_tag).prettify()

    def __str__(self):
        return str(self.__dict__)


class QBLineItem(object):
    def __init__(self, name, desc, qty, class_, cost):
        self.name = name
        self.desc = desc
        self.qty = qty
        self.class_ = class_
        self.cost = cost


# TODO: Implement with QBRqRs
class QBSalesReceipt(object):
    TEMPLATE = templates['sales_receipt']

    def __init__(self, person, date, memo='Items sold through counter'):
        if isinstance(person, QBPerson):
            self.person = person
        else:
            raise ValueError
        self.date = date
        self.memo = memo
        self.items = []
        self.stale = False
        self.list_id = None

    def add_lineitem(self, lineitem):
        if isinstance(lineitem, QBLineItem):
            self.items.append(lineitem)
        else:
            raise ValueError

    def add_to_quickbooks_xml(self):
        d = self.__dict__
        # d['items'] = self.items.__dict__
        qbxml = QBSalesReceipt.TEMPLATE.render(Context(d))
        # print qbxml
        return qbxml


class QBRqRs(object):

    def __init__(self, template, query_string=None, **kwargs):
        if not query_string:
            self.template = get_template(template)
            self.context = Context(kwargs)
            self.query_string = self.template.render(self.context)
        else:
            self.template = None
            self.context = None
            self.query_string = query_string
        self.response_string = None
        self._response_soup = None
        self._rs = None
        self.num_returned = None
        self._status_code = None
        self._status_severity = None
        self._status_message = None
        self._rets = None

    def get(self):
        self._query()
        if self.num_returned > 1:
            raise MultipleItemsReturned('More than one Ret object returned')
        elif self.num_returned == 0:
            raise DoesNotExist('None exists for %s' % self.context)
        return self
        # self.__getattr__ = self.single_ret_getattr

    def all(self):
        self._query()
        return self

    def add(self):
        self._query()
        if self.num_returned > 1:
            raise MultipleItemsReturned('More than one Ret object returned... what?')
        # elif self.num_returned == 0:
        #     raise DoesNotExist('None exists for %s' % self.context)
        return self

    def _query(self):
        with qbc.session():
            self.response_string = qbc.query(self.query_string)
        self._response_soup = bs4.BeautifulSoup(self.response_string, "xml")  # Root == <QBXML>
        self._rs = self._response_soup.QBXML.QBXMLMsgsRs.find_all(re.compile(r'(.*)Rs$'))
        if len(self._rs) > 1:
            raise NotImplementedError('More than one Rs object returned')
        self._rs = self._rs[0]
        self._status_check()
        self._rets = [QBXML(ret) for ret in self._rs.find_all(re.compile(r'(.*)Ret'))]
        self.num_returned = len(self._rets)

    def _status_check(self):
        self._status_code = self._rs['statusCode']
        self._status_severity = self._rs['statusSeverity']
        self._status_message = self._rs['statusMessage']
        if self._status_severity == 'ERROR':
            raise QBError(self._status_code, self._status_message)

    @property
    def status_code(self):
        return self._status_code

    def __iter__(self):
        return iter(self._rets)

    # is self.__getattr__ when a single Ret is returned
    def __getattr__(self, item):
        if self.num_returned == 1:
            return getattr(self._rets[0], item)

    def __len__(self):
        return len(self._rets)

    def __getitem__(self, item):
        if type(item) is not int:
            raise TypeError('Key must be an integer')
        # if -1 > item > self.num_returned - 1:
        return self._rets[item]
        # else:
        #     raise IndexError

    def __str__(self):
        if self.num_returned == 1:
            return self._rets[0].soup
        else:
            return self._response_soup


class QBXML(object):

    def __init__(self, soup):
        self.soup = soup

    def _smart_get_attr(self, attr):
        objs = []
        for item in self.soup(attr, recursive=False):
            if item.string:
                objs.append(item.string)
            else:
                objs.append(QBXML(item))

        if len(objs) == 1:
            objs = objs[0]
        elif len(objs) == 0:
            return None
        return objs

    # implemented to keep with standard foo_bar attribute naming scheme
    def __getattr__(self, item):
        item = item.title().replace('_', '').replace('Id', 'ID')
        # if re.match(r'(.*)Ref$', item):
        #     return self._smart_get_attr([item.ListID for item in self.soup(item, recursive=False)])
        ret = self._smart_get_attr(item)
        if ret:
            return ret
        raise

    def __contains__(self, item):
        if item in self.__dict__:
            return True
        elif self._smart_get_attr(item.title().replace('_', '').replace('Id', 'ID')):
            return True
        raise

    def __str__(self):
        return self.soup.prettify()


class Transaction(object):

    STATUS_ATTRIBUTES = ['_cleared', '_paid', '_printed']

    def __init__(self, txn_type=None, status=None, date=None, total=None, ref_num=None, _cleared=None, society=None,
                 budget_line=None, memo=None, name=None, txn_num=None, txn_id=None, _paid=None, _printed=None,
                 _billing=None, _class=None, account=None, sales_tax_code=None, amount_without_tax=None,
                 total_tax=None, parent_txn_id=None, is_balance_sheet=None):
        self.txn_type = txn_type
        self.status = status
        self.date = date
        self.total = total  # TODO: Make less dangerous?
        self.ref_num = ref_num
        self.society = society
        self.budget_line = budget_line
        self.memo = memo
        self.name = name
        self.txn_num = txn_num
        self.txn_id = txn_id
        self._cleared = _cleared
        self._paid = _paid
        self._printed = _printed
        self._billing = _billing
        self._class = _class
        self.cleared = None
        self.account = account
        self.sales_tax_code = sales_tax_code
        self.amount_without_tax = amount_without_tax
        self.total_tax = total_tax
        self.parent_txn_id = parent_txn_id
        self.is_balance_sheet = is_balance_sheet

    def split_class(self):
        try:
            self.society, self.budget_line = self._class.split(':', 1)
            self.budget_line = self.budget_line.replace(':', ' - ')
            # print self.society, self.budget_line
        except ValueError:
            self.society = self._class
            self.budget_line = 'Other'

    def eval_status(self):

        if self.txn_type == 'Deposit':
            if self.account.account_group == Account.AccountType.INCOME_GROUP:
                self.status = 'Deposited'
        elif self.txn_type == 'Invoice':
            if self._paid == 'Paid':  # Cheque Payment is received

                if self._cleared == 'Cleared':  # Cheque has been deposited in (some) account
                    self.status = 'Cheque deposited to an account'
                    # if self.society in self.account:  # Cheque has been deposited to proper account
                    #     self.status = 'Cheque deposited to society account'
                    #     print self.society, self.account
                    # else:  # cheque has been deposited to 'wrong' account
                    #     self.status = 'Cheque deposited - requires transfer'

                else:  # Cheque hasn't been deposited
                    self.status = 'Cheque received but not deposited'

            else:  # Cheque not received
                self.status = 'Cheque not received'

        elif self.txn_type == 'Cheque':
            if self._cleared == 'Cleared':
                self.status = 'Cleared'
            else:
                self.status = 'Printed'

        elif self.txn_type == 'Bill':
            if self._paid == 'Paid':  # bill has been paid (assumed printed)

                if self._cleared == 'Cleared':  # cheque has been deposited by company
                    self.status = 'Cleared'
                else:  # cheque not cleared
                    # if self._printed:
                        self.status = 'Cheque printed'

    def take_attributes_from(self, txn):
        # print "replacing %s (%s) with %s (%s):" % (self.txn_id, self.txn_type, txn.txn_id, txn.txn_type)
        if txn._cleared:
            # print "	Cleared status: %s => %s" % (self._cleared, txn._cleared)
            self._cleared = txn._cleared
        if txn._paid:
            # print "	Paid status: %s => %s" % (self._paid, txn._paid)
            self._paid = txn._paid
        if txn._printed:
            # print "	Printed status: %s => %s" % (self._printed, txn._printed)
            self._printed = txn._printed
        # if self.txn_type == 'Bill' or self.txn_type == 'Invoice':
        if txn.txn_type == 'Bill Pmt -Cheque' or txn.txn_type == 'Payment' or txn.txn_type == 'Cheque':
            # print "	refnum: %s => %s" % (self.ref_num, txn.ref_num)
            # self.ref_num = txn.ref_num
            self.ref_num = txn.ref_num
        # self.total = txn.total
        # print "	memo: %s => %s" % (self.memo, txn.memo)
        # self.memo = txn.memo
        if self.txn_type == 'Deposit':
            pass
            # print "	account: %s => %s" % (self.account, txn.account)
            # self.account = txn.account
        self.eval_status()
        # print "\n"

    def calculate_amount(self):
        if self.total_tax:
            try:
                self.total = float(self.amount_without_tax) + float(self.total_tax)
            except TypeError:
                print "TypeError"
                raise
                # print self.amount_without_tax, self.total_tax
        elif self.sales_tax_code:
            if self.sales_tax_code == '80000004-1232494917':  # Standard GST+QST
                self.total = round(float(self.amount_without_tax) * 1.14975, 5)
            elif self.sales_tax_code == '80000002-1232494917':  # Tax exempt
                self.total = self.amount_without_tax
            elif self.sales_tax_code == '80000001-1232494917':  # GST Only
                self.total = round(float(self.amount_without_tax) * 1.05, 5)
            elif self.sales_tax_code == '80000009-1418319027':  # Ontario
                self.total = round(float(self.amount_without_tax) * 1.13, 5)
            else:
                raise NotImplementedError(self.sales_tax_code)

    @property
    def expense(self):
        if (self.txn_type == 'Check' or self.txn_type == 'Cheque' or self.txn_type == 'General Journal' or
            self.txn_type == 'Bill') and self.total > 0:
            return True
        else:
            return False

    @property
    def income(self):
        if self.txn_type == 'Invoice' or self.txn_type == 'Sales Receipt' and self.total < 0:
            return True
        else:
            return False

    def __str__(self):
        return "%s:%s" % (self.parent_txn_id, self.txn_id)


xml_to_transaction_class_mapping = {
    'Account': 'account',
    'TxnType': 'txn_type',
    'TxnNumber': 'txn_num',
    'TxnID': 'txn_id',
    'Amount': 'amount_without_tax',
    'Date': 'date',
    'RefNumber': 'ref_num',
    'ClearedStatus': '_cleared',
    'Memo': 'memo',
    'Name': 'name',
    'PaidStatus': '_paid',
    'PrintStatus': '_printed',
    'BillingStatus': '_billing',
    'Class': '_class',
    'LatestOrPriorState': 'total_tax',
    'NameContact': 'sales_tax_code',
}


def get_linked_transactions(txn):
    c = Context({'type': txn.txn_type, 'txn_id': txn.parent_txn_id})
    qbxml_query = templates['bill_query'].render(c)
    # print qbxml_query
    response_string = qbc.query(qbxml_query)
    # print response_string
    _response = xml.etree.ElementTree.fromstring(response_string)
    msgs_rs = _response.find('QBXMLMsgsRs')
    bill_query_rs = msgs_rs.find('%sQueryRs' % txn.txn_type)
    bill_rs = bill_query_rs.find('%sRet' % txn.txn_type)
    linked_txns = bill_rs.findall('LinkedTxn')

    if len(linked_txns) == 0:
        return None
    else:
        return linked_txns[0].find('TxnID').text

    # if len(linked_txns) == 1 and txn.total == linked_txns[0].find('Amount').text[1:]:
        # there is a unique payment for this txn
        # TODO: should probably DataExtAdd here
        # return linked_txns[0].find('TxnID').text

    # else:
    #     print txn.total, linked_txns[0].find('Amount').text[1:]
    #     raise NotImplementedError


def write_transactions(society, transactions):
    f = open('%s.csv' % society, 'wb')
    fieldnames = ['budget_line', 'category', 'date', 'ref', 'person/company', 'amount', 'description', 'status', 'type', 'txnid']
    spamwriter = UnicodeDictWriter(f, fieldnames)

    # spamwriter.writeheader()

    for txn in transactions:
        t = {'budget_line': txn.budget_line, 'ref': txn.ref_num, 'date': txn.date, 'person/company': txn.name,
             'amount': txn.total, 'description': txn.memo, 'status': txn.status,
             'type': txn.txn_type, 'txnid': txn.txn_id}
        spamwriter.writerow(t)

    f.close()


# TODO: transition to QBRqRs
class QBReport(object):

    def __init__(self, from_date=None, to_date=None, date_macro='ThisYearToDate', mod_from_date=None, mod_to_date=None,
                 mod_date_macro=None):
        self.template = get_template('custom_report2.xml')
        context = Context({'from_date': from_date, 'to_date': to_date, 'date_macro': date_macro,
                           'mod_from_date': mod_from_date, 'mod_to_date': mod_to_date, 'mod_date_macro': mod_date_macro})
        self.query_string = self.template.render(context)
        with qbc.session():
            self.response_string = qbc.query(self.query_string)
        # print self.xml_string
        qbxml = xml.etree.ElementTree.fromstring(self.response_string)
        msgs_rs = qbxml.find('QBXMLMsgsRs')
        report_query_rs = msgs_rs.find('CustomDetailReportQueryRs')
        report_rs = report_query_rs.find('ReportRet')
        col_data = report_rs.iter('ColDesc')
        report_data = report_rs.find('ReportData')

        column_mapping = {}

        for col in col_data:
            type_xml = col.find('ColType')
            type = type_xml.text
            if type == 'Blank':
                pass
            else:
                column_mapping[col.attrib['colID']] = xml_to_transaction_class_mapping[type]

        self.transactions = {}

        #TODO: implement this properly
        for txn_xml in report_data[1:-1]:  # ignores first row (TextRow) and last row (TotalRow)
            # print txn_xml
            d = {}
            for col_xml in txn_xml:
                d[column_mapping[col_xml.attrib['colID']]] = col_xml.attrib['value']
            txn = Transaction(**d)
            if txn._class:
                txn.split_class()
            txn.calculate_amount()
            self.transactions[txn.txn_id] = txn

        # print self.transactions

    def __getitem__(self, item):
        return self.transactions[item]

    def __setitem__(self, key, value):
        self.transactions[key] = value

    def __delitem__(self, key):
        del self.transactions[key]

    def __iter__(self):
        return self.transactions.iteritems()


# TODO: Transition to QBRqRs
class QBCheque(object):

    def __init__(self, txn_type, ref_number=None, txn_id=None, line_items=True, linked_transactions=False):
        self.template = templates['check_query']
        context = Context({'ref_number': ref_number, 'txn_id': txn_id, 'line_items': line_items,
                           'linked_transactions': linked_transactions, 'txn_type': txn_type})
        self.query_string = self.template.render(context)
        self.response_string = qbc.query(self.query_string)
        qb_xml = xml.etree.ElementTree.fromstring(self.response_string)
        qb_xml_msgs = qb_xml.find('QBXMLMsgsRs')
        query_rs = qb_xml_msgs.find('%sQueryRs' % txn_type)
        query_ret = query_rs.find('%sRet' % txn_type)

        if line_items:
            if txn_type == 'Bill' or txn_type == 'Check':
                lines = query_ret.findall('ExpenseLineRet')
            elif txn_type == 'Invoice':
                lines = query_ret.findall('InvoiceLineRet')
            elif txn_type == 'Deposit':
                lines = query_ret.findall('DepositLineRet')
            elif txn_type == 'SalesReceipt':
                lines = query_ret.findall('SalesReceiptLineRet')
            elif txn_type == 'JournalEntry':
                lines = query_ret.findall('JournalCreditLine')
            else:
                print txn_type
                print self.response_string
                raise NotImplementedError
            lines.extend(query_ret.findall('ItemLineRet'))

            self.line_items = {}
            for line in lines:
                if txn_type == 'Deposit':
                    line_txn_type = line.find('TxnType').text
                    if not line_txn_type == 'Deposit':
                        continue
                line_txn_id = line.find('TxnLineID').text
                try:
                    class_ = line.find('ClassRef').find('FullName').text
                except AttributeError:
                    print self.response_string
                try:
                    line_sales_tax_code = line.find('SalesTaxCodeRef').find('ListID').text
                except AttributeError:
                    # print self.response_string
                    line_sales_tax_code = '80000002-1232494917'
                txn = Transaction(txn_type=txn_type, txn_id=line_txn_id, sales_tax_code=line_sales_tax_code,
                                  _class=class_)
                self.line_items[line_txn_id] = txn

        self.txn = Transaction(txn_type=txn_type, txn_id=txn_id)


# TODO: Transition to QBRqRs
class QBTxnReportByClass(object):

    def __init__(self, class_, from_txn_date, to_txn_date):
        self.template = templates['txn_query']
        self.from_txn_date = from_txn_date
        self.to_txn_date = to_txn_date
        self.class_ = class_
        context = Context({'from_txn_date': self.from_txn_date, 'to_txn_date': self.to_txn_date, 'class': self.class_})
        self.query_string = self.template.render(context)
        with qbc.session():
            self.response_string = qbc.query(self.query_string)
            print self.response_string
            qb_xml = xml.etree.ElementTree.fromstring(self.response_string)
            qb_xml_msgs = qb_xml.find('QBXMLMsgsRs')
            txn_rs = qb_xml_msgs.find('TransactionQueryRs')

            self.cheques = {}
            self.transactions = {}
            self.linked_transactions = {}
            txn_ret = txn_rs.iter('TransactionRet')

            for txn_xml in txn_ret:
                try:
                    name = txn_xml.find('EntityRef').find('FullName').text
                    name_id = txn_xml.find('EntityRef').find('ListID').text
                except AttributeError:
                    name = None
                parent_id = txn_xml.find('TxnID').text
                txn_id = txn_xml.find('TxnLineID').text
                date = txn_xml.find('TxnDate').text
                amount = float(txn_xml.find('Amount').text)
                # ref_num = txn_xml.find('RefNumber').text
                txn_type = txn_xml.find('TxnType').text
                if txn_type == 'Deposit':
                    xml.etree.ElementTree.dump(txn_xml)
                account_id = txn_xml.find('AccountRef').find('ListID').text
                account = Account.objects.get(qb_list_id=account_id)
                # print "%i, %s" % (account.number, account.name)
                try:
                    memo = txn_xml.find('Memo').text
                except AttributeError:
                    memo = None
                t = Transaction(name=name, parent_txn_id=parent_id, txn_id=txn_id, date=date,
                                amount_without_tax=amount, txn_type=txn_type, is_balance_sheet=False, memo=memo,
                                account=account)

                if parent_id not in self.transactions:
                    self.transactions[parent_id] = []
                self.transactions[parent_id].append(t)

                if parent_id not in self.cheques:
                    qb_cheque = QBCheque(txn_type, txn_id=parent_id)
                    self.cheques[parent_id] = qb_cheque

                # print self.cheques[parent_id].response_string
                t.sales_tax_code = self.cheques[parent_id].line_items[txn_id].sales_tax_code
                t.calculate_amount()
                t._class = self.cheques[parent_id].line_items[txn_id]._class
                t.split_class()

                if t.txn_type == 'Bill' or t.txn_type == 'Invoice':
                    linked_id = get_linked_transactions(t)
                    if linked_id and linked_id not in self.linked_transactions:
                        self.linked_transactions[linked_id] = parent_id

    def set_txn(self, txn):
        if txn.txn_id in self.transactions:
            for t in self.transactions[txn.txn_id]:
                t.take_attributes_from(txn)
        elif txn.txn_id in self.linked_transactions:
            self.set_linked_txn(txn)

    def set_linked_txn(self, txn):
        if txn.txn_id in self.linked_transactions:
            txn_id = self.linked_transactions[txn.txn_id]

            for t in self.transactions[txn_id]:
                t.take_attributes_from(txn)

    def txn_list_expense(self):
        transactions = []
        for txn_list in self.transactions.itervalues():
            for txn in txn_list:
                if txn.total > 0:
                    transactions.append(txn)
        return transactions

    def txn_list_income(self):
        transactions = []
        for txn_list in self.transactions.itervalues():
            for txn in txn_list:
                if txn.total < 0:
                    txn.total = abs(txn.total)
                    transactions.append(txn)
        return transactions


# TODO: Transition to QBRqRs
class QBAccountQuery(object):

    QB_TO_DJ_MAP = {
        'Bank': Account.AccountType.BANK,
        'AccountsReceivable': Account.AccountType.ACCOUNTS_RECEIVABLE,
        'FixedAsset': Account.AccountType.FIXED_ASSET,
        'AccountsPayable': Account.AccountType.ACCOUNTS_PAYABLE,
        'Income': Account.AccountType.INCOME,
        'CostOfGoodsSold': Account.AccountType.COGS,
        'Expense': Account.AccountType.EXPENSE,
        'NonPosting': Account.AccountType.NON_POSTING
    }

    def __init__(self):
        self.query_string = templates['account_query'].render(Context())
        with qbc.session():
            self.response_string = qbc.query(self.query_string)
        self.soup = bs4.BeautifulSoup(self.response_string, "xml")
        accounts = self.soup.find_all('AccountRet')

        for account_xml in accounts:
            try:
                account = {}
                qb_list_id = account_xml.ListID.text
                account['name'] = account_xml.find('Name').text
                if account_xml.ParentRef:
                    qb_parent_id = account_xml.ParentRef.ListID.text
                    account['parent_account'] = Account.objects.get(qb_list_id=qb_parent_id)
                account['number'] = int(account_xml.AccountNumber.text)
                if account['number'] == 1499:
                    account['account_type'] = Account.AccountType.NON_DEPOSITED_FUNDS
                elif 1500 <= account['number'] < 1600:
                    account['account_type'] = Account.AccountType.INVENTORY_ASSET
                elif account['number'] == 1300:
                    account['account_type'] = Account.AccountType.PREPAID_EXPENSES
                elif account['number'] == 1800:
                    account['account_type'] = Account.AccountType.ASSET_ACCRUAL
                elif account['number'] == 2200:
                    account['account_type'] = Account.AccountType.LIABILITY_ACCRUAL
                elif 25500 <= account['number'] < 25600:
                    account['account_type'] = Account.AccountType.TAX_PAYABLE
                elif account['number'] == 3000:
                    account['account_type'] = Account.AccountType.OPENING_BALANCE
                elif 6000 <= account['number'] < 7000:
                    account['account_type'] = Account.AccountType.PAYROLL
                else:
                    account['account_type'] = QBAccountQuery.QB_TO_DJ_MAP[account_xml.AccountType.text]
                account['is_active'] = True
                if account_xml.Desc:
                    account['description'] = account_xml.Desc.text
                if account_xml.BankNumber:
                    account['bank_account_number'] = account_xml.BankNumber.text
                account['qb_edit_sequence'] = account_xml.EditSequence.text
                (account, created) = Account.objects.update_or_create(qb_list_id=qb_list_id, defaults=account)
                account.save()
            except Exception:
                print account_xml
                raise


class QBXMLRq(object):

    REQUIRED_CONTEXT = []

    def __init__(self, template_file, **kwargs):

        self._check_context(kwargs)

        context = Context(**kwargs)

        f = open(template_file, 'r')
        self.template = Template(f.read())
        f.close()

        self.request_string = self.template.render(context)
        self.response_string = None

    def _check_context(self, context_vars):
        for (context_var, allowed_type) in self.REQUIRED_CONTEXT:
            if context_var not in context_vars:
                raise MissingContextVariable(context_var, type(self))
            elif allowed_type and type(context_vars[context_var]) is not type(allowed_type):
                raise TypeError('%s is of type %s and not %s' % (context_var,
                                                                 type(context_vars[context_var]),
                                                                 type(allowed_type)))


class QBSalesReceiptAdd(QBXMLRq):
    REQUIRED_CONTEXT = [
        ('entity', Person),
        ('date', None),
    ]


class MissingContextVariable(Exception):

    def __init__(self, var, class_):
        self.message = "Required Context variable '%s' not passed to %s constructor" % (var, class_)


# TODO: Make more exceptions
class QBError(Exception):
    def __init__(self, status_code, status_message):
        self.message = "The QuickBooks SDK threw the following error: " \
                       "'status_message' (Code %s)" % (status_message, status_code)


def create_qb_person(person):

    a = QBRqRs('create_customer.xml', full_name=person.full_name, first_name=person.first_name,
               last_name=person.last_name, )


def get_persons(person_object):

    if not isinstance(person_object, Person):
        raise Exception('Object passed to get_persons is not of type Person')

    base_name = person_object.full_name

    person_regex = re.compile(r'(Customer|Vendor|OtherName)Ret')

    with qbc.session():
        response_string = qbc.find_persons(base_name)
    persons_xml = bs4.BeautifulSoup(response_string, "xml")
    persons = [QBPerson(person) for person in persons_xml.find_all(person_regex)]
    num_people = len(persons)
    if num_people == 1:
        person = persons[0]
        if person.person_type != 'Customer':
            person.rename_with_type()
            print 'Found non-customer person'
            return None
    elif num_people == 0:
        return None
    elif num_people == 2:
        base_name = min(persons[0].name, persons[1].name)
        diff = max(persons[0].name, persons[1].name).replace(base_name, '')
        if len(diff) <= 2:
            customer = None
            for person in persons:
                if person.person_type == 'Customer':
                    customer = person
                person.rename_with_type()
            if customer:
                return customer
            else:
                return None
    else:
        raise MultipleItemsReturned("%i persons returned. Fuck" % num_people)
    # peeps = [QBPerson(xml) for xml in persons_xml.find_all()]
    # print peeps
    # qbc.close()


class DoesNotExist(Exception):
    pass


class MultipleItemsReturned(Exception):
    pass


def add_receipt(receipt):
    receipt_xml = QBRqRs('')


def test_person(l):
    first_name = 'Test'
    last_name = 'Person'
    full_name = 'Test Person'
    addr2, addr3, addr5, postal_code = l.split('\t')
    a = QBRqRs('create_customer2.xml', full_name=full_name, first_name=first_name, last_name=last_name,
               addr2=addr2, addr3=addr3, addr5=addr5, postal_code=postal_code).add()
    print a.status_code
    return a


def benchmark():
    template = get_template('durr.xml')
    a = QBRqRs2('durr.xml',).all(from_date='2013-05-01', to_date='2014-04-30')


class QBRqRs2(object):

    def __init__(self, template=None):
        if not template:
            template = 'generic.xml'
        self.template = get_template(template)
        self.context = None
        self.query_string = None
        self.response_string = None
        self._response_soup = None
        self._rs = None
        self.num_returned = None
        self._status_code = None
        self._status_severity = None
        self._status_message = None
        self._rets = None

    def get(self, **kwargs):

        self._query(kwargs)
        if self.num_returned > 1:
            raise MultipleItemsReturned('More than one Ret object returned')
        elif self.num_returned == 0:
            raise DoesNotExist('None exists for %s' % self.context)
        return self
        # self.__getattr__ = self.single_ret_getattr

    def all(self, **kwargs):
        self._query(**kwargs)
        return self

    def add(self, from_object=None, **kwargs):
        context = {
            'api_transaction_type': 'Add',
            'object': from_object
        }
        # self.context = Context(context)
        # self.query_string = self.template.render(self.context)
        self._query(context)
        if self.num_returned > 1:
            raise MultipleItemsReturned('More than one Ret object returned... what?')
        elif self.num_returned == 0:
            raise DoesNotExist('None exists for %s' % self.context)
        return self

    def _query(self, context):

        self.context = Context(context)
        self.query_string = self.template.render(self.context)
        with qbc.session():
            self.response_string = qbc.query(self.query_string)
        self._response_soup = bs4.BeautifulSoup(self.response_string, "xml")  # Root == <QBXML>
        self._rs = self._response_soup.QBXML.QBXMLMsgsRs.find_all(re.compile(r'(.*)Rs$'))
        if len(self._rs) > 1:
            raise NotImplementedError('More than one Rs object returned')
        self._rs = self._rs[0]
        self._status_check()
        # start = datetime.now()
        self._rets = [QBXML2(ret) for ret in self._rs.find_all(re.compile(r'(.*)Ret'))]
        # end = datetime.now()
        # print "took %s" % (end - start)
        self.num_returned = len(self._rets)

    def _status_check(self):
        self._status_code = self._rs['statusCode']
        self._status_severity = self._rs['statusSeverity']
        self._status_message = self._rs['statusMessage']
        if self._status_severity == 'ERROR':
            raise QBError(self._status_code, self._status_message)

    @property
    def status_code(self):
        return self._status_code

    def __iter__(self):
        return iter(self._rets)

    # is self.__getattr__ when a single Ret is returned
    def __getattr__(self, item):
        if self.num_returned == 1:
            return getattr(self._rets[0], item)
        raise

    def __len__(self):
        return len(self._rets)

    def __getitem__(self, item):
        if type(item) is not int:
            raise TypeError('Key must be an integer')
        # if -1 > item > self.num_returned - 1:
        return self._rets[item]
        # else:
        #     raise IndexError

    def __str__(self):
        if self.num_returned == 1:
            return self._rets[0].soup
        else:
            return self._response_soup


class QBXML2(object):

    def __init__(self, soup):
        self.soup = soup
        # print "\n", "new one"
        # print self.soup
        # print hasattr(self, 'Amount')
        start = datetime.now()
        for child in soup.children:
            # print child, "\n"
            if type(child) is not bs4.element.NavigableString:
                # attr_name =
                if child.string is not None:
                    # if hasattr(self, child.name):
                        # print "%s was %s, is now %s" % (child.name, getattr(self, child.name), child.string)
                    setattr(self, camel_case_to_lower_case(child.name), child.string)
                else:
                    setattr(self, camel_case_to_lower_case(child.name), whatever(child))
                # print child.name, child.string
        end = datetime.now()
        # print "took %s" % (end - start)
        # print self.__dict__
        # for child in soup.descendants:
        #     if type(child) is not bs4.element.NavigableString:
                # print child
                # if hasattr(child, 'string'):
                #     setattr(self, child.name, child.string)
                # else:
                #     setattr(self, child.name, whatever(self, child))

    def _smart_get_attr(self, attr):
        objs = []
        for item in self.soup(attr, recursive=False):
            if item.string:
                objs.append(item.string)
            else:
                objs.append(QBXML(item))

        if len(objs) == 1:
            objs = objs[0]
        elif len(objs) == 0:
            return None
        return objs

    # implemented to keep with standard foo_bar attribute naming scheme
    # def __getattr__(self, item):
    #     item = item.title().replace('_', '').replace('Id', 'ID')
    #     ret = self._smart_get_attr(item)
    #     if ret:
    #         return ret
    #     raise

    def __str__(self):
        return self.soup.prettify()


class whatever(object):

    def __init__(self, thing, *args, **kwargs):
        # print "thing: %s" % thing
        # print "args: %s" % args
        for child in thing.children:
            if type(child) is not bs4.element.NavigableString:
                if child.string is not None:
                    setattr(self, child.name, child.string)
                else:
                    setattr(self, child.name, whatever(child))


if __name__ == "__main__":
    sales_receipt = QBSalesReceiptAdd('sales_receipt.xml')


class SalesReceipt(QBRqRs2):

    def __init__(self, receipt):
        self.receipt = receipt
        super(SalesReceipt, self).__init__(template='sales_receipt.xml')
        qb_customer = get_persons(receipt.buyer)
        if qb_customer is None:
            addr2, addr3, addr5 = receipt.buyer.address.split('\n')
            a = QBRqRs('create_customer2.xml', person=receipt.buyer, addr2=addr2,
                       addr3=addr3, addr5=addr5).add()
            receipt.buyer.qb_list_id = a.list_id
            receipt.buyer.qb_edit_sequence = a.edit_sequence
            receipt.buyer.save()
        self.context_dict = {
            'list_id': receipt.qb_id,
            'amount': receipt.total_amount,
            'split_account': receipt.split_account,
            'buyer': receipt.buyer,
            'date': receipt.date.strftime('%Y-%m-%d'),
            'paymeth': receipt.paymeth,
            'memo': receipt.total_memo,
            'line_items': ReceiptLineItem.objects.filter(transaction=receipt),
        }

    def add(self, **kwargs):
        if self.receipt.qb_id:
            # TODO: Change to Django's IntegrityError maybe?
            raise Exception("Object already exists in QuickBooks")
        # TODO: extend self.context_dict with **kwargs
        self._query(self.context_dict)
        # elif self.num_returned == 0:
        #     raise DoesNotExist('None exists for %s' % self.context)
        self.receipt.qb_id = self.list_id
        self.receipt.qb_edit_sequence = self.edit_sequence
        self.receipt.save()
        print self.receipt.qb_id, self.receipt.qb_edit_sequence
        if self.num_returned > 1:
            raise MultipleItemsReturned('More than one Ret object returned... what?')

        return self


def camel_case_to_lower_case(string):
    new_string = ''
    last_letter = 'A'
    for letter in string:
        if letter.islower():
            new_string += letter
        elif not last_letter.isupper():
            new_string += '_' + letter.lower()
        else:
            new_string += letter.lower()
        last_letter = letter
    return new_string