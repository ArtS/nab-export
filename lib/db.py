
import sqlite3
from datetime import datetime
import time


db = None


def init_db():

    global db
    db = sqlite3.connect('transactions.db')
    db.execute('''
        create table if not exists transactions
              (
                id integer primary key autoincrement,

                name text,
                bsb text,
                acc_no text,

                date_sec integer,
                date_txt text,

                payee text,
                memo text,

                debit_amount double,
                credit_amount double,

                balance double
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

                     name,
                     bsb,
                     acc_no,

                     tran_date_txt,
                     tran_date,

                     payee,
                     memo,

                     debit_amount,
                     credit_amount,

                     balance
                    ):

    global db

    seconds = int(time.mktime(tran_date.utctimetuple()))
    db.execute('insert into transactions values (null, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
               (
                name,
                bsb,
                acc_no,

                seconds,
                tran_date_txt,

                payee,
                memo,

                debit_amount,
                credit_amount,

                balance
               )
              )
    db.commit()


def save_transactions(name, bsb, acc_no, transactions):

    global db

    for trans in transactions:
        save_transaction(name,
                         bsb,
                         acc_no,

                         trans['date'],
                         trans['date_obj'],

                         trans['payee'],
                         trans['memo'],

                         trans['debit_amount'],
                         trans['credit_amount'],
                         trans['balance']
                        )


def is_transaction_in_db(bsb, acc_no, tran):

    global db
    cur = db.execute('''
                     select * from transactions where
                        bsb = ?
                        and acc_no = ?
                        and date_txt = ?
                        and payee = ?
                        and memo = ?
                        and debit_amount = ?
                        and credit_amount = ?

                     ''',
                     (bsb, acc_no,
                      tran['date'],
                      tran['payee'], tran['memo'],
                      tran['debit_amount'],
                      tran['credit_amount']))

    row = cur.fetchall()
    if not row:
        return False

    return True
