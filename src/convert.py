#!/usr/bin/env python3
# encoding: utf-8
#
# Copyright  (c) 2014 deanishe@deanishe.net
#
# MIT Licence. See http://opensource.org/licenses/MIT
#
# Created on 2014-02-24
#

"""Drives Script Filter to show unit conversions in Alfred 3."""

from __future__ import print_function

from collections import namedtuple
import os
import sys

from pint import UnitRegistry, UndefinedUnitError, DimensionalityError

from workflow import Workflow, ICON_WARNING, ICON_INFO
from workflow.background import run_in_background, is_running
from config import (
    bootstrap,
    DEFAULT_UNIT_DEFINITIONS,
    BUILTIN_UNIT_DEFINITIONS,
    COPY_UNIT,
    CRYPTO_API_KEY,
    CRYPTO_CURRENCIES,
    CURRENCIES,
    CURRENCY_ATTEMPT_CACHE_NAME,
    CURRENCY_CACHE_AGE,
    CURRENCY_CACHE_NAME,
    CURRENCY_DECIMAL_PLACES,
    CURRENCY_HELP_URL,
    CURRENCY_RETRY_DELAY,
    CUSTOM_DEFINITIONS_FILENAME,
    DECIMAL_PLACES,
    DECIMAL_SEPARATOR,
    DEFAULT_SETTINGS,
    DYNAMIC_DECIMALS,
    HELP_URL,
    OPENX_APP_KEY,
    OPENX_ONLY_CURRENCIES,
    SOURCES_FILENAME,
    THOUSANDS_SEPARATOR,
)
from defaults import Defaults

log = None

# Pint objects
ureg = None
# Q = ureg.Quantity


def open_currency_instructions():
    """Magic action to open help in browser."""
    import webbrowser
    webbrowser.open(CURRENCY_HELP_URL)
    return 'Opening instructions in browser...'


def error_if_currency(unit):
    """Show which API key is needed if ``unit`` is an unavailable currency."""
    if is_running('update'):  # rates may just not be downloaded yet
        return

    unit = unit.upper()
    # Check APP_KEY first: here XPD is palladium, not the PetroDollar coin
    if unit in OPENX_ONLY_CURRENCIES and not OPENX_APP_KEY:
        setting = 'APP_KEY'
    elif unit in CRYPTO_CURRENCIES and not CRYPTO_API_KEY:
        setting = 'CRYPTO_API_KEY'
    else:
        return

    log.error('[parser] unit %s is a currency without rates: set %s',
              unit, setting)
    show_currency_help(setting)
    sys.exit(0)


def show_currency_help(setting):
    """Show a message in Alfred telling user to set ``setting``."""
    wf.add_item('Set {} to convert this currency'.format(setting),
                'Action this item for instructions',
                autocomplete='workflow:appkey',
                icon=ICON_WARNING)

    wf.send_feedback()


def clear_rates_if_sources_changed(wf):
    """Clear cached exchange rates if the configured rate sources changed.

    E.g. the user has just set or removed ``APP_KEY`` or ``CRYPTO_API_KEY``,
    so cached rates are from the wrong sources until they expire.

    """
    path = wf.cachefile(SOURCES_FILENAME)
    sources = 'openx={} crypto={}'.format(bool(OPENX_APP_KEY),
                                          bool(CRYPTO_API_KEY))
    if os.path.exists(path):
        with open(path) as fp:
            if fp.read() == sources:
                return

    wf.cache_data(CURRENCY_CACHE_NAME, None)
    # Fetch now, don't wait to retry
    wf.cache_data(CURRENCY_ATTEMPT_CACHE_NAME, None)
    with open(path, 'w') as fp:
        fp.write(sources)
    log.debug('cleared cached exchange rates: sources are now %s', sources)


def start_update(wf):
    """Fetch exchange rates in the background if they're out of date.

    A failed download (e.g. offline) leaves the rates out of date, so
    only try again after ``CURRENCY_RETRY_DELAY`` seconds.

    """
    if (wf.cached_data_fresh(CURRENCY_CACHE_NAME, CURRENCY_CACHE_AGE) or
            wf.cached_data_fresh(CURRENCY_ATTEMPT_CACHE_NAME,
                                 CURRENCY_RETRY_DELAY)):
        return

    wf.cache_data(CURRENCY_ATTEMPT_CACHE_NAME, True)
    run_in_background('update', [sys.executable,
                                 wf.workflowfile('currency.py')])


class NoToUnits(Exception):
    """Raised if there are no to units (or defaults)."""


# Parsed user query
Input = namedtuple('Input', 'number dimensionality from_unit to_unit context')


class Formatter(object):
    """Format a number.

    Attributes:
        decimal_places (int): Number of decimal places in formatted numbers
        decimal_separator (str): Character to use as decimal separator
        thousands_separator (str): Character to use as thousands separator

    """

    def __init__(self, decimal_places=2, decimal_separator='.',
                 thousands_separator='', dynamic_decimals=True):
        """Create a new `Formatter`."""
        self.decimal_places = decimal_places
        self.decimal_separator = decimal_separator
        self.thousands_separator = thousands_separator
        self.dynamic_decimals = dynamic_decimals

    def _decimal_places(self, n):
        """Calculate the number of decimal places the result should have.

        If :attr:`dynamic_decimals` is `True`, increase the number of
        decimal places until two significant digits show (at most 10),
        without trailing zeros.

        Args:
            n (float): Number that will be formatted.

        Returns:
            int: Number of decimal places for result.

        """
        log.debug('DYNAMIC_DECIMALS: %s', ('off', 'on')[self.dynamic_decimals])

        if not self.dynamic_decimals or n == 0.0:
            return self.decimal_places

        p = self.decimal_places
        while p < 10 and abs(n) * 10 ** p < 10:
            p += 1

        if p > self.decimal_places:  # drop trailing zeros: 0.0040 -> 0.004
            digits = '{:.{}f}'.format(n, p).rstrip('0').split('.')[1]
            p = max(len(digits), self.decimal_places)

        log.debug('places=%d', p)
        return p

    def formatted(self, n, unit=None):
        """Format number with thousands and decimal separators."""
        sep = u''
        if self.thousands_separator:
            sep = u','

        fmt = u'{{:0{}.{:d}f}}'.format(sep, self._decimal_places(n))
        num = fmt.format(n)
        # log.debug('n=%r, fmt=%r, num=%r', n, fmt, num)
        num = num.replace(',', '||comma||')
        num = num.replace('.', '||point||')
        num = num.replace('||comma||', self.thousands_separator)
        num = num.replace('||point||', self.decimal_separator)

        if unit:
            num = u'{} {}'.format(num, unit)

        return num

    def formatted_no_thousands(self, n, unit=None):
        """Format number with decimal separator only."""
        fmt = u'{{:0.{:d}f}}'.format(self._decimal_places(n))
        num = fmt.format(n)
        # log.debug('n=%r, fmt=%r, num=%r', n, fmt, num)
        num = num.replace('.', '||point||')
        num = num.replace('||point||', self.decimal_separator)

        if unit:
            num = u'{} {}'.format(num, unit)

        return num


# Result of converting an `Input` to one unit
Conversion = namedtuple(
    'Conversion', 'from_number from_unit to_number to_unit dimensionality')


class Converter(object):
    """Parse query and convert.

    Parses user input into an `Input` object, then converts this into
    one or more `Conversion` objects.

    Attributes:
        decimal_separator (str): Decimal separator character in input.
        defaults (defaults.Defaults): Default units for conversions.
        thousands_separator (str): Thousands separator character in input.

    """

    def __init__(self, defaults, decimal_separator='.',
                 thousands_separator=','):
        """Create new `Converter`.

        Args:
            defaults (defaults.Defaults): Default units for conversions.
            decimal_separator (str, optional): Decimal separator character
                in query.
            thousands_separator (str, optional): Thousands separator character
                in query.

        """
        self.defaults = defaults
        self.decimal_separator = decimal_separator
        self.thousands_separator = thousands_separator

    def convert(self, i):
        """Convert `Input`.

        Args:
            i (Input): Parsed user query

        Returns:
            list: Sequence of `Conversion` objects

        Raises:
            NoToUnits: Raised if user hasn't specified a destination unit
                or there are no default units for the given dimensionality
            ValueError: Raised if a unit is unknown

        """
        if i.to_unit is not None:
            units = [i.to_unit]
        else:
            units = self.defaults.defaults(i.dimensionality)

        results = []
        qty = ureg.Quantity(i.number, i.from_unit)
        for u in units:
            try:
                to_unit = ureg.Quantity(1, u)
            except UndefinedUnitError:
                error_if_currency(u)
                raise ValueError('Unknown unit: {}'.format(u))

            # Skip defaults that are the input unit under another name,
            # e.g. a saved "degF" when the input is "degree_Fahrenheit"
            if i.to_unit is None and to_unit.units == qty.units:
                continue

            conv = qty.to(to_unit)
            log.debug('[convert] %s -> %s = %s', i.from_unit, u, conv)
            results.append(Conversion(i.number, i.from_unit,
                                      conv.magnitude, u, i.dimensionality))

        if not results:
            raise NoToUnits()

        return results

    def parse(self, query):
        """Parse user query into `Input`.

        Args:
            query (str): User query

        Returns:
            Input: Parsed query

        Raises:
            ValueError: Raised if query is invalid

        """
        ctx, query = self.parse_context(query)
        qty, tail = self.parse_quantity(query)

        # Show error message for invalid input
        if qty is None:
            if ctx:
                raise ValueError('No quantity')

            raise ValueError('Start your query with a number')

        if not len(tail):
            raise ValueError('No units specified')

        log.debug('[parser] quantity=%s, tail=%s', qty, tail)

        # Parse query into pint.Quantity objects
        from_unit, to_unit = self.parse_units(tail, qty)

        # Create `Input` from parsed query
        tu = None
        # Pint raises on bool() of offset units (degC, degF)
        if to_unit is not None:
            tu = str(to_unit.units)
        i = Input(from_unit.magnitude, str(from_unit.dimensionality),
                  str(from_unit.units), tu, ctx)

        log.debug('[parser] %s', i)

        return i

    def parse_context(self, query):
        """Extract and set context.

        Args:
            query (str): User input

        Returns:
            (list/str, str): Parsed or empty context and rest of query

        Raises:
            ValueError: Raised if supplied context is invalid

        """
        ctx = []
        for c in query:
            if c in 'abcdefghijklmnopqrstuvwxyz':
                ctx.append(c)
            else:
                break

        if ctx:
            ctx = ''.join(ctx)
            try:
                ureg.enable_contexts(ctx)
            except KeyError:
                raise ValueError('Unknown context: {}'.format(ctx))

            log.debug('[parser] context=%s', ctx)
            query = query[len(ctx):].strip()

        return ctx, query

    def parse_quantity(self, query):
        """Extract quantity from query.

        Args:
            query (str): (Partial) user query

        Returns:
            (float, str): Quantity and remainder of query

        """
        qty = []
        qtychars = ('+-1234567890' + self.thousands_separator +
                    self.decimal_separator)
        for c in query:
            if c in qtychars:
                if c == '+':
                    qty.append('')
                elif c == self.thousands_separator:
                    log.debug('ignored thousands separator "%s"', c)
                    # Append an empty string so qty length is correct
                    qty.append('')
                elif c == self.decimal_separator:
                    qty.append('.')
                else:
                    qty.append(c)
            else:
                break
        if not len(qty):
            return None, ''

        tail = query[len(qty):].strip()
        qty = float(''.join(qty))

        return qty, tail

    def parse_units(self, query, qty=1):
        """Extract from and (optional) to units from query.

        Args:
            query (str): (Partial) user input
            qty (int, optional): Quantity of from units

        Returns:
            (pint.Quantity, pint.Quantity): From and to quantities. To
                quantity is initialised with ``1``.

        Raises:
            ValueError: Raised if a unit is unknown, or more than 2 units
                are specified.

        """
        from_unit = to_unit = None
        units = [s.strip() for s in query.split()]
        from_unit = units[0]
        log.debug('[parser] from_unit=%s', from_unit)

        if len(units) > 1:
            to_unit = units[1]
            log.debug('[parser] to_unit=%s', to_unit)
        if len(units) > 2:
            raise ValueError('More than 2 units specified')

        # Validate units
        try:
            from_unit = ureg.Quantity(qty, from_unit)
        except UndefinedUnitError:
            error_if_currency(from_unit)
            raise ValueError('Unknown unit: ' + from_unit)

        if to_unit:
            try:
                to_unit = ureg.Quantity(1, to_unit)
            except UndefinedUnitError:
                error_if_currency(to_unit)
                raise ValueError('Unknown unit: ' + to_unit)

        return from_unit, to_unit


def register_units():
    """Add built-in and user units to unit registry.

    Returns:
        str: The user's unit definitions, without comments.

    """
    # Add custom units from workflow and user data
    ureg.load_definitions(BUILTIN_UNIT_DEFINITIONS)

    user_definitions = wf.datafile(CUSTOM_DEFINITIONS_FILENAME)

    # User's custom units
    if not os.path.exists(user_definitions):
        return ''

    ureg.load_definitions(user_definitions)
    with open(user_definitions) as fp:
        return ''.join(line.split('#')[0] for line in fp)


def register_exchange_rates(exchange_rates):
    """Add currency definitions with exchange rates to unit registry.

    Args:
        exchange_rates (dict): `{symbol: rate}` mapping of currencies.

    """
    # USD will be the baseline currency. All exchange rates are
    # defined relative to the US dollar
    ureg.define('USD = [currency] = usd')

    for abbr, rate in exchange_rates.items():
        # Old caches may hold names like "STR*". Pint raises AssertionError
        # on these, not the UndefinedUnitError caught below.
        if not abbr.isidentifier():
            log.warning('skipping currency %r : not a valid unit name', abbr)
            continue

        definition = '{} = usd / {}'.format(abbr, rate)

        try:
            ureg.Quantity(1, abbr)
        except UndefinedUnitError:
            pass  # Unit does not exist
        else:
            log.debug('skipping currency %s : Unit is already defined', abbr)
            continue

        # A fiat code beats a name Pint only gets via a prefix, e.g. "php"
        # (picohorsepower); an exact unit name such as "cup" still wins
        found = ureg.parse_unit_name(abbr.lower())
        if not found or (abbr in CURRENCIES and
                         all(prefix for prefix, _, _ in found)):
            definition += ' = {}'.format(abbr.lower())

        log.debug('registering currency : %r', definition)
        try:
            ureg.define(definition)
        except Exception as err:  # one bad rate mustn't break all conversions
            log.error('skipping currency %r : %s', definition, err)


def convert(query):
    """Perform conversion and send results to Alfred."""
    error = None
    results = None

    defs = Defaults(wf)
    c = Converter(defs, DECIMAL_SEPARATOR, THOUSANDS_SEPARATOR)

    try:
        i = c.parse(query)
    except ValueError as err:
        log.critical(u'invalid query (%s): %s', query, err)
        error = str(err)

    else:
        try:
            results = c.convert(i)
            # log.debug('results=%r', results)
        except NoToUnits:
            log.critical(u'No to_units (or defaults) for %s', i.dimensionality)
            error = u'No destination units (or defaults) for {}'.format(
                i.dimensionality)

        except DimensionalityError as err:
            log.critical(u'invalid conversion (%s): %s', query, err)
            error = u"Can't convert from {} {} to {} {}".format(
                err.units1, err.dim1, err.units2, err.dim2)

        except KeyError as err:
            log.critical(u'invalid context (%s): %s', i.context, err)
            error = u'Unknown context: {}'.format(i.context)

    if not error and not results:
        error = 'Conversion input not understood'

    if error:  # Show error
        wf.add_item(error,
                    'For example: 2.5cm in  |  178lb kg  |  200m/s mph',
                    valid=False, icon=ICON_WARNING)

    else:  # Show results
        p = (CURRENCY_DECIMAL_PLACES if i.dimensionality == '[currency]'
             else DECIMAL_PLACES)
        f = Formatter(p, DECIMAL_SEPARATOR, THOUSANDS_SEPARATOR,
                      DYNAMIC_DECIMALS)
        wf.setvar('query', query)
        for conv in results:
            value = copytext = f.formatted(conv.to_number, conv.to_unit)
            arg = f.formatted_no_thousands(conv.to_number, conv.to_unit)
            if not COPY_UNIT:
                copytext = f.formatted(conv.to_number)
                arg = f.formatted_no_thousands(conv.to_number)

            it = wf.add_item(value,
                             valid=True,
                             arg=arg,
                             copytext=copytext,
                             largetext=value,
                             icon='icon.png')

            action = 'save'
            name = 'Save'
            if defs.is_default(conv.dimensionality, conv.to_unit):
                action = 'delete'
                name = 'Remove'

            mod = it.add_modifier(
                'cmd',
                u'{} {} as default unit for {}'.format(
                    name, conv.to_unit, conv.dimensionality))
            mod.setvar('action', action)
            mod.setvar('unit', conv.to_unit)
            mod.setvar('dimensionality', conv.dimensionality)

    wf.send_feedback()
    log.debug('finished')
    return 0


def main(wf):
    """Run workflow Script Filter.

    Args:
        wf (workflow.Workflow): Current Workflow object.

    """
    global ureg
    # Cache parsed definitions: saves ~80 ms per keystroke
    ureg = UnitRegistry(DEFAULT_UNIT_DEFINITIONS,
                        cache_folder=wf.cachefile('pint'))
    ureg.formatter.default_format = 'P'

    wf.magic_arguments['appkey'] = open_currency_instructions

    if not len(wf.args):
        return

    query = wf.args[0]  # .lower()
    log.debug('query : %s', query)

    clear_rates_if_sources_changed(wf)
    # Create data files if necessary
    bootstrap(wf)

    # Add workflow and user units to unit registry
    custom_units = register_units()

    # Load cached data
    exchange_rates = wf.cached_data(CURRENCY_CACHE_NAME, max_age=0)

    # Defining ~190 currencies costs ~40 ms, so only do it when the query or
    # a custom unit (e.g. "bigmac = 5.69 USD") may use one. Substrings keep
    # "1 kEUR usd" working; a false match only costs time.
    text = (query + custom_units).lower()
    if exchange_rates and any(s.lower() in text for s in exchange_rates):
        register_exchange_rates(exchange_rates)

    start_update(wf)

    if is_running('update'):
        wf.rerun = 0.5
        if exchange_rates is None:  # No data cached yet
            wf.add_item(u'Fetching exchange rates…',
                        'Currency conversions will be momentarily possible',
                        icon=ICON_INFO)
        else:
            wf.add_item(u'Updating exchange rates…',
                        icon=ICON_INFO)

    return convert(query)


if __name__ == '__main__':
    wf = Workflow(default_settings=DEFAULT_SETTINGS, help_url=HELP_URL)
    log = wf.logger
    sys.exit(wf.run(main))
