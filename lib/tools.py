

from datetime import datetime
from getpass import getpass


def write_step(name, content):

    with open(name, 'w') as f:
        f.write(content)


def read_step(name):

    with open(name, 'r') as r:
        return r.read()


def get_credentials():

    try:
        with open('.credentials', 'r') as f:
            lines = f.read().split('\n')

            if len(lines) < 2:
                print '\n\n\tIt looks like there\'s only ' + str(len(lines)) + ' line in .credentials file'
                print '\tPlease ensure the file contains two lines,'
                print '\tfirst line - username, second line - password'
                print '\n\n'
                return None

            return lines

    except Exception as e:
        lines = []
        print('Could not find .credentials file. Please enter username and password')
        print('Username:')
        lines.append(raw_input())
        lines.append(getpass())

        return lines


def writeQIF(trans, creds):
    """See http://en.wikipedia.org/wiki/Quicken_Interchange_Format for more info."""

    accName = creds[2] if len(creds) > 2 else 'QIF Account'

    with open('export.qif', 'w') as f:

        # Write header
        f.write('!Account\n')
        f.write('N' + accName + '\n')
        f.write('TCCard\n')
        f.write('^\n')
        f.write('!Type:CCard\n')

        for t in trans:
            f.write('C\n')  # status - uncleared
            f.write('D' + t.date + '\n')  # date
            f.write('T' + t.amount.replace('$', '') + '\n')  # amount
            f.write('M' + re.sub('\s+', ' ', t.name + ' ' + t.desc) + '\n')  # memo
            # f.write('P' + t.desc.replace('\t', ' ') + '\n') # payee
            f.write('^\n')  # end of record


def make_password(password, webKey, webAlpha):
    """
    Python implementation of the 'encode(g,c,b)' JS function
    """
    for d in range(len(webAlpha)):
        if d != webAlpha.index(webAlpha[d]):
            b = webAlpha[0:d] + webAlpha[d + 1:]

    e = ['' for i in range(len(password))]
    for d in range(len(password)):
        e[d] = password[d]
        try:
            f = webAlpha.index(password[d])
            if f >= 0 and d < len(webKey):
                h = webAlpha.index(webKey[d])
                if h >= 0:
                    f -= h
                    if f < 0:
                        f += len(webAlpha)
                    e[d] = webAlpha[f]
        except ValueError:
            continue

    return "".join(e)


def parse_transaction_date(text):

    return datetime.strptime(text, '%d %b %y')
