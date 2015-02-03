from django.conf.urls import patterns, include, url
from QB.views import do_spreadsheet, refresh_accounts, refresh_tax_codes, refresh_budget_lines, tester

urlpatterns = patterns('',
    url(r'^update/spreadsheets/$', do_spreadsheet),
    url(r'^update/accounts$', refresh_accounts),
    url(r'^update/tax_codes$', refresh_tax_codes),
    url(r'^update/budget_lines$', refresh_budget_lines),
    url(r'test$', tester),
)