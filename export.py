#!/usr/bin/env python


from datetime import timedelta

from lib import db, browser


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

        last_date = db.get_last_transaction_date(account['bsb'], account['acc_no'])
        if not last_date:

            print('\tWe don\'t seem to have any transactins for account \'%s\' in database.' % account['name'])
            print('\tThat\'s OK though! Let\'s retrieve all of them since the beginning of times.')

            # It looks like NAB only lets you get transactions for last 560 days
            # (ancient back-end restriction, I suppose?)
            today = browser.get_servers_today_date(b)
            last_date = today - timedelta(days=560)

        else:

            print('Account %(acc)s has some transactions, so just get the new ones...' %
                  {'acc': account['acc_no']})

        trans = browser.get_all_transactions(b, account, last_date)
        if not trans:
            return
        db.save_transactions(account['bsb'], account['acc_no'], trans)

        print('\tSaved %s transactions' % len(trans))


if __name__ == "__main__":
    export()
