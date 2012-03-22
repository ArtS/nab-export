

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
        print 'Error opening credentials file.'
        print e
        return None


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
