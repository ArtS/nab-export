
import sqlite3
from datetime import datetime
import time

from tools import parse_transaction_date


db = None


def init_db():

    global db
    db = sqlite3.connect('transactions.db')
    db.execute('''
        create table if not exists transactions
              (
                id integer primary key autoincrement,

                bsb text,
                acc_no text,

                date_sec integer,
                date_txt text,
                details text,

                debit_amount text,
                credit_amount text,

                balance text
              )''')
    return db


def get_last_transaction_date(bsb, acc_no):

    global db
    cur = db.execute('''
                     select date_sec from transactions
                     where bsb = ? and acc_no = ?
                     order by date_sec desc
                     limit 1
                     ''',
                     [bsb, acc_no]
                    )

    row = cur.fetchall()
    if not row:
        return None

    return datetime.fromtimestamp(row[0][0])


def save_transaction(

                     bsb,
                     acc_no,

                     tran_date_txt,
                     details,

                     debit_amount,
                     credit_amount,

                     balance
                    ):

    global db
    # Need to convert tran_date into number of seconds and store those
    tran_date = parse_transaction_date(tran_date_txt)
    seconds = int(time.mktime(tran_date.utctimetuple()))


    db.execute('insert into transactions values (null, ?, ?, ?, ?, ?, ?, ?, ?)',
               (
                bsb,
                acc_no,

                seconds,
                tran_date_txt,
                details,

                debit_amount,
                credit_amount,

                balance
               )
              )
    db.commit()


def save_transactions(bsb, acc_no, transactions):

    global db

    for trans in transactions:
        save_transaction(bsb,
                         acc_no,

                         trans['date'],
                         trans['details'],

                         trans['debit_amount'],
                         trans['credit_amount'],
                         trans['balance']
                        )
