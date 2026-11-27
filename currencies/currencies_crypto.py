#!/usr/bin/env python3
# encoding: utf-8
#
# Copyright (c) 2017 Dean Jackson <deanishe@deanishe.net>
#
# MIT Licence. See http://opensource.org/licenses/MIT
#
# Created on 2017-07-14
#

"""
Filter list of cryptocurrencies by whether an exchange rate is available.
"""

from __future__ import print_function, absolute_import

from collections import namedtuple
import csv
import os
import sys
from time import sleep

here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(here, '..', 'src'))

from workflow import web  # noqa: E402

reference_currency = 'USD'
api_key = None

all_currencies_url = 'https://min-api.cryptocompare.com/data/all/coinlist'
base_url = 'https://min-api.cryptocompare.com/data/price?fsym={}&tsyms={}'

crypto_currencies_file = os.path.join(here, 'currencies_crypto.tsv')


Currency = namedtuple('Currency', 'symbol name')


def main():
    """Generate list of cryptocurrencies with exchange rates."""
    headers = {'Authorization': 'Apikey ' + api_key}
    r = web.get(all_currencies_url, headers=headers)
    r.raise_for_status()
    data = r.json()
    all_currencies = []
    valid = []
    for k, d in data['Data'].items():
        if k.isidentifier():  # Pint can't use e.g. "STR*" as a unit name
            all_currencies.append(Currency(k, d['CoinName']))

    print('%d total currencies' % len(all_currencies))

    for i in range(0, len(all_currencies), 20):
        currencies = all_currencies[i:i + 20]
        url = base_url.format(reference_currency,
                              ','.join([c.symbol for c in currencies]))
        r = web.get(url, headers=headers)
        r.raise_for_status()
        data = r.json()
        for c in currencies:
            if c.symbol in data:
                valid.append(c)
                print('[%s] OK' % c.symbol)
            else:
                print('[%s] ERROR' % c.symbol)

        sleep(0.3)

    with open(crypto_currencies_file, 'w', newline='', encoding='utf-8') as fp:
        w = csv.writer(fp, delimiter='\t')
        for c in sorted(valid, key=lambda t: t.symbol):
            w.writerow([c.symbol, c.name])


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('Usage: currencies_crypto.py <CRYPTO_API_KEY>')
        sys.exit(1)
    api_key = sys.argv[1]
    main()
