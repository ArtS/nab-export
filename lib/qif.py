

import os

from lib.tools import parse_transaction_date


def get_qif_name(start_date, end_date):

    start_date = parse_transaction_date(start_date)
    end_date = parse_transaction_date(end_date)
    date_format = '%Y.%m.%d'

    return  '%s - %s.qif' % (
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


def save_qif_file(bsb, acc_n, trans):

    dir_name = '%s-%s' % (bsb.replace('-', ''), acc_n.replace('-', '')
    file_name = get_qif_name(trans[-1]['date'], trans[0]['date'])
    full_path = os.path.join(dir_name, file_name)

    # Create folder if not present
    if not os.path.exists(dir_name):
        os.mkdir(dir_name)

    # It's possible that file with such name already exists.
    # in this case we'll be adding a postfix of N to the file
    # name.
    available_name = get_available_name(full_path)

    return
