#!/usr/bin/env python


from datetime import timedelta

from lib import db, browser, qif


def get_last_transaction_date(b, account):

    today = browser.get_servers_today_date(b)

    # It looks like NAB only lets you get transactions for last 560 days
    # (ancient back-end restriction, I suppose?)
    MAX_HISTORY_DAYS = 560
    last_date = db.get_last_transaction_date(account['bsb'], account['acc_no'])

    if not last_date:

        print('\tWe don\'t seem to have any transactins for account \'%s\' in database.' % account['name'])
        print('\tThat\'s OK though! Let\'s retrieve transactions for last %s days' % MAX_HISTORY_DAYS)

        last_date = today - timedelta(days=MAX_HISTORY_DAYS)

    else:

        print('\tAccount %(acc)s has some transactions, so just get the new ones...' %
              {'acc': account['acc_no']})

        if (today - last_date).days > MAX_HISTORY_DAYS:
            print('Looks like the oldest transaction in the DB is older than %s days' % MAX_HISTORY_DAYS)
            print('Retrieving transactions for only last %s days' % MAX_HISTORY_DAYS)
            last_date = today - timedelta(days=MAX_HISTORY_DAYS)

    return last_date


def remove_pending_transactions(trans):

    res = []
    for t in trans:

        if t['details'] == 'EFTPOS DEBIT PURCHASE-FLEXIPAY':
            print('\tSkipping transaction %s' % t)
            pass

        res.append(t)

    return res


def exclude_existing_in_db_trans(bsb, acc_n, trans):

    res = []
    for t in trans:
        if not db.is_transaction_in_db(bsb, acc_n, t):
            res.append(t)

    return res


def export():

    db.init_db()
    if not db:
        return

    b = browser.login()
    if not b:
        return

    response = b.response().read()

    accounts = browser.get_accounts(response)
    if not accounts:
        return

    for account in accounts:

        print('\nProcessing account \'%s\' (BSB: %s Number: %s)' % (
            account['name'], account['bsb'], account['acc_no']))

        b = browser.open_account_transactions_page(b, account['params'])
        if not b:
            return

        last_date = get_last_transaction_date(b, account)

        trans = browser.get_all_transactions(b, account, last_date)
        trans = remove_pending_transactions(trans)
        trans = exclude_existing_in_db_trans(account['bsb'],
                                             account['acc_no'],
                                             trans)

        if not trans:
            return

        db.save_transactions(account['name'],
                             account['bsb'],
                             account['acc_no'],
                             trans)

        qif.save_qif_file(account['name'],
                          account['bsb'],
                          account['acc_no'],
                          trans)

        print('\tSaved %s transactions' % len(trans))


if __name__ == "__main__":
    export()
