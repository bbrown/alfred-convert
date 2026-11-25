#!/usr/bin/env python3
# encoding: utf-8
#
# Copyright (c) 2017 Dean Jackson <deanishe@deanishe.net>
#
# MIT Licence. See http://opensource.org/licenses/MIT
#
# Created on 2017-07-16
#

"""Test converter."""

from __future__ import print_function, absolute_import

from collections import namedtuple
import logging
import time

import pytest

import convert
from defaults import Defaults

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger()
convert.log = logging.getLogger('convert')
# Normally created by convert.main()
convert.ureg = convert.UnitRegistry(convert.DEFAULT_UNIT_DEFINITIONS)
convert.ureg.formatter.default_format = 'P'


T = namedtuple('T', 'number dimensionality from_unit to_unit')
C = namedtuple('C', 'from_number from_unit to_number to_unit dimensionality')


class FakeWorkflow(object):
    """Just enough of `workflow.Workflow`, with settings and cache in memory."""

    def __init__(self, tmp_path=None):
        self.dir = tmp_path
        self.settings = {}
        self.saved = {}  # cache name -> time saved
        self.rerun = 0

    def cachefile(self, name):
        return str(self.dir / name)

    def cache_data(self, name, data):
        if data is None:
            self.saved.pop(name, None)
        else:
            self.saved[name] = time.time()

    def cached_data_fresh(self, name, max_age):
        return time.time() - self.saved.get(name, 0) < max_age

    def workflowfile(self, name):
        return name


def verify_parsed(t1, t2):
    """Verify results of `Converter.parse()`."""
    assert t1.number == t2.number
    assert t1.dimensionality == t2.dimensionality
    assert t1.from_unit == t2.from_unit
    assert t1.to_unit == t2.to_unit


def verify_conversion(c1, c2):
    """Verify results of `Converter.convert()`."""
    assert c1.from_number == c2.from_number
    assert c1.from_unit == c2.from_unit
    assert c1.to_number == c2.to_number
    assert c1.to_unit == c2.to_unit
    assert c1.dimensionality == c2.dimensionality


def test_invalid():
    """Test invalid input."""
    queries = [
        'dave',  # doesn't start with a number
        '1.3',  # no unit
        '5 daves',  # invalid units
        '10 km m cm',  # too many units
    ]
    c = convert.Converter(None)
    for query in queries:
        with pytest.raises(ValueError):
            c.parse(query)


def test_valid():
    """Test valid input."""
    data = [
        ('1.3 km', T(1.3, '[length]', 'kilometer', None)),
        ('1.3 km miles', T(1.3, '[length]', 'kilometer', 'mile')),
        ('5 m/s kph', T(5.0, '[length] / [time]', 'meter/second',
                        'kilometer_per_hour')),
        ('21.3 m^2 acres', T(21.3, '[length] ** 2', u'meter²', 'acre')),
        ('+5km m', T(5.0, '[length]', 'kilometer', 'meter')),
        ('20 degC degF', T(20.0, '[temperature]', 'degree_Celsius',
                           'degree_Fahrenheit')),
    ]
    c = convert.Converter(None)
    for t in data:
        i = c.parse(t[0])
        verify_parsed(t[1], i)


def test_conversion():
    """Test conversions."""
    data = [
        ('1km m', C(1, 'kilometer', 1000, 'meter', '[length]')),
    ]
    c = convert.Converter(None)
    for t in data:
        i = c.parse(t[0])
        res = c.convert(i)
        verify_conversion(t[1], res[0])


def test_defaults():
    """Test default conversions."""
    data = [
        ('1m', [
            C(1, 'meter', 100, 'centimeter', '[length]'),
            C(1, 'meter', 0.001, 'kilometer', '[length]')]),
        ('100g', [
            C(100, 'gram', 0.1, 'kilogram', '[mass]'),
            C(100, 'gram', 100000, 'milligram', '[mass]')]),
    ]

    wf = FakeWorkflow()
    wf.settings['default_units'] = {
        '[length]': ['centimeter', 'kilometer'],
        '[mass]': ['kilogram', 'milligram'],
        '[temperature]': ['degF'],
    }
    c = convert.Converter(Defaults(wf))

    for t in data:
        i = c.parse(t[0])
        res = c.convert(i)
        assert len(res) == len(t[1])
        for j, r in enumerate(res):
            log.debug(r)
            verify_conversion(t[1][j], r)

    # Pint calls degF "degree_Fahrenheit": still don't convert it to itself
    with pytest.raises(convert.NoToUnits):
        c.convert(c.parse('100 degF'))


def test_formatter():
    """Dynamic decimals work the same for negative numbers."""
    f = convert.Formatter(2, '.', ',', True)
    assert f.formatted(-1234.5) == '-1,234.50'
    assert f.formatted(-0.004) == '-0.004'
    assert f.formatted(0.004) == '0.004'


def test_bad_currency_symbols_are_skipped(monkeypatch):
    """One bad exchange rate doesn't stop the others from loading."""
    monkeypatch.setattr(convert, 'ureg',
                        convert.UnitRegistry(convert.DEFAULT_UNIT_DEFINITIONS))
    convert.register_exchange_rates(
        {'STR*': 2.0, '1ST': 3.0, 'ZZZ': 'Error', 'EUR': 0.5})
    assert convert.ureg.Quantity(1, 'EUR').to('usd').magnitude == 2.0


def test_currency_error_names_missing_key(monkeypatch):
    """Unknown currencies say which API key would add them."""
    shown = []
    monkeypatch.setattr(convert, 'show_currency_help', shown.append)
    monkeypatch.setattr(convert, 'is_running', lambda name: False)
    monkeypatch.setattr(convert, 'CRYPTO_API_KEY', None)
    for unit in ('eth', 'btc', 'zmw'):
        with pytest.raises(SystemExit):
            convert.error_if_currency(unit)
    assert shown == ['CRYPTO_API_KEY', 'CRYPTO_API_KEY', 'APP_KEY']

    convert.error_if_currency('furlong')  # not a currency
    monkeypatch.setattr(convert, 'is_running', lambda name: True)
    convert.error_if_currency('eth')  # rates are still downloading
    assert len(shown) == 3


def test_rate_sources_change_clears_cache(tmp_path, monkeypatch):
    """Setting or removing an API key clears cached exchange rates."""
    wf = FakeWorkflow(tmp_path)
    monkeypatch.setattr(convert, 'CRYPTO_API_KEY', None)
    convert.handle_update(wf)  # no record of previous sources yet
    wf.cache_data('exchange_rates', {})
    convert.handle_update(wf)  # unchanged
    assert 'exchange_rates' in wf.saved

    monkeypatch.setattr(convert, 'CRYPTO_API_KEY', 'key')
    convert.handle_update(wf)
    assert 'exchange_rates' not in wf.saved


def test_failed_update_waits_before_retrying(monkeypatch):
    """Offline, don't start a new download on every keystroke."""
    started = []
    monkeypatch.setattr(convert, 'run_in_background',
                        lambda name, cmd: started.append(cmd))
    wf = FakeWorkflow()
    convert.start_update(wf)
    convert.start_update(wf)  # first download failed: rates still stale
    assert len(started) == 1

    wf.saved['rates_attempt'] -= convert.RETRY_DELAY
    convert.start_update(wf)
    assert len(started) == 2

    wf.cache_data('exchange_rates', {})  # rates are fresh: nothing to do
    wf.saved['rates_attempt'] -= convert.RETRY_DELAY
    convert.start_update(wf)
    assert len(started) == 2


if __name__ == '__main__':  # pragma: no cover
    pytest.main([__file__])
