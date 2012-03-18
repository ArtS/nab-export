#!/usr/bin/env python

from mechanize import Browser, ControlNotFoundError
from mechanize import _http
from pyquery import PyQuery
from collections import namedtuple
import re


Transaction = namedtuple('Transaction', ['date', 'name', 'desc', 'amount'])


def get_credentials():

    try:
        with open('.credentials', 'r') as f:
            lines = f.read().split('\n')

            if len(lines) < 2:
                print '.credentials file should have username on first line, password on second'
                return None

            return lines

    except Exception as e:
        print 'Error opening credentials file.'
        print e
        return None


def fetchTransactions(text):

    q = PyQuery(text)
    trans = []

    for row in q('tr[name="DataContainer"]'):
        date = q('span[name="Transaction_TransactionDate"]', row)
        name = q('span[name="Transaction_CardName"]', row)
        desc = q('span[name="Transaction_TransactionDescription"]', row)
        amount = q('span[name="Transaction_Amount"]', row)

        trans.append(Transaction(date=date[0].text if len(date) != 0 else None,
                                 name=name[0].text if len(name) != 0 else None,
                                 desc=desc[0].text if len(desc) != 0 else None,
                                 amount=amount[0].text if len(amount) != 0 else None))
    return trans


"""See http://en.wikipedia.org/wiki/Quicken_Interchange_Format for more info."""
def writeQIF(trans, creds):

    accName = creds[2] if len(creds) > 2 else 'QIF Account'

    with open('export.qif', 'w') as f:

        # Write header
        f.write('!Account\n')
        f.write('N' + accName +'\n')
        f.write('TCCard\n')
        f.write('^\n')
        f.write('!Type:CCard\n')

        for t in trans:
            f.write('C\n') # status - uncleared
            f.write('D' + t.date + '\n') # date
            f.write('T' + t.amount.replace('$', '') + '\n') # amount
            f.write('M' + re.sub('\s+', ' ', t.name + ' ' + t.desc) + '\n') # memo
            #f.write('P' + t.desc.replace('\t', ' ') + '\n') # payee
            f.write('^\n') # end of record


def write_step(name, content):

    with open(name, 'w') as f:
        f.write(content)


def export():

    """creds = getCredentials()
    if not creds:
        return
    """
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
    b.set_debug_http(True)
    b.set_debug_redirects(True)
    b.set_debug_responses(True)

    def make_password(password, key, alphabet):

        # No idea why this is neeed. Seems to check for duplicates
        # Why they didn't do that on server? Stupid...
        for i in range(0, len(alphabet)):
            if i != alphabet.index(alphabet[i]):
                alphabet = alphabet[0, i] + alphabet[i+1:]

        # Now here's funny bit.
        # We take a character from password and corresponding (by index) character from
        # password key (which changes every page load).
        # Then we calculate the length between pasword chararcer and corersponding
        # key character in the alphabet.
        r = []
        for i in range(0, len(password)):

            if password[i] in alphabet:
                pi = alphabet.index(password[i])
                ki = alphabet.index(key[i])
                ni = pi - ki
                if ni < 0:
                    ni = ni + len(alphabet)
                r.append(alphabet[ni])

        return ''.join(r)

    # Test case for password 'encoding' function.
    #hashedPwd = make_password('qqqqqqqq', 'jTECuQc6', '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ')
    #expectedPwd = '7xMOWAek'
    #print hashedPwd + ' == ' + expectedPwd

    creds = get_credentials()
    if not creds:
        return

    print 'Opening main page...'
    b.open('http://www.nab.com.au')
    write_step('www.nab.com.au.html', b.response().read())
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

    write_step('logged-in.html', b.response().read())


if __name__ == "__main__":
    export()
