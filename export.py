#!/usr/bin/env python

import re
import sqlite3
from collections import namedtuple
from datetime import date, timedelta

from mechanize import Browser, ControlNotFoundError
from mechanize import _http
from pyquery import PyQuery

from lib import make_password, get_credentials, write_step, read_step


Transaction = namedtuple('Transaction', ['date', 'name', 'desc', 'amount'])

logged_in_url = 'https://ib.nab.com.au/nabib/acctInfo_acctBal.ctl'

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
    b.submit()

    if not check_url(b, logged_in_url):
        print('Error logging in.')
        return None

    return b


Account = namedtuple('Account', ['acc_id', 'acc_type'])


def get_account_ids(text):

    pq = PyQuery(text)
    account_links = pq.find('#accountBalances_nonprimary_subaccounts a.accountNickname')
    if len(account_links) == 0:
        print('\tNo accounts found.')
        return

    accounts = []
    for link in account_links:

        params = re.findall("'(.*?)'", link.attrib['href'])
        if len(params) != 2:
            print('\tError: incorrect HREF for account: ', link.attrib['href'])
            return None

        accounts.append(params)

    return accounts


def init_db():

    db = sqlite3.connect('transactions.db')
    db.execute('''
        create table if not exists transactions
              (
                account_id text,

                date text,
                details text,

                debit_amount_whole integer,
                debit_amount_fraction integer,

                credit_amount_whole integer,
                credit_amount_fraction integer,

                balance_whole integer,
                balance_fraction integer,
                balance_sign text
              )''')
    return db


def is_account_empty(db, account_id):

    cur = db.execute('''
                     select count(account_id) from transactions
                     where account_id = ?
                     ''',
                     [account_id]
                    )
    row = cur.next()

    return row[0] == 0


def save_transaction(db,
                     account_id,
                     date,
                     details,

                     debit_amount_whole,
                     debit_amount_fraction,

                     credit_amount_whole,
                     credit_amount_fraction,

                     balance_whole,
                     balance_fraction,
                     balance_sign):

    db.execute('insert into transactions values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
               (
                account_id,
                date,
                details,

                debit_amount_whole,
                debit_amount_fraction,

                credit_amount_whole,
                credit_amount_fraction,

                balance_whole,
                balance_fraction,
                balance_sign
               )
              )


def export():

    db = init_db()

    b = login()
    if not b:
        return

    response = b.response().read()
    #response = read_step('logged-in.html')

    # Get all account ids and types
    accounts = get_account_ids(response)
    if not accounts:
        return

    for account in accounts:

        account_id = account[0]
        account_type = account[1]

        if b.geturl() != logged_in_url:
            print('Current url is %s, need to open accounts page at %s' %
                  (b.geturl(), logged_in_url))
            b.open('https://ib.nab.com.au/nabib/acctInfo_acctBal.ctl')

        print('Opening transaction page for account ' + account_id)
        URL_FORM_ACCOUNT_HISTORY = 'https://ib.nab.com.au/nabib/transactionHistoryGetSettings.ctl'
        b.select_form(name='submitForm')
        b.form.set_all_readonly(False)
        b.form.action = URL_FORM_ACCOUNT_HISTORY
        b.form['account'] = account_id
        b.form['accountType'] = account_type
        b.submit()

        if not check_url(b, URL_FORM_ACCOUNT_HISTORY):
            return

        # This will render date filtering form
        URL_TRANS_HISTORY = 'https://ib.nab.com.au/nabib/transactionHistorySelectAccount.ctl'
        form_url = URL_TRANS_HISTORY + '?filterIndicator=true'
        b.open(form_url)
        if not check_url(b, form_url):
            return

        if is_account_empty(db, account_id):

            print('Account %(acc)s is empty, retrieving transactions from beginning of times' %
                  {'acc': account_id})

            # It looks like NAB only lets you get transactions from last 560 days
            # (ancient back-end restriction, I suppose?)
            # So let's calculate that date then, shall we?

            # periodToDate seems to contain today's date, should be safe to use
            b.select_form(name='transactionHistoryForm')
            input_today = b.form['periodToDate'].split('/')
            today = date(2000 + int(input_today[2]), int(input_today[1]), int(input_today[0]))
            start_date = today - timedelta(days=560)
            b.form['periodFromDate'] = start_date.strftime('%d/%m/%y')
            URL_SUBMIT_HISTORY_FORM = 'https://ib.nab.com.au/nabib/transactionHistoryValidate.ctl'
            b.form.action = URL_SUBMIT_HISTORY_FORM
            b.submit()

            response = b.response().read()
            if not check_url(b, URL_SUBMIT_HISTORY_FORM):
                return

            write_step(account_id + '.html', response)
            #if not check_url(b, ''

        else:
            print('Account %(acc)s has some transactions, so just get the new ones...' %
                  {'acc': account_id})

        #response = b.response().read()
        #write_step(account[0] + '.html', response)


if __name__ == "__main__":
    export()


