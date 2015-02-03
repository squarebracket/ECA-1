from django.db import models
from django.utils.timezone import now


class FiscalYear(models.Model):
    start = models.DateField()
    end = models.DateField()

    def __unicode__(self):
        return "%s-%s" % (self.start.year, self.end.year)


class Division(models.Model):
    name = models.CharField(max_length=32)
    parent_division = models.ForeignKey('Division', null=True, blank=True)
    is_active = models.BooleanField(default=True)
    qb_id = models.CharField(max_length=36, null=True)
    qb_edit_sequence = models.CharField(max_length=16, null=True)

    @property
    def full_name(self):
        if self.parent_division is not None:
            return "%s : %s" % (self.parent_division.full_name, self.name)
        return self.name

    def __unicode__(self):
        return self.full_name


class Tag(models.Model):
    name = models.CharField(max_length=50)
    parent_tag = models.ForeignKey('Tag', null=True, blank=True)

    def __unicode__(self):
        return self.name


class BudgetLineManager(models.Manager):
    def get_by_full_name(self, full_name, division):
        parts = full_name.split(' - ')
        parent = None
        for part in parts:
            parent = self.get(division=division, name=part, parent_budget_line=parent)
        return parent

    def leaf_nodes(self):
        return self.filter(budgetline=None)


class BudgetLine(models.Model):
    name = models.CharField(max_length=100)
    year = models.ForeignKey(FiscalYear)
    parent_budget_line = models.ForeignKey('BudgetLine', null=True, blank=True)
    division = models.ForeignKey(Division)
    tags = models.ManyToManyField(Tag, blank=True)
    qb_id = models.CharField(max_length=36, null=True, blank=True)
    qb_edit_sequence = models.CharField(max_length=16, null=True, blank=True)

    objects = BudgetLineManager()

    @property
    def full_name(self):
        if self.parent_budget_line is not None:
            return "%s : %s" % (self.parent_budget_line.full_name, self.name)
        return self.name

    @property
    def is_tail(self):
        raise Exception

    def __unicode__(self):
        # return u"%s :: %s" % (self.division.full_name, self.full_name)
        return self.full_name


class Transaction(models.Model):

    date = models.DateField()
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    ref_num = models.CharField(max_length=50, null=True, blank=True)
    qb_id = models.CharField(max_length=36, null=True, unique=True)
    qb_edit_sequence = models.CharField(max_length=16, null=True)
    qb_transaction_type = models.CharField(max_length=20)
    cleared = models.BooleanField(default=False)
    tags = models.ManyToManyField(Tag, blank=True)
    split_account = models.ForeignKey('Account')
    total_amount = models.DecimalField(max_digits=20, decimal_places=5)
    total_memo = models.CharField(max_length=1024)

    def validate(self):
        total = 0
        for item in self.lineitem_set.all():
            total += item.accounting_amount
        return total == self.split_amount

    def save(self, *args, **kwargs):
        if self.date is None:
            self.date = now()
        if self.split_account_id is None:
            self.split_account = Account.objects.get(number=1160)
        super(Transaction, self).save(*args, **kwargs)

    def __unicode__(self):
        return "%s %s" % (self.qb_transaction_type, self.ref_num)
    #     return self.qb_id


# TODO: MAKE THIS TIME DEPENDANT OR WHATEVER
class TaxCode(models.Model):
    code = models.CharField(max_length=3)
    description = models.CharField(max_length=31, null=True, blank=True)
    rate = models.DecimalField(decimal_places=10, max_digits=10, help_text="Tax percentage as a decimal number")
    qb_id = models.CharField(max_length=36)
    qb_edit_sequence = models.CharField(max_length=16)

    def __unicode__(self):
        return self.code


class Account(models.Model):

    class AccountType(object):
        BANK = 0
        ACCOUNTS_RECEIVABLE = 1
        PREPAID_EXPENSES = 2
        NON_DEPOSITED_FUNDS = 3
        INVENTORY_ASSET = 4
        FIXED_ASSET = 5
        ASSET_ACCRUAL = 6
        OTHER_ASSET = 7
        ACCOUNTS_PAYABLE = 8
        LIABILITY_ACCRUAL = 9
        TAX_PAYABLE = 10
        OPENING_BALANCE = 11
        RETAINED_EARNINGS = 12
        INCOME = 13
        COGS = 14
        PAYROLL = 15
        EXPENSE = 16
        NON_POSTING = 17

        ACCOUNT_CHOICES = (
            (BANK, 'Bank'),
            (ACCOUNTS_RECEIVABLE, 'Accounts Receivable'),
            (PREPAID_EXPENSES, 'Prepaid Expenses'),
            (NON_DEPOSITED_FUNDS, 'Undeposited Funds'),
            (INVENTORY_ASSET, 'Inventory Asset'),
            (FIXED_ASSET, 'Fixed Asset'),
            (ASSET_ACCRUAL, 'Asset Accrual'),
            (OTHER_ASSET, 'Other Asset'),
            (ACCOUNTS_PAYABLE, 'Accounts payable'),
            (LIABILITY_ACCRUAL, 'Liability Accrual'),
            (TAX_PAYABLE, 'Tax Payable'),
            (OPENING_BALANCE, 'Opening Balance'),
            (RETAINED_EARNINGS, 'Retained Earnings'),
            (INCOME, 'Income'),
            (COGS, 'Cost of Goods Sold'),
            (PAYROLL, 'Payroll'),
            (EXPENSE, 'Expense'),
            (NON_POSTING, 'Non-Posting'),
        )

        ASSET_GROUP = 1
        LIABILITY_GROUP = 2
        EQUITY_GROUP = 3
        INCOME_GROUP = 4
        EXPENSE_GROUP = 5
        NON_POSTING_GROUP = 6

        asset_accounts = (BANK, ACCOUNTS_RECEIVABLE, PREPAID_EXPENSES, NON_DEPOSITED_FUNDS, INVENTORY_ASSET,
                          FIXED_ASSET, ASSET_ACCRUAL)
        liability_accounts = (ACCOUNTS_PAYABLE, LIABILITY_ACCRUAL, TAX_PAYABLE)
        equity_accounts = (OPENING_BALANCE, RETAINED_EARNINGS)
        income_accounts = (INCOME, )
        expense_accounts = (COGS, PAYROLL, EXPENSE)
        non_posting_accounts = (NON_POSTING, )

    class AccountType2(object):
        INCOME_EXPENSE = 0
        BALANCE_SHEET = 1

    name = models.CharField(max_length=31)
    parent_account = models.ForeignKey('Account', null=True, blank=True)
    number = models.PositiveIntegerField(verbose_name='Accounting Number', unique=True)
    account_type = models.PositiveSmallIntegerField(choices=AccountType.ACCOUNT_CHOICES)
    is_active = models.BooleanField(default=True)
    description = models.TextField(null=True, blank=True)
    bank_account_number = models.CharField(max_length=50, verbose_name='Bank Account Number', null=True, blank=True)
    tags = models.ManyToManyField(Tag, blank=True)
    qb_list_id = models.CharField(max_length=36, unique=True)
    qb_edit_sequence = models.CharField(max_length=16)

    @property
    def full_name(self):
        if self.parent_account is not None:
            return "%s : %s" % (self.parent_account.full_name, self.name)
        return self.name

    @property
    def account_group(self):
        if self.account_type in Account.AccountType.asset_accounts:
            return Account.AccountType.ASSET_GROUP
        elif self.account_type in Account.AccountType.liability_accounts:
            return Account.AccountType.LIABILITY_GROUP
        elif self.account_type in Account.AccountType.equity_accounts:
            return Account.AccountType.EQUITY_GROUP
        elif self.account_type in Account.AccountType.income_accounts:
            return Account.AccountType.INCOME_GROUP
        elif self.account_type in Account.AccountType.expense_accounts:
            return Account.AccountType.EXPENSE_GROUP
        else:
            raise NotImplementedError  # TODO: replace with proper exception

    def __unicode__(self):
        return u"%i - %s" % (self.number, self.name)


class LineItem(models.Model):

    transaction = models.ForeignKey(Transaction)

    qb_id = models.CharField(max_length=36)
    qb_parent_id = models.CharField(max_length=36)
    qb_edit_sequence = models.CharField(max_length=16)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    memo = models.CharField(max_length=1024)
    account = models.ForeignKey(Account, null=True, blank=True)

    division = models.ForeignKey(Division)
    budget_line = models.ForeignKey(BudgetLine)
    tags = models.ManyToManyField(Tag, blank=True)

    tax_code = models.ForeignKey(TaxCode)
    tax_included = models.BooleanField(default=False)
    _tax_amount = models.DecimalField(max_digits=20, decimal_places=5, null=True)
    _amount_without_tax = models.DecimalField(max_digits=20, decimal_places=5, null=True)
    _amount_with_tax = models.DecimalField(max_digits=20, decimal_places=5, null=True)
    _amount_entered = models.DecimalField(max_digits=20, decimal_places=5, null=True, verbose_name='Amount')

    @property
    def date(self):
        return self.transaction.date

    @property
    def ref_num(self):
        return self.ref_num

    @property
    def amount(self):
        return self._amount_with_tax

    @property
    def accounting_amount(self):
        return self.amount

    def __unicode__(self):
        return self.qb_id

    class Meta:
        permissions = (("can_assign_account", "Can assign an account to Line Items"),)


class PaymentMethod(models.Model):
    name = models.CharField(max_length=31)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    type = models.CharField(max_length=50)

    qb_id = models.CharField(max_length=36)
    qb_edit_sequence = models.CharField(max_length=16)


class Item(models.Model):
    name = models.CharField(max_length=150)
    cost = models.DecimalField(decimal_places=2, max_digits=5)
    item_code = models.CharField(max_length=25)
    income_account = models.ForeignKey(Account)
    budget_line = models.ForeignKey(BudgetLine)
    division = models.ForeignKey(Division)

    qb_id = models.CharField(max_length=36)
    qb_edit_sequence = models.CharField(max_length=16)

    def __unicode__(self):
        return self.name