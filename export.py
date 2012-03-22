#!/usr/bin/env python

import re

from mechanize import Browser, ControlNotFoundError
from mechanize import _http
from pyquery import PyQuery
from collections import namedtuple

from lib import make_password, get_credentials, write_step, read_step


Transaction = namedtuple('Transaction', ['date', 'name', 'desc', 'amount'])


def check_url(b, expected_url):

    if b.geturl() != expected_url:
        print('\tExpected URL: ', loggedin_url)
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

    if not check_url(b, 'https://ib.nab.com.au/nabib/acctInfo_acctBal.ctl'):
        print('Error logging in.')
        return None

    return b


Account = namedtuple('Account', ['acc_id', 'acc_type'])


def get_accounts(text):

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


def export():

    b = login()
    if not b:
        return

    response = b.response().read()
    #response = read_step('logged-in.html')

    # Get all account names
    accounts = get_accounts(response)
    if not accounts:
        return

    b.select_form(name='submitForm')
    b.form.set_all_readonly(False)
    b.form.action = 'https://ib.nab.com.au/nabib/transactionHistoryGetSettings.ctl'
    b.form['account'] = accounts[0][0]
    b.form['accountType'] = accounts[0][1]
    b.submit()

    response = b.response().read()
    write_step(accounts[0][0] + '.html', response)


if __name__ == "__main__":
    export()


