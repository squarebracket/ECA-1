from django.conf import settings
import logging
import win32com.client
import pythoncom
from django.template import Template, Context
from django.template.loader import get_template
from contextlib import contextmanager
import inspect

logger = logging.getLogger(__name__)

com_handler = None
ticket = None
qb_file_setting = settings.QB_FILE
try:
    default_application_name = settings.QB_APPLICATION_NAME
except AttributeError:
    default_application_name = 'Test qbXML Request'
status = None


@contextmanager
def open_connection():
    try:
        open_qbc()
        yield
    finally:
        close()


@contextmanager
def session():
    global status
    try:
        open_qbc()
        begin_session()
        yield
    finally:
        end_session()
        close()
        status = None


def open_qbc(application_name=default_application_name):
    """
    Opens a COM connection to the QuickBooks API, registering itself as the
    application *application_name*.

    Internally, it registers the `QBXMLRP2.RequestProcessor` COM object to
    this module's :attr:`com_handler` attribute.

    If no Exceptions are raised when attempting to register the COM object, a
    connection is opened with QuickBooks. This connection remains open until
    :func:`close` is called. For that reason, it is suggested to use the
    context manager (`with QuickBooksConnection.session():`) so that the
    connection is always automatically closed.

    :param str application_name: Name used when asking QuickBooks for API Access
    """
    global com_handler, status
    if com_handler is not None:
        # We are already initialized
        return

    pythoncom.CoInitialize()
    com_handler = win32com.client.Dispatch("QBXMLRP2.RequestProcessor")
    logger.debug('calling OpenConnection')
    com_handler.OpenConnection2('', application_name, 1)
    logger.debug('OpenConnection called')
    status = 'Open'


def begin_session(qb_file=qb_file_setting):
    """
    Begins a session with the QuickBooks API.

    Sets the module attribute :attr:`ticket` for keeping track of the session.

    .. note:: This is where most of the overhead is.

    :param str qb_file: Path to the QuickBooks file to open.
    """

    global ticket, status
    logger.debug('Calling BeginSession')
    ticket = com_handler.BeginSession(qb_file, 0)
    logger.debug('BeginSession called')
    status = 'Locked'


def query(qbxml_query):
    qbxml_query = """
<?qbxml version="6.0"?>
<QBXML>
<QBXMLMsgsRq onError="stopOnError">
%s
</QBXMLMsgsRq>
</QBXML>""" % qbxml_query
    logger.debug('Sending query to QuickBooks')
    try:
        response = com_handler.ProcessRequest(ticket, qbxml_query)
    except pythoncom.com_error as e:
        print e.__dict__
        raise

    logger.debug('Response received from QuickBooks')
    return response


def end_session():
    """
    Closes the session referred to by :attr:`ticket`.
    """
    global ticket, status
    if ticket:
        logger.debug('Calling EndSession')
        com_handler.EndSession(ticket)
        logger.debug('EndSession called')
        ticket = None
        status = 'Open'


def find_persons(name):
    c = Context({'name': name})
    qbxml_query = get_template('find_person.xml').render(c)
    return query(qbxml_query)


def find_account(name):
    c = Context({'name': name})
    qbxml_query = get_template('find_account.xml').render(c)
    return query(qbxml_query)


def close():
    """
    Closes the connection referred to by :attr:`com_handler`.
    """
    global com_handler, status
    logger.debug('Calling CloseConnection')
    com_handler.CloseConnection()      # Close the connection
    logger.debug('CloseConnection called')
    print 'CloseConnection called'
    pythoncom.CoUninitialize()
    print 'CoUninitialize called'
    status = None
    com_handler = None