#!/usr/bin/env python

from mechanize import Browser
from mechanize import _http
from pyquery import PyQuery
from collections import namedtuple
import re


Transaction = namedtuple('Transaction', ['date', 'name', 'desc', 'amount'])


def getCredentials():

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
    br = Browser()
    br.set_handle_robots(False)
    br.addheaders = [('User-agent', 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.1) Gecko/2008071615 Fedora/3.0.1-1.fc9 Firefox/3.0.1')]

    br.set_handle_equiv(True)
    br.set_handle_gzip(True)
    br.set_handle_redirect(True)
    br.set_handle_referer(True)
    br.set_handle_robots(False)

    # Follows refresh 0 but not hangs on refresh > 0
    br.set_handle_refresh(_http.HTTPRefreshProcessor(), max_time=1)

    # Want debugging messages?
    br.set_debug_http(True)
    br.set_debug_redirects(True)
    br.set_debug_responses(True)

    print 'Opening main page...'
    br.open('http://www.nab.com.au')
    write_step('www.nab.com.au.html', br.response().read())
    br.set_cookie("lastLogin=0; expires=Sat, 08 Sep 2012 12:46:52 GMT; path=/")
    print 'OK'

    print 'Opening login redir page...'
    br.open('http://www.nab.com.au/cgi-bin/ib/301_start.pl?browser=correct')
    write_step('pre-ib.html', br.response().read())
    print 'OK'

    print 'Opening real login page...'
    br.open('https://ib.nab.com.au/nabib/index.jsp')
    write_step('ib.html', br.response().read())
    print 'OK'






if __name__ == "__main__":
    export()
