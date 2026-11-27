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


T = namedtuple('T', 'number dimensionality from_unit to_units')
C = convert.Conversion


class FakeWorkflow:
    """Just enough of `workflow.Workflow`: settings, cache and results."""

    def __init__(self, tmp_path=None):
        self.dir = tmp_path
        self.settings = {}
        self.saved = {}  # cache name -> time saved
        self.items = []  # results shown in Alfred
        self.age = 0  # of the cached exchange rates

    def add_item(self, title, subtitle='', **kwargs):
        self.items.append(dict(kwargs, title=title, subtitle=subtitle))
        return self  # also stands in for the item

    def add_modifier(self, *args, **kwargs):
        return self

    def setvar(self, name, value):
        pass

    def send_feedback(self):
        pass

    def cached_data_age(self, name):
        return self.age

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
        '-',  # half-typed: "-40 degC degF"
        '20.5 m/',  # half-typed: "20.5 m/s kph"
        '1 m)',
        '1 m ft-in',  # Pint raises TypeError on "+" or "-" between units
        '1 m ft+',  # half-typed: "1 m ft+in"
    ]
    c = convert.Converter(None)
    for query in queries:
        with pytest.raises(ValueError):
            c.parse(query)


def test_valid():
    """Test valid input."""
    data = [
        ('1.3 km', T(1.3, '[length]', 'kilometer', None)),
        ('1.3 km miles', T(1.3, '[length]', 'kilometer', ['mile'])),
        ('5 m/s kph', T(5.0, '[length] / [time]', 'meter/second',
                        ['kilometer_per_hour'])),
        ('21.3 m^2 acres', T(21.3, '[length] ** 2', 'meter²', ['acre'])),
        ('+5km m', T(5.0, '[length]', 'kilometer', ['meter'])),
        ('1 km to mi', T(1.0, '[length]', 'kilometer', ['mile'])),
        ('1 km in', T(1.0, '[length]', 'kilometer', ['inch'])),
        ('1 in in cm', T(1.0, '[length]', 'inch', ['centimeter'])),
        ('5 miles per hour kph', T(5.0, '[length] / [time]', 'mile/hour',
                                   ['kilometer_per_hour'])),
        ('20 degC degF', T(20.0, '[temperature]', 'degree_Celsius',
                           ['degree_Fahrenheit'])),
        ('1 kg lb oz', T(1.0, '[mass]', 'kilogram', ['pound', 'ounce'])),
        ('1 kg to lb oz', T(1.0, '[mass]', 'kilogram', ['pound', 'ounce'])),
        ('1.8 m ft+in', T(1.8, '[length]', 'meter', ['foot+inch'])),
    ]
    c = convert.Converter(None)
    for t in data:
        assert c.parse(t[0])[:4] == t[1]  # all fields but context


def test_mixed_input():
    """5'10", 5 ft 10 in and 5ft10in are all 70 inches."""
    c = convert.Converter(None)
    for query in ('5 ft 10 in cm', '5ft10in cm', '5\'10" cm', '5′10″ cm',
                  '5ft 10in to cm'):
        i = c.parse(query)
        assert (i.number, i.from_unit, i.to_units) == (
            pytest.approx(70 / 12), 'foot', ['centimeter'])
    assert c.parse('1h30min')[:3] == (1.5, '[time]', 'hour')
    assert c.parse('-1 h 30 min').number == -1.5
    assert c.parse('1 cmH2O').from_unit == 'centimeter_H2O'  # not split
    for query, error in [('5 ft 10', 'No unit after 10'),
                         ('5 ft 10 kg', "Can't add kg to ft"),
                         ('20 degC 5 degF', "Can't add")]:
        with pytest.raises(ValueError, match=error):
            c.parse(query)


def test_contexts():
    """A context's name can start with a capital, e.g. "Gaussian"."""
    c = convert.Converter(None)
    try:
        assert c.parse('Gau 1 T G').context == 'Gau'
        [conv] = c.convert(c.parse('Gau 1 T G'))
        assert conv.to_number == pytest.approx(10000)
    finally:
        convert.ureg.disable_contexts()


def test_number_formats():
    """Scientific notation, fractions and the web's minus sign "−"."""
    c = convert.Converter(None)
    for query, number, rest in [
            ('1e3 m', 1000, 'm'),
            ('1.5E-6m', 1.5e-6, 'm'),
            ('−40 degC', -40, 'degC'),
            ('1/2 cup', 0.5, 'cup'),
            ('1 1/2 cups', 1.5, 'cups'),
            ('½ cup', 0.5, 'cup'),
            ('-1½cup', -1.5, 'cup'),
            ('2 ¾ cup', 2.75, 'cup'),
            ('1e C', 1, 'e C'),  # 1 elementary charge
            ('3/0 m', 3, '/0 m')]:  # not a fraction
        assert c.parse_quantity(query) == (number, rest)


def test_thousands_separators():
    """A thousands separator needs 3 digits after it, so "1,5" isn't 15."""
    c = convert.Converter(None)
    assert c.parse_quantity('1,500.5 m') == (1500.5, 'm')
    assert c.parse_quantity('-.5m') == (-0.5, 'm')
    for query in ('1,5 m', '1,5000 m', '1,500,00 m'):
        with pytest.raises(ValueError):
            c.parse_quantity(query)

    c = convert.Converter(None, decimal_separator=',',
                          thousands_separator='.')
    assert c.parse_quantity('1.500,5 m') == (1500.5, 'm')
    with pytest.raises(ValueError):
        c.parse_quantity('1.5 m')


def test_units_with_numbers():
    """A unit can hold a number: "l/100km" is liters per 100 km."""
    c = convert.Converter(None)
    i = c.parse('7 l/100km l/km')
    assert (i.number, i.from_unit) == (pytest.approx(0.07), 'liter/kilometer')
    [conv] = c.convert(c.parse('30 kWh/100mi kWh/100km'))
    assert conv.to_unit == 'kWh/100km'  # as typed: Pint's name drops 100
    assert conv.to_number == pytest.approx(18.64, abs=0.01)
    for query in ('2 m to 3', '1 l/0km l/km', '.5.5 m'):
        with pytest.raises(ValueError, match='Unknown unit'):
            c.parse(query)


def test_reciprocal_units():
    """Pace and speed, or fuel economy and consumption, are inverses."""
    c = convert.Converter(None)
    for query, number in [('5 min/km km/h', 12), ('10 mph min/mi', 6),
                          ('30 mi/gal l/100km', 7.84), ('50 Hz ms', 20)]:
        [conv] = c.convert(c.parse(query))
        assert conv.to_number == pytest.approx(number, abs=0.01)
    for query in ('0 mph min/mi', '1 m s'):  # 1/0, and not inverses
        with pytest.raises(convert.DimensionalityError):
            c.convert(c.parse(query))


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


def test_starter_defaults():
    """Common dimensionalities have defaults until the user saves some."""
    wf = FakeWorkflow()
    defs = Defaults(wf)
    assert defs.defaults('[mass]') == ['gram', 'kilogram', 'ounce', 'pound']
    defs.remove('[mass]', 'ounce')
    assert Defaults(wf).defaults('[mass]') == ['gram', 'kilogram', 'pound']
    for unit in ('gram', 'kilogram', 'pound'):
        defs.remove('[mass]', unit)
    assert Defaults(wf).defaults('[mass]') == []  # starters don't return
    assert Defaults(FakeWorkflow()).defaults('[mass]') == [
        'gram', 'kilogram', 'ounce', 'pound']

    # A default that's gone, e.g. a deleted custom unit, is skipped
    wf.settings['default_units'] = {'[length]': ['furlongz', 'meter']}
    c = convert.Converter(Defaults(wf))
    assert [r.to_unit for r in c.convert(c.parse('1 km'))] == ['meter']


def test_dimension_names():
    """Messages name dimensionalities, e.g. "area" for "[length] ** 2"."""
    for dimensionality, name in [
            ('[length]', 'length'),
            ('[length] ** 2', 'area'),
            ('[length] ** 3 / [time]', 'volumetric flow rate'),
            ('[time] / [length]', 'time / length'),  # not Gaussian
            ('[currency] / [mass]', 'currency / mass'),
            ('dimensionless', 'dimensionless')]:
        assert convert.dimension_name(dimensionality) == name


def test_formatter():
    """Dynamic decimals show 2 significant digits, negative numbers too."""
    f = convert.Formatter(2, '.', ',', dynamic_decimals=True)
    assert f.formatted(-1234.5) == '-1,234.50'
    assert f.formatted(-0.004) == '-0.004'
    assert f.formatted(0.004) == '0.004'
    assert f.formatted(0.015) == '0.015'
    assert f.formatted(0.0046) == '0.0046'
    assert f.formatted(1.5e-9) == '0.0000000015'
    assert f.formatted(1e-28) == '1.00e-28'  # not "0.00"
    assert f.formatted(-5e-10) == '-5.00e-10'

    # Mixed units: the number is in the last unit
    assert f.formatted(70.866, 'foot+inch') == '5 ft 10.87 in'
    assert f.formatted(71.996, 'foot+inch') == '6 ft 0 in'  # not 12.00 in
    assert f.formatted(72.0000001, 'foot+inch') == '6 ft 0 in'
    assert f.formatted(-70.866, 'foot+inch') == '-5 ft 10.87 in'
    assert f.formatted(1e6, 'day+hour+minute+second') == (
        '11 d 13 h 46 min 40 s')

    # Pace in minutes and seconds
    assert f.formatted(8.0467, 'minute/mile') == '8:03 min/mi'
    assert f.formatted(5.9999, 'minute/kilometer') == '6:00 min/km'
    assert f.formatted(1.75, 'min/100m', show_unit=False) == '1:45'

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


def test_currency_symbols(monkeypatch):
    """Symbols stand for currency codes, before or after the number."""
    monkeypatch.setattr(convert, 'ureg',
                        convert.UnitRegistry(convert.DEFAULT_UNIT_DEFINITIONS))
    convert.ureg.formatter.default_format = 'P'
    convert.register_exchange_rates({'EUR': 0.5, 'GBP': 0.25})
    c = convert.Converter(None)
    for query, from_unit, to_units in [
            ('$100 eur', 'USD', ['EUR']),
            ('100€ usd', 'EUR', ['USD']),
            ('£5 $', 'GBP', ['USD']),
            ('5 $/lb €/kg', 'USD/pound', ['EUR/kilogram'])]:
        i = c.parse(query)
        assert (i.from_unit, i.to_units) == (from_unit, to_units)


@pytest.fixture(scope='module')
def workflow_ureg():
    """Unit registry as main() builds it, with the built-in units."""
    ureg = convert.UnitRegistry(convert.DEFAULT_UNIT_DEFINITIONS,
                                on_redefinition='ignore')
    ureg.formatter.default_format = 'P'
    ureg.load_definitions(convert.BUILTIN_UNIT_DEFINITIONS)
    return ureg


def show(query, monkeypatch, ureg, rates=None):
    """Return the results Alfred would show for ``query``."""
    wf = FakeWorkflow()
    wf.age = 3 * 3600 + 600
    monkeypatch.setattr(convert, 'wf', wf, raising=False)
    for name, value in [('DECIMAL_PLACES', 2), ('CURRENCY_DECIMAL_PLACES', 2),
                        ('DECIMAL_SEPARATOR', '.'),
                        ('THOUSANDS_SEPARATOR', ','),
                        ('DYNAMIC_DECIMALS', True), ('COPY_UNIT', False)]:
        monkeypatch.setattr(convert, name, value)
    monkeypatch.setattr(convert, 'ureg', ureg)
    if rates:
        convert.register_exchange_rates(rates)
    convert.convert(query)
    return wf.items


def test_currency_subtitle(monkeypatch, workflow_ureg):
    """Currency results show the rate, and how old the rates are."""
    [item] = show('10 eur usd', monkeypatch, workflow_ureg, {'EUR': 0.5})
    assert item['subtitle'] == (
        '1 EUR = 2.00 USD · rates updated 3 hours 10 minutes ago')
    [item] = show('10 km mi', monkeypatch, workflow_ureg)
    assert item['subtitle'] == ''


def test_kitchen_fractions(monkeypatch, workflow_ureg):
    """Cups and spoons show the nearest amount a measuring cup has."""
    for query, title, subtitle in [
            ('100 ml cup', '0.42 cup', '≈ ⅜ cup'),
            ('1 l cup', '4.23 cup', '≈ 4¼ cup'),
            ('1.5 tbsp tsp', '4.50 tsp', '≈ 4½ tsp'),
            ('2 tbsp cup', '0.12 cup', '≈ ⅛ cup'),
            ('1 ml cup', '0.0042 cup', '')]:  # nearest is 0
        [item] = show(query, monkeypatch, workflow_ureg)
        assert (item['title'], item['subtitle']) == (title, subtitle)


def test_below_absolute_zero(monkeypatch, workflow_ureg):
    """Temperatures below absolute zero convert, with a warning."""
    for query, subtitle in [
            ('-300 degC K', 'Below absolute zero: colder than physics allows'),
            ('-5 K degC', 'Below absolute zero: colder than physics allows'),
            ('-40 degC degF', ''),
            ('-300 delta_degC delta_degF', '')]:  # a change, not a reading
        [item] = show(query, monkeypatch, workflow_ureg)
        assert item['subtitle'] == subtitle


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
