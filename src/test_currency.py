#!/usr/bin/env python3
# encoding: utf-8
#
# MIT Licence. See http://opensource.org/licenses/MIT
#

"""Test exchange rate fetching."""

import logging

import currency

currency.log = logging.getLogger('currency')


class FakeResponse(object):
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
    crypto = {'ETH': 0.0003, 'Response': 'Error'}  # junk keys must be dropped

    def fake_get(url, headers=None, **kwargs):
        if 'cryptocompare' not in url:
            return FakeResponse({'rates': {'EUR': 0.9, 'GBP': 0.8}})
        headers_sent.update(headers)
        if isinstance(crypto, Exception):
            raise crypto
        return FakeResponse(crypto)

    monkeypatch.setattr(currency.web, 'get', fake_get)
    monkeypatch.setattr(currency, 'load_active_currencies',
                        lambda: {'EUR', 'ETH'})
    monkeypatch.setattr(currency, 'OPENX_APP_KEY', None)

    monkeypatch.setattr(currency, 'CRYPTO_API_KEY', None)
    assert currency.fetch_exchange_rates() == {'EUR': 0.9}
    assert not headers_sent  # CryptoCompare not even called

    monkeypatch.setattr(currency, 'CRYPTO_API_KEY', 'secret')
    assert currency.fetch_exchange_rates() == {'EUR': 0.9, 'ETH': 0.0003}
    assert headers_sent['Authorization'] == 'Apikey secret'

    crypto = IOError('HTTP Error 401: Unauthorized')  # e.g. a bad key
    assert currency.fetch_exchange_rates() == {'EUR': 0.9}
