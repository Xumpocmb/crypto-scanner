import requests
import json
import sqlite3 as sq
from art import tprint
from datetime import datetime


# получаем информацию о всех парах
def get_info():
    response = requests.get(url='https://yobit.net/api/3/info')
    with open('info.json', 'w', encoding='utf-8') as file:
        json.dump(response.json(), file, indent=4, ensure_ascii=False)


# информация о конкретной паре за 24 часа
def get_ticker(curr1, curr2):
    response = requests.get(url=f'https://yobit.net/api/3/ticker/{curr1}_{curr2}?ignore_invalid=1')
    with open('ticker.json', 'w', encoding='utf-8') as file:
        json.dump(response.json(), file, indent=4, ensure_ascii=False)

    base = sq.connect('CryptoHistory.db')
    cur = base.cursor()
    table_name = f'{curr1}_{curr2}'
    date_today = datetime.now().strftime('%d.%m.%Y %H:%M')
    if base:
        cur.execute(
            f'CREATE TABLE IF NOT EXISTS {table_name}(date DATETIME, json_data TEXT)')
    cur.execute(f'INSERT INTO {table_name} VALUES(?, ?)', (f'{date_today}', f'{response.text}'))
    base.commit()
    cur.close()
    base.close()


# информация о выставленных на продажу и покупку ордерах
# в ответе будет 2 словаря: asks - на продажу, bids - на покупку
def get_depth(curr1, curr2, limit):
    response = requests.get(url=f'https://yobit.net/api/3/depth/{curr1}_{curr2}?limit={limit}&ignore_invalid=1')
    with open('depth.json', 'w', encoding='utf-8') as file:
        json.dump(response.json(), file, indent=4, ensure_ascii=False)

    # считаем общую сумму выставленных монет в последних {limit} ордерах
    bids = response.json()[f'{curr1}_usd']['bids']
    bids_amount = 0
    for bid in bids:
        price = bid[0]
        amount = bid[1]
        bids_amount += price * amount

    print(f'[+] Total amount on sale: ${round(bids_amount, 2)}')

    base = sq.connect('CryptoHistory.db')
    cur = base.cursor()
    table_name = f'depth_{curr1}_{curr2}'
    date_today = datetime.now().strftime('%d.%m.%Y %H:%M')
    if base:
        cur.execute(
            f'CREATE TABLE IF NOT EXISTS {table_name}(date DATETIME, bids_amount TEXT, json_data TEXT)')
        cur.execute(
            f'INSERT INTO {table_name} VALUES(?, ?, ?)', (f'{date_today}', f'{round(bids_amount, 2)}', f'{response.text}'))
    base.commit()
    cur.close()
    base.close()


# получаем информацию о сделках покупки и продажи
# в ответе получаем 2 словаря, ask - сделки по покупке, bid - сделки по продаже
# когда монету пампят, ее активно начинают скупать -> bid активно растет
def get_trades(curr1, curr2, limit):
    response = requests.get(url=f'https://yobit.net/api/3/trades/{curr1}_{curr2}?limit={limit}&ignore_invalid=1')
    with open('trades.json', 'w', encoding='utf-8') as file:
        json.dump(response.json(), file, indent=4, ensure_ascii=False)

    # посчитаем ask и bid
    asks_amount = 0
    bids_amount = 0
    bids = response.json()[f'{curr1}_{curr2}']
    for item in bids:
        if item['type'] == 'ask':
            asks_amount += item['price'] * item['amount']
        if item['type'] == 'bid':
            bids_amount += item['price'] * item['amount']

    print(f'[+] Total sold ask amount: ${round(asks_amount, 2)}')
    print(f'[+] Total sold bid amount: ${round(bids_amount, 2)}')

    base = sq.connect('CryptoHistory.db')
    cur = base.cursor()
    table_name = f'trades_{curr1}_{curr2}'
    date_today = datetime.now().strftime('%d.%m.%Y %H:%M')
    if base:
        cur.execute(
            f'CREATE TABLE IF NOT EXISTS {table_name}(date DATETIME, asks_amount TEXT, bids_amount TEXT, json_data TEXT)')
        cur.execute(f'INSERT INTO {table_name} VALUES(?, ?, ?, ?)',
                    (f'{date_today}', f'{round(asks_amount, 2)}', f'{round(bids_amount, 2)}', f'{response.text}'))
    base.commit()
    cur.close()
    base.close()


def get_history(curr1, curr2):
    print('\n\nДля получения истории о выставленных на продажу и покупку ордерах 3')
    print('Для получения истории о сделках покупки и продажи введите 4')
    x_user_choice2 = input('\nВаш выбор?.. ')
    if x_user_choice2 == '3':
        base = sq.connect('CryptoHistory.db')
        cur = base.cursor()
        table_name = f'depth_{curr1}_{curr2}'
        if base:
            cur.execute(f'SELECT date, bids_amount FROM {table_name}')
            history = cur.fetchall()
            for record in history:
                print(f'Дата: {record[0]} | Total amount on sale: ${record[1]}')
        base.commit()
        cur.close()
        base.close()
    elif x_user_choice2 == '4':
        base = sq.connect('CryptoHistory.db')
        cur = base.cursor()
        table_name = f'trades_{curr1}_{curr2}'
        if base:
            cur.execute(f'SELECT date, asks_amount, bids_amount FROM {table_name}')
            history = cur.fetchall()
            for record in history:
                print(f'Дата: {record[0]} | Total sold ask amount: ${record[1]} | Total sold bids amount: ${record[2]}')
        base.commit()
        cur.close()
        base.close()


def main(curr1, curr2):
    get_info()
    get_ticker(curr1, curr2)
    get_depth(curr1, curr2, limit=150)
    get_trades(curr1, curr2, limit=150)


if __name__ == '__main__':
    tprint('CryptoScanner')
    while True:
        print('\n[+] Для получения текущей информации о ценах монет введите 1')
        print('[+] Для получения истории цен монет введите 2')
        print('[+] Для выхода из программы введите 0')
        x_user_choice = input('\nВаш выбор?.. ')
        if x_user_choice == '1':
            print('Пример валют: btc, usd')
            x_curr1 = input('Введите валюту #1: ')
            x_curr2 = input('Введите валюту #2: ')
            main(x_curr1, x_curr2)
        elif x_user_choice == '2':
            print('Пример валют: btc, usd')
            x_curr1 = input('Введите валюту #1: ')
            x_curr2 = input('Введите валюту #2: ')
            get_history(x_curr1, x_curr2)
        elif x_user_choice == '0':
            print('[-] Выход из программы..')
            break

