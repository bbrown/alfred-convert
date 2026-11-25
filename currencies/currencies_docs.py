#!/usr/bin/env python3
# encoding: utf-8
#
# MIT Licence. See http://opensource.org/licenses/MIT
#

"""
Generate docs/currencies.md from the currency lists in src/config.py.

Marks the fiat currencies that need APP_KEY, and stops if
OPENX_ONLY_CURRENCIES in src/config.py no longer matches the sources.
"""

import datetime
import os
import sys

here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(here, '..', 'src'))

from config import (  # noqa: E402
    CRYPTO_CURRENCIES,
    CURRENCIES,
    OPENX_ONLY_CURRENCIES,
    REFERENCE_CURRENCY,
    USER_AGENT,
    XRA_API_URL,
)
from workflow import web  # noqa: E402

# Public list of openexchangerates.org's currencies (no API key needed)
openx_currencies_url = 'https://openexchangerates.org/api/currencies.json'

# Destination file
docs_file = os.path.join(here, '..', 'docs', 'currencies.md')

template = """
Supported Currencies
====================

Use a currency's symbol in conversions, e.g. `conv 100 eur gbp`. The workflow
downloads exchange rates only for your
[active currencies](../README.md#active-currencies).

- [Fiat currencies](#fiat-currencies) ({nfiat:,})
- [Cryptocurrencies](#cryptocurrencies) ({ncrypto:,})
- [Symbols in both lists](#symbols-in-both-lists)


Fiat currencies
---------------

Without an API key, exchange rates come from [ExchangeRate-API.com][xapi]. It
doesn't offer the {npaid} currencies marked `*` (as of {date}). To convert
those, set `APP_KEY` to an [openexchangerates.org][openx] API key.
With `APP_KEY` set, all fiat exchange rates come from
openexchangerates.org.{dead_note}

{fiat_table}


Cryptocurrencies
----------------

Exchange rates come from [CryptoCompare][cryptocompare] and need a
CryptoCompare API key in `CRYPTO_API_KEY`. The list leaves out coins whose
symbols Pint can't use as unit names, such as `1ST` or `STR*`.

{crypto_table}


Symbols in both lists
---------------------

{shared}


[xapi]: https://www.exchangerate-api.com/
[openx]: https://openexchangerates.org/
[cryptocompare]: https://www.cryptocompare.com/
"""


def log(s, *args):
    """Simple STDERR logger."""
    if args:
        s = s % args
    print(s, file=sys.stderr)


def get_json(url):
    """Return the decoded JSON at ``url``."""
    r = web.get(url, headers={'User-Agent': USER_AGENT})
    r.raise_for_status()
    return r.json()


def table(rows):
    """Return a Markdown table of ``(symbol, name)`` rows."""
    rows = [('Symbol', 'Name')] + rows
    w0 = max(len(r[0]) for r in rows)
    w1 = max(len(r[1]) for r in rows)
    lines = ['| {} | {} |'.format(a.ljust(w0), b.ljust(w1)) for a, b in rows]
    lines.insert(1, '|{}|{}|'.format('-' * (w0 + 2), '-' * (w1 + 2)))
    return '\n'.join(lines)


def main():
    """Write docs/currencies.md."""
    free = set(get_json(XRA_API_URL.format(REFERENCE_CURRENCY))['rates'])
    openx = set(get_json(openx_currencies_url))
    fiat = {s: n.strip() for s, n in CURRENCIES.items()}
    crypto = {s: n.strip() for s, n in CRYPTO_CURRENCIES.items()}

    paid = {s for s in fiat if s not in free and s in openx}
    if paid != OPENX_ONLY_CURRENCIES:
        log('Set OPENX_ONLY_CURRENCIES in src/config.py to: %s',
            ', '.join(sorted(paid)))
        sys.exit(1)

    dead = {s for s in fiat if s not in free and s not in openx}
    for message, symbols in [
            ('No source offers', dead),
            ('Lost when APP_KEY is set', {s for s in fiat
                                          if s in free and s not in openx}),
            ('Free source offers, not in CURRENCIES', free - set(fiat))]:
        if symbols:
            log('%s: %s', message, ', '.join(sorted(symbols)))

    # Same rule as currency.py: a shared symbol with another name is fiat
    shared = sorted(set(fiat) & set(crypto))
    as_fiat = {s for s in shared if fiat[s] != crypto[s]}
    crypto_rows = [(s, crypto[s]) for s in sorted(crypto) if s not in as_fiat]
    shared_lines = []
    for s in shared:
        if s in as_fiat:
            line = '- `{}` means {}, not the {} cryptocurrency.'.format(
                s, fiat[s], crypto[s])
        else:
            line = '- `{}` is {} in both lists, so either API key adds it.'
            line = line.format(s, fiat[s])
        shared_lines.append(line)

    marks = dict.fromkeys(paid, ' \\*')
    marks.update(dict.fromkeys(dead, ' †'))
    dead_note = ''
    if dead:
        dead_note = (" Neither source offers the {} currencies marked `†` "
                     "any more, so they can't be converted.").format(len(dead))

    today = datetime.date.today()
    doc = template.format(
        nfiat=len(fiat), ncrypto=len(crypto_rows), npaid=len(paid),
        date='{:%B} {}, {}'.format(today, today.day, today.year),
        dead_note=dead_note,
        fiat_table=table([(s, fiat[s] + marks.get(s, ''))
                          for s in sorted(fiat)]),
        crypto_table=table(crypto_rows),
        shared='\n'.join(shared_lines))

    with open(docs_file, 'w', encoding='utf-8') as fp:
        fp.write(doc)
    log('Wrote %s', os.path.normpath(docs_file))


if __name__ == '__main__':
    main()
