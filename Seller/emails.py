from django.conf import settings
from gmail import GMail, Message


class ReceiptEmail(object):

    email_template = '''Hello,

Attached is your purchase receipt

Thank you,

Engineering & Computer Science Association
Concordia University
1455 de Maisonneuve Ouest, Suite H-838
Tel. 514-848-2424 ext. 7408
Fax. 514-848-4535
office@ecaconcordia.ca
www.ecaconcordia.ca'''

    email_format = "%(name)s <%(email)s>"

    def __init__(self, receipt, pdf):
        self.to_name = receipt.buyer.full_name
        self.to_email = receipt.buyer.email
        self.to_field = ReceiptEmail.email_format % {'name': self.to_name, 'email': self.to_email}
        self.from_name = settings.RECEIPT_EMAILER_NAME
        self.from_email = settings.RECEIPT_EMAILER_EMAIL
        self.from_field = ReceiptEmail.email_format % {'name': self.from_name, 'email': self.from_email}
        self.pdf = pdf
        self.is_authenticated = False
        self.email_handler = None
        self.email = None

    def login(self):
        self.email_handler = GMail(self.from_field, settings.RECEIPT_EMAILER_PASSWORD)

    def create_email(self):
        self.email = Message(subject="Receipt", to=self.to_field, text=ReceiptEmail.email_template, attachments=[self.pdf.filename, ])

    def send(self):
        if not self.is_authenticated:
            self.login()
        if not self.email:
            self.create_email()
        if settings.DEBUG is False:
            self.email_handler.send(self.email)


