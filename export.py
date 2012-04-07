#!/usr/bin/env python

import re
import sqlite3
from collections import namedtuple
from datetime import date, timedelta

from mechanize import Browser, ControlNotFoundError
from mechanize import _http
from bs4 import BeautifulSoup
from bs4.element import NavigableString

from lib import make_password, get_credentials, write_step, read_step


Transaction = namedtuple('Transaction', ['date', 'name', 'desc', 'amount'])

logged_in_url = 'https://ib.nab.com.au/nabib/acctInfo_acctBal.ctl'

db = None

def check_url(b, expected_url):

    if b.geturl() != expected_url:
        print('\tExpected URL: ', expected_url)
        print('\tCurrent URL: ', b.geturl())
        return False

    return True


def login():

    creds = get_credentials()
    if not creds:
        return None

    b = Browser()
    b.set_handle_robots(False)
    b.addheaders = [('User-agent', 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.1) Gecko/2008071615 Fedora/3.0.1-1.fc9 Firefox/3.0.1')]

    b.set_handle_equiv(True)
    b.set_handle_gzip(True)
    b.set_handle_redirect(True)
    b.set_handle_referer(True)
    b.set_handle_robots(False)

    # Follows refresh 0 but not hangs on refresh > 0
    b.set_handle_refresh(_http.HTTPRefreshProcessor(), max_time=1)

    # Want debugging messages?
    #b.set_debug_http(True)
    b.set_debug_redirects(True)
    b.set_debug_responses(True)


    print 'Opening main page...'
    b.open('http://www.nab.com.au')
    print 'OK'

    print 'Opening login redir page...'
    b.open('http://www.nab.com.au/cgi-bin/ib/301_start.pl?browser=correct')
    print 'OK'

    print 'Opening real login page...'
    b.open('https://ib.nab.com.au/nabib/index.jsp')
    print 'OK'

    b.select_form(nr=0)
    try:
        webKeyCtrl = b.form.find_control(id='webKey')
        webAlphaCtrl = b.form.find_control(id='webAlpha')
    except ControlNotFoundError:
        print 'Cannot find necessary login controls, quitting'
        return

    webKey = webKeyCtrl.value
    webAlpha = webAlphaCtrl.value
    newPassword = make_password(creds[1], webKey, webAlpha)

    usernameCtrl = b.form.find_control(name='userid')
    passwordCtrl = b.form.find_control(name='password')
    usernameCtrl.value = creds[0]
    passwordCtrl.value = newPassword

    b_data = b.form.find_control(name='browserData')
    b_data.readonly = False
    b_data.value = '1332067415674;z=-660*-600;s=1440x900x24;h=325b2e41;l=en-US;p=MacIntel;i=0;j=7;k=0;c=81d6c46c:,799e53ad:,f67180ac:,c801b011:,9ed81ce8:,68bab54a:,3db529ef,97362cfc;'

    b.form.new_control('text', 'hidden', {'name': 'login', 'value': 'Login'})

    print('Logging in...')
    b.submit()

    if not check_url(b, logged_in_url):
        print('Error logging in.')
        return None

    print('OK')
    return b


Account = namedtuple('Account', ['acc_id', 'acc_type'])


def get_accounts(text):

    soup = BeautifulSoup(text)
    account_divs = soup.select('.acctDetails')
    if len(account_divs) == 0:
        print('\tNo accounts found.')
        return None

    accounts = []
    for div in account_divs:

        name = div.select('a span')[0].text.strip()
        if not name:
            print('No Account name found.')
            return None

        details_div = div.select('.accountNumber')[0]
        bsb = re.findall('BSB: ([\d-]*)', details_div.text)
        acc_no = re.findall('Acct No: ([\d-]*)', details_div.text)

        if not bsb or not acc_no:
            print('Account number of BSB is missing for account \'%s\'' % name)
            return None

        link = div.select('a[href^="javascript:viewTransaction(\'"]')[0]
        params = re.findall("'(.*?)'", link.attrs['href'])
        if len(params) != 2:
            print('\tError: incorrect HREF for account: ', link.attrib['href'])
            return None

        accounts.append({
            'name': name,
            'bsb': bsb[0],
            'acc_no': acc_no[0],
            'params': params
        })

    return accounts


def init_db():

    db = sqlite3.connect('transactions.db')
    db.execute('''
        create table if not exists transactions
              (
                bsb text,
                acc_no text,

                date text,
                details text,

                debit_amount text,
                credit_amount text,

                balance text
              )''')
    return db


def is_account_empty(db, bsb, acc_no):

    cur = db.execute('''
                     select count(bsb) from transactions
                     where bsb = ? and acc_no = ?
                     ''',
                     [bsb, acc_no]
                    )
    row = cur.next()

    return row[0] == 0


def save_transaction(db,

                     bsb,
                     acc_no,

                     date,
                     details,

                     debit_amount,
                     credit_amount,

                     balance
                    ):

    db.execute('insert into transactions values (?, ?, ?, ?, ?, ?, ?)',
               (
                bsb,
                acc_no,

                date,
                details,

                debit_amount,
                credit_amount,

                balance
               )
              )
    db.commit()


def save_transactions(db, bsb, acc_no, transactions):

    for trans in transactions:
        save_transaction(db,

                         bsb,
                         acc_no,

                         trans['date'],
                         trans['details'],

                         trans['debit_amount'],
                         trans['credit_amount'],
                         trans['balance']
                        )


def extract_transactions(content):

    soup = BeautifulSoup(content)
    rows = soup.select('#transactionHistoryTable tbody tr')
    transactions = []

    for row in rows:

        tds = row.select('td')
        detail_lines = list(tds[1].children)
        details = []

        for detail_line in detail_lines:
            if type(detail_line) == NavigableString:
                details.append(detail_line)

        transactions.append({
            'date': tds[0].text,
            'details': '\n'.join(details),
            'debit_amount': tds[2].text,
            'credit_amount': tds[3].text,
            'balance': tds[4].text
        })

    return transactions


def open_account_transactions_page(b, account):

    account_id = account[0]
    account_type = account[1]

    if b.geturl() != logged_in_url:
        print('\tCurrent url is %s, need to open accounts page at %s' %
              (b.geturl(), logged_in_url))
        b.open('https://ib.nab.com.au/nabib/acctInfo_acctBal.ctl')

    print('\tOpening transaction page for account %s... ' % account_id)

    URL_FORM_ACCOUNT_HISTORY = 'https://ib.nab.com.au/nabib/transactionHistoryGetSettings.ctl'
    b.select_form(name='submitForm')
    b.form.set_all_readonly(False)
    b.form.action = URL_FORM_ACCOUNT_HISTORY
    b.form['account'] = account_id
    b.form['accountType'] = account_type
    b.submit()

    if not check_url(b, URL_FORM_ACCOUNT_HISTORY):
        print('\tCannot open page %s with details for account %s' % (
              URL_FORM_ACCOUNT_HISTORY, account_id))
        return

    return b


def render_all_transactions(b):

    # It looks like NAB only lets you get transactions from last 560 days
    # (ancient back-end restriction, I suppose?)
    # So let's calculate that date then, shall we?
    delta_days = 560

    # periodToDate seems to contain today's date, should be safe to use
    b.select_form(name='transactionHistoryForm')
    input_today = b.form['periodToDate'].split('/')
    today = date(2000 + int(input_today[2]), int(input_today[1]), int(input_today[0]))
    start_date = today - timedelta(days=delta_days)

    b.form['periodFromDate'] = start_date.strftime('%d/%m/%y')

    URL_SUBMIT_HISTORY_FORM = 'https://ib.nab.com.au/nabib/transactionHistoryValidate.ctl'
    b.form.action = URL_SUBMIT_HISTORY_FORM

    print('\tGetting transactions from %s to %s (last %s days)' % (start_date,
                                                                   today,
                                                                   delta_days))
    b.submit()

    response = b.response().read()
    if not check_url(b, URL_SUBMIT_HISTORY_FORM):
        return

    # Check we actually got what we asked for
    expr = 'Period:\\r\\n\\s*' + start_date.strftime('%d/%m/%y')

    if not re.findall(expr, response):
        print('It doesn\'t look like I was able to get transactions')
        print('Cannot find string : %s in response' % expr)
        return None

    #write_step( + '.html', response)

    print('\tAll good, transactions retrieved')
    return b


def get_all_transactions(b, account):

    print('\tWe don\'t seem to have any transactins for account \'%s\', hmm...' % account['name'])
    print('\tAnyhow, let\'s retrieve all transactions from beginning of times for it!')

    b = render_all_transactions(b)
    if not b:
        return None

    # Extract and store all transactions into db
    while True:

        cont = b.response().read()
        soup = BeautifulSoup(cont)

        input = soup.select('input[name="pageNo"]')
        if not input:
            currPage = 1
        else:
            currPage = int(input[0].attrs['value'])
        print('\tGetting transactions from page %s' % currPage)

        trans = extract_transactions(cont)
        save_transactions(db, account['bsb'], account['acc_no'], trans)
        print('\tSaved %s transactions' % len(trans))


        # Links to all pages with history are kind of fucked-up
        # there's no classes on them to identify, hence the need to find
        # closest unique element and go via siblings
        currPage += 1
        transExp = soup.select('#transactionExport')[0]

        # :contains does not seem to work, using .find()
        pageLink = list(transExp.nextSiblingGenerator())[1].find('a', text=str(currPage))
        if not pageLink:
            print('\tNo page #%s is available, finished processing' % currPage)
            break

        print('\tOpening page #%s...' % currPage)
        b.open('https://ib.nab.com.au' + pageLink.attrs['href'])
        print('\tOK')

    return b


def export():

    global db
    db = init_db()
    if not db:
        return

    b = login()
    if not b:
        return

    response = b.response().read()
    #response = read_step('logged-in.html')
    write_step('logged-in.html', response)

    # Get all account ids and types
    accounts = get_accounts(response)
    if not accounts:
        return

    for account in accounts:

        print('\nProcessing account \'%s\' (BSB: %s Number: %s)' % (
            account['name'], account['bsb'], account['acc_no']))

        b = open_account_transactions_page(b, account['params'])
        if not b:
            return

        # This will render date filtering form
        URL_TRANS_HISTORY = 'https://ib.nab.com.au/nabib/transactionHistorySelectAccount.ctl'
        form_url = URL_TRANS_HISTORY + '?filterIndicator=true'
        b.open(form_url)
        if not check_url(b, form_url):
            return

        if is_account_empty(db, account['bsb'], account['acc_no']):

            b = get_all_transactions(b, account)
            if not b:
                return

        else:
            print('Account %(acc)s has some transactions, so just get the new ones...' %
                  {'acc': account['acc_no']})

        #response = b.response().read()
        #write_step(account['params'][0] + '.html', response)


if __name__ == "__main__":
    export()


