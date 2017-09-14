

import re
import os


def get_qif_name(start_date, end_date):

    date_format = '%Y.%m.%d'

    return '%s - %s.qif' % (
        start_date.strftime(date_format),
        end_date.strftime(date_format)
    )


def is_file_present(full_path):

    found = False
    try:
        with open(full_path) as f:
            found = True
    except IOError:
        pass

    return found


def get_available_name(full_path):

    n = 0
    while True:

        full_path_n = full_path + ('' if n == 0 else '.%d' % n)

        if is_file_present(full_path_n):
            n += 1
        else:
            return full_path_n


def write_qif(acc_name, trans, file_name):
    """See http://en.wikipedia.org/wiki/Quicken_Interchange_Format for more info."""

    with open(file_name, 'w') as f:

        # Write header
        f.write('!Type:Bank\n')
        #f.write('N' + acc_name +'\n')
        # f.write('^\n')

        for t in trans:
            f.write('C\n')  # status - uncleared
            f.write('D%s\n' % t['date_obj'].strftime('%d/%m/%y'))  # date

            if t['debit_amount']:
                amount = t['debit_amount']
                sign = '-'
            else:
                amount = t['credit_amount']
                sign = '+'
            f.write('T%s%s\n' % (sign, amount))  # amount

            f.write('P%s\n' % t['payee'])  # payee
            f.write('M%s\n' % t['memo'])  # memo

            f.write('^\n')  # end of record


def save_qif_file(acc_name, bsb, acc_n, trans):

    dir_name = '%s-%s' % (bsb.replace('-', ''), acc_n.replace('-', ''))
    file_name = get_qif_name(trans[-1]['date_obj'], trans[0]['date_obj'])
    full_path = os.path.join(dir_name, file_name)

    # Create folder if not present
    if not os.path.exists(dir_name):
        os.mkdir(dir_name)

    # It's possible that file with such name already exists.
    # in this case we'll be adding a postfix of N to the file
    # name.
    available_file_name = get_available_name(full_path)

    write_qif(acc_name, trans, available_file_name)

    return
