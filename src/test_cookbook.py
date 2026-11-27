#!/usr/bin/env python3
#
# MIT Licence. See http://opensource.org/licenses/MIT
#

"""Test that every example in docs/cookbook.md shows what Alfred shows.

Examples are "conv <query> → <result>" lines in the doc's ```text blocks,
with any further results of the query on the next "→ <result>" lines. The
doc's ```ini blocks hold custom units, and its tables set the exchange
rates and saved default units the examples use.
"""

import contextlib
import logging
import os
import plistlib
import re

import pytest

import convert

convert.log = logging.getLogger('convert')

here = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(here, '..', 'docs', 'cookbook.md'),
          encoding='utf-8') as fp:
    DOC = fp.read()
with open(os.path.join(here, 'info.plist'), 'rb') as fp:
    SETTINGS = plistlib.load(fp)['variables']

# The workflow's default settings, read the way config.py reads them
WORKFLOW_DEFAULTS = {
    'DECIMAL_PLACES': int(SETTINGS['DECIMAL_PLACES']),
    'CURRENCY_DECIMAL_PLACES': int(SETTINGS['CURRENCY_DECIMAL_PLACES']),
    'DECIMAL_SEPARATOR': SETTINGS['DECIMAL_SEPARATOR'],
    'THOUSANDS_SEPARATOR': SETTINGS['THOUSANDS_SEPARATOR'],
    'DYNAMIC_DECIMALS': SETTINGS['DYNAMIC_DECIMALS'] not in ('', '0'),
    'OPENX_APP_KEY': SETTINGS['APP_KEY'] or None,
    'CRYPTO_API_KEY': SETTINGS['CRYPTO_API_KEY'] or None,
}

BLOCKS = re.findall(r'^```(\w*)\n(.*?)^```$', DOC, re.M | re.S)
RATES = {symbol: float(rate) for symbol, rate in
         re.findall(r'^\| ([A-Z]{3}) +\| ([\d.]+) +\|$', DOC, re.M)}
DEFAULTS = {dim: re.findall(r'`([^`]+)`', units) for dim, units in
            re.findall(r'^\| `(\[[^`]+\])` +\| (.+?) +\|$', DOC, re.M)}


def parse_examples():
    """Return ``(query, [result, ...])`` for each example in the doc."""
    examples = []
    for lang, body in BLOCKS:
        if lang != 'text':
            continue
        for line in body.splitlines():
            query, arrow, result = line.partition('→')
            if query.startswith('conv ') and arrow:
                examples.append((query[5:].strip(), [result.strip()]))
            elif arrow and not query.strip() and examples:
                examples[-1][1].append(result.strip())
            elif line.strip():
                raise ValueError('not an example: ' + line)
    return examples


EXAMPLES = parse_examples()


class FakeWorkflow(object):
    """Records the titles of the results Alfred would show."""

    def __init__(self):
        self.settings = {'default_units': DEFAULTS}
        self.titles = []

    def add_item(self, title, *args, **kwargs):
        self.titles.append(title)
        return self  # also stands in for the item

    def add_modifier(self, *args, **kwargs):
        return self

    def setvar(self, name, value):
        pass

    def send_feedback(self):
        pass

    def cached_data_age(self, name):
        return 0


@pytest.fixture(scope='module')
def ureg():
    """Unit registry as main() builds it, with the doc's units and rates."""
    old = convert.ureg
    convert.ureg = convert.UnitRegistry(convert.DEFAULT_UNIT_DEFINITIONS,
                                        on_redefinition='ignore')
    convert.ureg.formatter.default_format = 'P'
    convert.ureg.load_definitions(convert.BUILTIN_UNIT_DEFINITIONS)
    for lang, body in BLOCKS:
        if lang == 'ini':
            convert.ureg.load_definitions(body.splitlines())
    convert.register_exchange_rates(RATES)
    yield convert.ureg
    convert.ureg = old


def test_every_example_is_checked():
    """Every "conv" line is in a ```text block, so test_example runs it."""
    assert EXAMPLES and DOC.count('\nconv ') == len(EXAMPLES)


@pytest.mark.parametrize('query, results', EXAMPLES,
                         ids=[query for query, _ in EXAMPLES])
def test_example(query, results, ureg, monkeypatch):
    """The query shows the results the cookbook says it does."""
    wf = FakeWorkflow()
    monkeypatch.setattr(convert, 'wf', wf, raising=False)
    monkeypatch.setattr(convert, 'is_running', lambda name: False)
    for name, value in WORKFLOW_DEFAULTS.items():
        monkeypatch.setattr(convert, name, value)

    try:
        with contextlib.suppress(SystemExit):  # after an API key message
            convert.convert(query)
    finally:
        ureg.disable_contexts()  # "sp ..." leaves its context enabled

    assert wf.titles == results


if __name__ == '__main__':  # pragma: no cover
    pytest.main([__file__])
