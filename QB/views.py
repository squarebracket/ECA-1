from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import render
from django.db import IntegrityError
from core.models import TaxCode, Division, BudgetLine, FiscalYear, Transaction, LineItem, Account
from Seller.models import Receipt
import qb2
import requests
import gspread
import datetime
import time
from decimal import *
import logging
logger = logging.getLogger('gspread')
import QuickbooksConnection as qbc


OUT_URL = 'https://spreadsheets.google.com/feeds/list/1FHBNGDpE09avt0NTsepqSdTYe86rnqITbH0JsFD-aA4/3/private/full'
IN_URL = 'https://spreadsheets.google.com/feeds/list/1FHBNGDpE09avt0NTsepqSdTYe86rnqITbH0JsFD-aA4/4/private/full'
TRANS_URL = 'https://spreadsheets.google.com/feeds/list/1FHBNGDpE09avt0NTsepqSdTYe86rnqITbH0JsFD-aA4/5/private/full'


class Token(object):

    def __init__(self, access_token):
        self.access_token = access_token

@login_required()
def do_spreadsheet(request):
    FROM_DATE = '2014-05-01'
    TO_DATE = '2014-12-25'

    social = request.user.social_auth.get(provider='google-oauth2')
    gc = gspread.authorize(Token(social.extra_data['access_token']))
    ss = gc.open_by_key('1OC7WUKfpnxfYHjyPVcY1xlRKmXbkqX7riawSHhlRFXU')
    sheet = ss.sheet1

    societies = sheet.col_values(1)
    keys = sheet.col_values(2)
    ss_keys = {}
    for i in range(0, len(societies)):
        ss_keys[societies[i]] = keys[i]

    qb2.qbc = qb2.QuickBooksConnection
    qb2.qbc.open()
    # qb2.QBAccountQuery()
    all_t = qb2.QBReport()
    class_reports = {}

    for society in societies:
        class_report = qb2.QBTxnReportByClass(society, FROM_DATE, TO_DATE)
        class_reports[society] = class_report

    qb2.qbc.close()

    for (society, class_report) in class_reports.iteritems():
        intsersect = set(class_report.transactions.keys()) & set(all_t.transactions.keys())
        for txn_id in intsersect:
            class_report.set_txn(all_t[txn_id])
        try:
            society_ss = gc.open_by_key(ss_keys[society])
        except gspread.exceptions.SpreadsheetNotFound as e:
            print ss_keys[society]
            raise e

        money_out = society_ss.worksheet('Money Out')
        update_ss(money_out, class_report.txn_list_expense())

        money_in = society_ss.worksheet('Money In')
        update_ss(money_in, class_report.txn_list_income())

    # (out_txns, in_txns) = qb2.do_stuff(societies)
    #
    # money_out = ss.worksheet('Money Out')
    # update_ss(money_out, out_txns)
    #
    # money_in = ss.worksheet('Money In')
    # update_ss(money_in, in_txns)
    return HttpResponse()


def update_ss(ss, txns):
    if len(txns) > ss.row_count - 1:
        ss.add_rows(len(txns) - ss.row_count + 1)
    cell_range = ss.range("A2:I%i" % (len(txns)+1,))
    txn_number = 0
    for txn in txns:
        values_to_append = (
            txn.budget_line,
            '=iferror(vlookup(A2,Overview!A$3:B,2,False),"")',
            txn.date,
            txn.ref_num,
            txn.name,
            txn.total,
            txn.memo,
            '',
            txn.status
        )
        for i in range(0, len(values_to_append)):
            j = txn_number * len(values_to_append) + i
            cell_range[j].value = values_to_append[i]
        txn_number += 1

        # money_out.append_row(values_to_append)
    ss.update_cells(cell_range)


# TODO: MAKE SURE SOCIETY 'OTHER' BUDGET LINES ARE ALWAYS CREATED
@login_required()
def tester(request):

    try:
        FROM_DATE = '2014-05-01'
        TO_DATE = '2014-12-25'

        # societies = ['ASHRAE', 'CASI', 'CSCE', 'CSME', 'CUBES', 'EngGames', 'EWB', 'IEEE', 'IIE',
        #              'NSBE', 'SAE', 'SCS', 'SEC', 'Space Concordia', 'WIE']
        societies = ['CASI', 'EngGames']

        start = time.clock()
        all_t = qb2.QBReport()
        end = time.clock()
        print 'Execution of QBReport took: %s' % (end-start)
        class_reports = {}

        for society in societies:
            start = time.clock()
            class_report = qb2.QBTxnReportByClass(society, FROM_DATE, TO_DATE)
            end = time.clock()
            print 'Society transaction report for %s took: %s' % (society, end-start)
            class_reports[society] = class_report

        for (society, class_report) in class_reports.iteritems():
            intersect = set(class_report.transactions.keys()) & set(all_t.transactions.keys())
            for txn_id in intersect:
                class_report.set_txn(all_t[txn_id])
                updates = {'date': all_t[txn_id].date, "ref_num": all_t[txn_id].ref_num,
                           'qb_transaction_type': all_t[txn_id].txn_type}
                try:
                    (t, c) = Transaction.objects.update_or_create(qb_id=all_t[txn_id].txn_id, defaults=updates)
                except IntegrityError:
                    print all_t[txn_id].date, all_t[txn_id].txn_type
                    raise

                for line_item in class_report.transactions[txn_id]:
                    try:
                        society = Division.objects.get(name=line_item.society)
                        budget_line = BudgetLine.objects.get_by_full_name(full_name=line_item.budget_line, division=society)
                        tax_code = TaxCode.objects.get(qb_id=line_item.sales_tax_code)
                        amount_with_tax = Decimal(1+tax_code.rate)*Decimal(line_item.amount_without_tax)
                        updates = {'transaction': t, 'qb_parent_id': all_t[txn_id].txn_id, 'memo': line_item.memo,
                                  'account': line_item.account, 'division': society, 'budget_line': budget_line,
                                  'tax_code': tax_code, 'tax_included': False,
                                  '_amount_without_tax': line_item.amount_without_tax,
                                  '_amount_with_tax': amount_with_tax}
                        (L, c) = LineItem.objects.update_or_create(qb_id=line_item.txn_id, defaults=updates)
                    except (Division.DoesNotExist, BudgetLine.DoesNotExist, TaxCode.DoesNotExist, Account.DoesNotExist) as e:
                        print e
                        print "Division: %s - Budget line: %s - Tax Code: %s - Account: %s" % \
                            (line_item.society, line_item.budget_line, line_item.sales_tax_code, line_item.account)
                        raise

    except Exception:
        raise
    return HttpResponse()


# TODO: Make this not dumb.
def refresh_accounts(request):
    """
    Updates all :class:`core.Account`s from QuickBooks.

    .. warning::
       This function does not delete any :class:`Account` that exists in the
       database but not in QuickBooks.
    """
    qbc = qb2.QuickBooksConnection()
    try:
        qb2.QBAccountQuery()
    finally:
        qbc.close()
    return HttpResponse()


def refresh_tax_codes(request):

    qbc = qb2.QuickBooksConnection()
    getcontext().prec = 10
    try:
        for qb_tax_code in qb2.QBRqRs('taxcode_query.xml').all():
            params = {
                'code': qb_tax_code.name,
                'qb_id': qb_tax_code.list_id,
                'qb_edit_sequence': qb_tax_code.edit_sequence,
                'description': qb_tax_code.desc,
                'rate': Decimal('0.00000')
            }
            print params['code']
            if 'item_sales_tax_ref' in qb_tax_code:
                print 'has tax'
                d = {'list_id': qb_tax_code.item_sales_tax_ref.list_id}
                print d
                group_taxcode = qb2.QBRqRs('item_group_taxcode_query.xml', **d).get()
                print 'got group taxcode'
                for item_taxcode in group_taxcode.item_sales_tax_ref:
                    # print item_taxcode
                    print 'got group item tax code: %s' % item_taxcode.list_id
                    item_taxcode2 = qb2.QBRqRs('item_taxcode_query.xml', list_id=item_taxcode.list_id).get()
                    print 'got item tax code'
                    params['rate'] += (Decimal(item_taxcode2.tax_rate) / Decimal(100))
                        # print params['rate']
                        # print item_taxcode2.tax_rate

            print params
            # print params['rate']
            (dj_tax_code, created) = TaxCode.objects.update_or_create(qb_id=qb_tax_code.list_id, defaults=params)
            dj_tax_code.save()

            # for a in group_taxcode:
            #     print a.soup
            # for qb_item_group_tax_code in qb2.QBRqRs('item_group_taxcode_query.xml', **d):
            #     print qb_item_group_tax_code
    finally:
        qbc.close()
    return HttpResponse()


def refresh_budget_lines(request):

    """
    Updates the budget lines in the database from society spreadsheets.

    It also grabs the list_id of the budget lines from QuickBooks, creating the classes in
    QuickBooks if necessary.

    :param request: HttpRequest
    :return: HttpResponse
    """

    from datetime import date
    today = date.today()
    fiscal_year = FiscalYear.objects.get(start__lte=today, end__gte=today)

    social = request.user.social_auth.get(provider='google-oauth2')
    gc = gspread.authorize(Token(social.extra_data['access_token']))
    ss = gc.open_by_key('1OC7WUKfpnxfYHjyPVcY1xlRKmXbkqX7riawSHhlRFXU')
    sheet = ss.sheet1

    societies = sheet.col_values(1)
    keys = sheet.col_values(2)
    ss_keys = {}
    for i in range(0, len(societies)):
        ss_keys[societies[i]] = keys[i]

    with qbc.session():
        for (society, ss_key) in ss_keys.iteritems():
            if society != 'SAE':
                qb_base_class = qb2.QBRqRs('class_query.xml', full_name=society).get()
                if qb_base_class:
                    params = {
                        'name': qb_base_class.name,
                        'qb_edit_sequence': qb_base_class.edit_sequence,
                    }
                    (base_division, c) = Division.objects.update_or_create(qb_id=qb_base_class.list_id, defaults=params)
                # create the 'Other' budget line for each society
                (other, c) = BudgetLine.objects.update_or_create(qb_id=qb_base_class.list_id, name='Other',
                                                                 qb_edit_sequence=qb_base_class.edit_sequence,
                                                                 division=base_division, year=fiscal_year)
                society_ss = gc.open_by_key(ss_key)
                ss = society_ss.worksheet('Overview')
                cell_range = ss.range("A3:B%i" % ss.row_count)
                budget_lines = zip(cell_range[0::2], cell_range[1::2])
                for (budget_line, budget_line_type) in budget_lines:
                    if budget_line_type.value == 'Total' or budget_line.value.strip() == '':
                        continue
                    full_name = society
                    parts = budget_line.value.split(' - ')
                    parent = None
                    for part in parts:
                        full_name = "%s:%s" % (full_name, part)
                        try:
                            qb_class = qb2.QBRqRs('class_query.xml', full_name=full_name).get()
                        except qb2.DoesNotExist:
                            qb_class = qb2.QBRqRs('class_add.xml', name=part, parent=parent).add()
                        params = {
                            'name': part,
                            'qb_edit_sequence': qb_base_class.edit_sequence,
                            'year': fiscal_year,
                            'division': base_division,
                            'parent_budget_line': parent,
                        }
                        (budget_line, created) = BudgetLine.objects.update_or_create(qb_id=qb_class.list_id, defaults=params)
                        parent = budget_line

    return HttpResponse()


def add_sales_receipt(request, receipt):
    assert type(receipt) == Receipt


def add_sales_to_quickbooks(request):

    qbc = qb2.QuickBooksConnection()
