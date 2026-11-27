#!/usr/bin/env python3
#
# MIT Licence. See http://opensource.org/licenses/MIT
#

"""Test exchange rate fetching."""

import logging
import os
import re

import config
import currency

currency.log = logging.getLogger('currency')


class FakeResponse:
    """Just enough of `workflow.web.Response`."""

    status_code = 200

    def __init__(self, data):
        self.data = data

    def raise_for_status(self):
        pass

    def json(self):
        return self.data


def test_crypto_rates_are_optional(monkeypatch):
    """Crypto rates need CRYPTO_API_KEY, and failing never loses fiat rates."""
    headers_sent = {}
    # Junk keys must be dropped, and XPD (palladium as fiat) never requested
    crypto = {'ETH': 0.0003, 'BTC': 0.00001, 'XPD': 1.0, 'Response': 'Error'}

    def fake_get(url, headers=None, **kwargs):
        if 'cryptocompare' not in url:
            return FakeResponse({'rates': {'EUR': 0.9, 'GBP': 0.8}})
        headers_sent.update(headers)
        if isinstance(crypto, Exception):
            raise crypto
        return FakeResponse(crypto)

    monkeypatch.setattr(currency.web, 'get', fake_get)
    monkeypatch.setattr(currency, 'load_active_currencies',
                        lambda: {'EUR', 'ETH', 'BTC', 'XPD'})
    monkeypatch.setattr(currency, 'OPENX_APP_KEY', None)

    monkeypatch.setattr(currency, 'CRYPTO_API_KEY', None)
    assert currency.fetch_exchange_rates() == {'EUR': 0.9}
    assert not headers_sent  # CryptoCompare not even called

    monkeypatch.setattr(currency, 'CRYPTO_API_KEY', 'secret')
    # BTC is also in the fiat list, but the free fiat source doesn't have it
    assert currency.fetch_exchange_rates() == {'EUR': 0.9, 'ETH': 0.0003,
                                               'BTC': 0.00001}
    assert headers_sent['Authorization'] == 'Apikey secret'

    crypto = IOError('HTTP Error 401: Unauthorized')  # e.g. a bad key
    assert currency.fetch_exchange_rates() == {'EUR': 0.9}


def test_app_key_picks_fiat_source(monkeypatch):
    """With APP_KEY, fiat rates come from openexchangerates.org."""
    urls = []

    def fake_get(url, headers=None, **kwargs):
        urls.append(url)
        return FakeResponse({'rates': {'EUR': 0.9, 'GBP': 0.8}})

    monkeypatch.setattr(currency.web, 'get', fake_get)
    for key, host in (('secret', 'openexchangerates.org'),
                      (None, 'exchangerate-api.com')):
        monkeypatch.setattr(currency, 'OPENX_APP_KEY', key)
        assert currency.load_fiat_rates(['EUR']) == {'EUR': 0.9}
        assert host in urls[-1]


def test_currency_symbols_are_unit_names():
    """Pint can't use symbols such as "STR*" as unit names."""
    symbols = list(currency.CURRENCIES) + list(currency.CRYPTO_CURRENCIES)
    assert [s for s in symbols if not s.isidentifier()] == []


def test_currency_docs_match_config():
    """docs/currencies.md matches config.py: rerun currencies_docs.py."""
    path = os.path.join(os.path.dirname(__file__), '..', 'docs',
                        'currencies.md')
    with open(path, encoding='utf-8') as fp:
        rows = re.findall(r'^\| (\w+) +\| (.*?) +\|$', fp.read(), re.M)
    assert {s for s, _ in rows} - {'Symbol'} == (
        set(config.CURRENCIES) | set(config.CRYPTO_CURRENCIES))
    assert {s for s, name in rows if name.endswith('\\*')} == (
        config.OPENX_ONLY_CURRENCIES)


def test_bad_number_setting_uses_default(monkeypatch):
    """A typo such as UPDATE_INTERVAL=2.5 mustn't stop the workflow."""
    monkeypatch.setenv('UPDATE_INTERVAL', '2.5')
    assert config._int('UPDATE_INTERVAL', 360) == 360
    monkeypatch.setenv('UPDATE_INTERVAL', '60')
    assert config._int('UPDATE_INTERVAL', 360) == 60
