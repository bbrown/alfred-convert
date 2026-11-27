#!/usr/bin/env python3
#
# Copyright (c) 2017 Dean Jackson <deanishe@deanishe.net>
#
# MIT Licence. See http://opensource.org/licenses/MIT
#
# Created on 2017-07-16
#

"""Test converter."""

from collections import namedtuple
import logging
import time

import pytest

import convert
from defaults import Defaults

logging.basicConfig(level=logging.DEBUG)
convert.log = logging.getLogger('convert')
# Normally created by convert.main()
convert.ureg = convert.UnitRegistry(convert.DEFAULT_UNIT_DEFINITIONS)
convert.ureg.formatter.default_format = 'P'


T = namedtuple('T', 'number dimensionality from_unit to_unit')
C = convert.Conversion


class FakeWorkflow:
    """Just enough of `workflow.Workflow`: settings and cache in memory."""

    def __init__(self, tmp_path=None):
        self.dir = tmp_path
        self.settings = {}
        self.saved = {}  # cache name -> time saved

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


def test_invalid():
    """Test invalid input."""
    queries = [
        'dave',  # doesn't start with a number
        '1.3',  # no unit
        '5 daves',  # invalid units
        '10 km m cm',  # too many units
        '-',  # half-typed: "-40 degC degF"
        '20.5 m/',  # half-typed: "20.5 m/s kph"
        '1 m)',
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
        ('21.3 m^2 acres', T(21.3, '[length] ** 2', 'meter²', 'acre')),
        ('+5km m', T(5.0, '[length]', 'kilometer', 'meter')),
        ('20 degC degF', T(20.0, '[temperature]', 'degree_Celsius',
                           'degree_Fahrenheit')),
    ]
    c = convert.Converter(None)
    for t in data:
        assert c.parse(t[0])[:4] == t[1]  # all fields but context


def test_conversion():
    """Test conversions."""
    data = [
        ('1km m', C(1, 'kilometer', 1000, 'meter', '[length]')),
    ]
    c = convert.Converter(None)
    for t in data:
        assert c.convert(c.parse(t[0])) == [t[1]]


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
        assert c.convert(c.parse(t[0])) == t[1]

    # Pint calls degF "degree_Fahrenheit": still don't convert it to itself
    with pytest.raises(convert.NoToUnits):
        c.convert(c.parse('100 degF'))


def test_formatter():
    """Dynamic decimals show 2 significant digits, negative numbers too."""
    f = convert.Formatter(2, '.', ',', dynamic_decimals=True)
    assert f.formatted(-1234.5) == '-1,234.50'
    assert f.formatted(-0.004) == '-0.004'
    assert f.formatted(0.004) == '0.004'
    assert f.formatted(0.015) == '0.015'
    assert f.formatted(0.0046) == '0.0046'

    f = convert.Formatter(2, ',', '.', dynamic_decimals=False)
    assert f.formatted(1234.5, 'm') == '1.234,50 m'
    assert f.formatted(1234.5, thousands=False) == '1234,50'


def test_bad_currency_symbols_are_skipped(monkeypatch):
    """One bad exchange rate doesn't stop the others from loading."""
    monkeypatch.setattr(convert, 'ureg',
                        convert.UnitRegistry(convert.DEFAULT_UNIT_DEFINITIONS))
    convert.register_exchange_rates(
        {'STR*': 2.0, '1ST': 3.0, 'ZZZ': 0, 'EUR': 0.5})
    assert convert.ureg.Quantity(1, 'EUR').to('usd').magnitude == 2.0


def test_lowercase_currency_codes(monkeypatch):
    """Lowercase "php" is the peso, not picohorsepower; "cup" is a volume."""
    monkeypatch.setattr(convert, 'ureg',
                        convert.UnitRegistry(convert.DEFAULT_UNIT_DEFINITIONS))
    convert.register_exchange_rates({'PHP': 50.0, 'CUP': 24.0})
    assert convert.ureg.Quantity(100, 'php').to('usd').magnitude == 2.0
    assert str(convert.ureg.Quantity(1, 'cup').dimensionality) == (
        '[length] ** 3')


def test_currency_error_names_missing_key(monkeypatch):
    """Unknown currencies say which API key would add them."""
    shown = []
    monkeypatch.setattr(convert, 'show_currency_help', shown.append)
    monkeypatch.setattr(convert, 'is_running', lambda name: False)
    monkeypatch.setattr(convert, 'CRYPTO_API_KEY', None)
    monkeypatch.setattr(convert, 'OPENX_APP_KEY', None)
    monkeypatch.setattr(convert, 'OPENX_ONLY_CURRENCIES', {'XAU', 'XPD'})
    for unit in ('eth', 'xau', 'xpd'):
        with pytest.raises(SystemExit):
            convert.error_if_currency(unit)
    assert shown == ['CRYPTO_API_KEY', 'APP_KEY', 'APP_KEY']

    convert.error_if_currency('furlong')  # not a currency
    convert.error_if_currency('zmw')  # the free source has it: no key helps
    monkeypatch.setattr(convert, 'is_running', lambda name: True)
    convert.error_if_currency('eth')  # rates are still downloading
    monkeypatch.setattr(convert, 'is_running', lambda name: False)
    monkeypatch.setattr(convert, 'CRYPTO_API_KEY', 'key')
    monkeypatch.setattr(convert, 'OPENX_APP_KEY', 'key')
    convert.error_if_currency('eth')  # key already set
    convert.error_if_currency('xau')
    assert len(shown) == 3


def test_rate_sources_change_clears_cache(tmp_path, monkeypatch):
    """Setting or removing an API key clears cached exchange rates."""
    wf = FakeWorkflow(tmp_path)
    monkeypatch.setattr(convert, 'CRYPTO_API_KEY', None)
    convert.clear_rates_if_sources_changed(wf)  # no sources recorded yet
    wf.cache_data(convert.CURRENCY_CACHE_NAME, {})
    convert.clear_rates_if_sources_changed(wf)  # unchanged
    assert convert.CURRENCY_CACHE_NAME in wf.saved

    monkeypatch.setattr(convert, 'CRYPTO_API_KEY', 'key')
    convert.clear_rates_if_sources_changed(wf)
    assert convert.CURRENCY_CACHE_NAME not in wf.saved


def test_failed_update_waits_before_retrying(monkeypatch):
    """Offline, don't start a new download on every keystroke."""
    started = []
    monkeypatch.setattr(convert, 'run_in_background',
                        lambda name, cmd: started.append(cmd))
    wf = FakeWorkflow()
    attempt = convert.CURRENCY_ATTEMPT_CACHE_NAME
    convert.start_update(wf)
    convert.start_update(wf)  # first download failed: rates still stale
    assert len(started) == 1

    wf.saved[attempt] -= convert.CURRENCY_RETRY_DELAY
    convert.start_update(wf)
    assert len(started) == 2

    wf.cache_data(convert.CURRENCY_CACHE_NAME, {})  # rates are fresh
    wf.saved[attempt] -= convert.CURRENCY_RETRY_DELAY
    convert.start_update(wf)
    assert len(started) == 2


if __name__ == '__main__':  # pragma: no cover
    pytest.main([__file__])
