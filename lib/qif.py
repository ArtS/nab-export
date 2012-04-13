

from os import path

from lib.tools import parse_transaction_date


def get_qif_name(start_date, end_date):

    start_date = parse_transaction_date(start_date)
    end_date = parse_transaction_date(end_date)
    date_format = '%Y.%m.%d'

    return  '%s - %s.qif' % (
                              start_date.strftime(date_format),
                              end_date.strftime(date_format)
                            )


def is_file_present(dir_name, file_name):

    found = False
    try:
        with open(path.join(dir_name, file_name)) as f:
            found = True
    except IOError:
        pass

    return found


def save_qif_file(bsb, acc_n, trans):

    name = get_qif_name(trans[-1]['date'], trans[0]['date'])


    return
