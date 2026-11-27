#!/usr/bin/env python3
#
# Copyright  (c) 2014 deanishe@deanishe.net
#
# MIT Licence. See http://opensource.org/licenses/MIT
#
# Created on 2014-02-24
#

"""Drives Script Filter to show unit conversions in Alfred 3."""

from collections import namedtuple
import math
import os
import re
import sys
from tokenize import TokenError
import unicodedata

from pint import (UnitRegistry, UndefinedUnitError, DimensionalityError,
                  DefinitionSyntaxError)

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
    CURRENCY_SYMBOLS,
    CURRENCY_RETRY_DELAY,
    CUSTOM_DEFINITIONS_FILENAME,
    DECIMAL_PLACES,
    DECIMAL_SEPARATOR,
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


VULGAR_FRACTIONS = '¼½¾⅐⅑⅒⅓⅔⅕⅖⅗⅘⅙⅚⅛⅜⅝⅞'

# Number at the start of a query. "−" is the minus sign web pages use.
# {t} and {d} are the thousands and decimal separators.
NUMBER = (
    r'(?P<sign>[-+−]?)(?:'
    r'(?:(?P<whole>\d+) +)?(?P<num>\d+)/(?P<den>[1-9]\d*)'  # 1/2, 1 1/2
    r'|(?P<int>\d*) ?(?P<vulgar>[' + VULGAR_FRACTIONS + '])'  # ½, 1½
    # 5, .5, 1,500.5, 1e-3: a digit first or after the decimal separator
    r'|(?P<dec>(?={d}?\d)\d*(?:{t}\d{{3}}(?!\d))*(?:{d}\d*)?'
    r'(?:[eE][-+−]?\d+)?))'
)


class NoToUnits(Exception):
    """Raised if there are no to units (or defaults)."""


# Replaces currency symbols with codes, e.g. "$" with "USD"
SYMBOLS = str.maketrans(CURRENCY_SYMBOLS)

# Parsed user query
Input = namedtuple('Input', 'number dimensionality from_unit to_units context')


class Formatter:
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

    def formatted(self, n, unit=None, thousands=True, show_unit=True):
        """Format number with separators, and ``unit`` as its symbol.

        For mixed units such as "foot+inch", ``n`` is in the last unit,
        and the result always shows each unit, e.g. "5 ft 10.87 in". A
        pace in minutes per distance shows minutes and seconds, e.g.
        "8:03 min/mi".

        """
        if unit and '+' in unit:
            units = unit.split('+')
            numbers = split(abs(n), units, self.decimal_places)
            return ('-' if n < 0 else '') + ' '.join(
                self.formatted(x, u, thousands)
                for x, u in zip(numbers, units))

        if unit and unit.startswith(('minute/', 'min/')) and n >= 0:
            num = '{}:{:02d}'.format(*divmod(round(n * 60), 60))
        elif self.dynamic_decimals and 0 < abs(n) < 1e-9:
            # 10 decimal places can't show 2 significant digits
            num = '{:.{}e}'.format(n, self.decimal_places)
        else:
            sep = ',' if thousands and self.thousands_separator else ''
            # Whole numbers from split() have no decimals
            places = 0 if isinstance(n, int) else self._decimal_places(n)
            num = '{:{}.{}f}'.format(n, sep, places)
        # One pass, so swapping "," and "." (e.g. 1.234,50) works
        num = num.translate({ord(','): self.thousands_separator,
                             ord('.'): self.decimal_separator})
        return '{} {}'.format(num, symbol(unit)) if unit and show_unit else num


# Result of converting an `Input` to one unit
Conversion = namedtuple(
    'Conversion', 'from_number from_unit to_number to_unit dimensionality')


def quantity(number, unit):
    """Return ``ureg.Quantity(number, unit)``.

    ``unit`` may contain a number, e.g. "l/100km" (liters per 100 km), so
    the quantity's magnitude is ``number`` times its scale.

    Raises:
        ValueError: Raised if ``unit`` is unknown or half-typed, e.g. "m/".

    """
    try:
        try:
            return ureg.Quantity(number, unit)
        except ValueError:  # Pint won't take a number in a unit
            # It reads "l/100km" as (l/100)*km, so wrap what follows "/"
            scaled = ureg.parse_expression(re.sub(
                r'/(\d+(?:\.\d+)?)\s*([^\W\d]\w*)', r'/(\1 \2)', unit))
            if isinstance(scaled, ureg.Quantity):  # not just a number, "3"
                return number * scaled
    # Pint's parser raises the others on half-typed units, e.g. "m/", "m)",
    # "ft-in" or "l/0"
    except (UndefinedUnitError, AssertionError, TokenError,
            DefinitionSyntaxError, TypeError, ZeroDivisionError):
        pass
    error_if_currency(unit)
    raise ValueError('Unknown unit: {}'.format(unit))


def split(total, units, places):
    """Split ``total`` of the last of ``units`` into whole larger units.

    E.g. 70.87 inches across "foot" and "inch" is ``[5, 10.87]``.

    """
    total = round(total, places)  # as shown, so 71.996 in isn't 5 ft 12 in
    numbers = []
    for unit in units[:-1]:
        factor = quantity(1, unit).to(units[-1]).magnitude
        n = math.floor(round(total / factor, 9))  # 5.999999999999999 is 6
        numbers.append(n)
        total = max(0.0, round(total - n * factor, places))  # not -0.0
    return numbers + [int(total) if total.is_integer() else total]


def symbol(unit):
    """Return the short name to show for ``unit``, e.g. "°F" for "degF"."""
    if isinstance(unit, str) and '+' in unit:  # mixed units, e.g. "ft+in"
        return '+'.join(symbol(u) for u in unit.split('+'))
    try:
        # Pint formats dimensionless as ""
        return '{:~P}'.format(ureg.Unit(unit)) or str(unit)
    except ValueError:  # a number in the unit, e.g. "l/100km": show as typed
        return unit


class Converter:
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
        units = i.to_units or self.defaults.defaults(i.dimensionality)

        results = []
        qty = ureg.Quantity(i.number, i.from_unit)
        for u in units:
            # Mixed units such as "foot+inch" convert to the last one.
            # Magnitude 0.01 for "l/100km".
            to_unit = quantity(1, u.split('+')[-1])

            # Skip defaults that are the input unit under another name,
            # e.g. a saved "degF" when the input is "degree_Fahrenheit"
            if not i.to_units and to_unit.units == qty.units and '+' not in u:
                continue

            try:
                conv = qty.to(to_unit)
            except DimensionalityError:
                # Reciprocal units, e.g. pace (min/km) and speed (km/h)
                if (qty.dimensionality != 1 / to_unit.dimensionality or
                        not qty.magnitude):
                    raise
                # Base units, as Pint can't divide by an offset unit (degC)
                conv = (1 / qty.to_base_units()).to(to_unit)
            log.debug('[convert] %s -> %s = %s', i.from_unit, u, conv)
            results.append(Conversion(i.number, i.from_unit,
                                      conv.magnitude / to_unit.magnitude, u,
                                      i.dimensionality))

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
        # 5'10" is 5 ft 10 in
        query = re.sub(r"(?<=\d)['′]", ' ft ', query)
        query = re.sub(r'(?<=\d)["″]', ' in ', query)
        # Read "$100 eur" as "100 $ eur"
        cur = query[:1] if query[:1] in CURRENCY_SYMBOLS else ''
        qty, tail = self.parse_quantity(query[len(cur):])
        tail = (cur + ' ' + tail).translate(SYMBOLS).strip()

        # Show error message for invalid input
        if qty is None:
            if ctx:
                raise ValueError('No quantity')

            raise ValueError('Start your query with a number')

        if not len(tail):
            raise ValueError('No units specified')

        log.debug('[parser] quantity=%s, tail=%s', qty, tail)

        # Parse query into pint.Quantity objects
        from_unit, to_units = self.parse_units(tail, qty)

        i = Input(from_unit.magnitude, str(from_unit.dimensionality),
                  str(from_unit.units), to_units or None, ctx)

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
            if c.isalpha():
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
            (float, str): Quantity and remainder of query, or
                ``(None, '')`` if the query doesn't start with a number.

        Raises:
            ValueError: Raised if a thousands separator isn't followed by
                3 digits, e.g. "1,5", which is likely a decimal.

        """
        t = self.thousands_separator
        d = self.decimal_separator
        m = re.match(NUMBER.format(t=re.escape(t), d=re.escape(d)), query)
        if not m:
            return None, ''

        if t and re.match(re.escape(t) + r'\d', query[m.end():]):
            raise ValueError('Use "{}" for decimals and "{}" between '
                             'thousands'.format(d, t))

        if m['den']:
            n = int(m['whole'] or 0) + int(m['num']) / int(m['den'])
        elif m['vulgar']:
            n = int(m['int'] or 0) + unicodedata.numeric(m['vulgar'])
        else:
            n = float(m['dec'].replace(t, '').replace(d, '.')
                      .replace('−', '-'))
        if m['sign'] in ('-', '−'):
            n = -n
        return n, query[m.end():].strip()

    def parse_units(self, query, qty=1):
        """Extract from unit and any to units from query.

        Args:
            query (str): (Partial) user input
            qty (int, optional): Quantity of from units

        Returns:
            (pint.Quantity, list): From quantity, the sum of mixed input
                such as "5 ft 10 in", and Pint's name for each to unit.

        Raises:
            ValueError: Raised if a unit is unknown, or mixed input can't
                be added up.

        """
        units = re.sub(r'\s+per\s+', '/', query).split()
        total = None
        while True:
            unit = units.pop(0)
            # "ft10in" in "5ft10in": split off the next number and unit
            m = re.match(r'([^\W\d]+)(\d[\d.]*[^\W\d]\w*)$', unit)
            if m and not ureg.parse_unit_name(unit):  # cmH2O is a unit
                unit = m.group(1)
                units.insert(0, m.group(2))

            q = quantity(qty, unit)
            if total is None:
                total = q
            else:  # "-1 h 30 min" is -1.5 h
                try:
                    total = total - q if total.magnitude < 0 else total + q
                except TypeError:  # different dimensions, or degC
                    raise ValueError("Can't add {} to {}".format(
                        symbol(q.units), symbol(total.units)))

            # Mixed input, e.g. "5 ft 10 in": another number and unit
            qty, rest = self.parse_quantity(' '.join(units))
            if qty is None:
                break
            if not rest:
                raise ValueError('No unit after {:g}'.format(qty))
            units = rest.split()

        # "10 km to mi". Only between units, so "10 km in" is still inches.
        if len(units) > 1 and units[0] in ('to', 'in', 'as', '->', '='):
            del units[0]
        log.debug('[parser] from=%s, to_units=%s', total, units)
        to_units = []
        for u in units:
            names = []
            for part in u.split('+'):  # mixed units, e.g. "ft+in"
                if not part:
                    raise ValueError('Unknown unit: {}'.format(u))
                q = quantity(1, part)
                # Keep "l/100km" as typed: Pint's name would drop the 100
                names.append(str(q.units) if q.magnitude == 1 else part)
            to_units.append('+'.join(names))
        return total, to_units


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
    # defined relative to the US dollar. "_" means no symbol, so results
    # show the code ("USD"), not its lowercase alias.
    ureg.define('USD = [currency] = _ = usd')

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
            definition += ' = _ = {}'.format(abbr.lower())

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
        log.critical('invalid query (%s): %s', query, err)
        error = str(err)

    else:
        try:
            results = c.convert(i)
        except NoToUnits:
            log.critical('No to_units (or defaults) for %s', i.dimensionality)
            error = 'No destination units (or defaults) for {}'.format(
                i.dimensionality)

        except DimensionalityError as err:
            log.critical('invalid conversion (%s): %s', query, err)
            error = "Can't convert from {} {} to {} {}".format(
                symbol(err.units1), err.dim1, symbol(err.units2), err.dim2)

        except KeyError as err:
            log.critical('invalid context (%s): %s', i.context, err)
            error = 'Unknown context: {}'.format(i.context)

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
            value = f.formatted(conv.to_number, conv.to_unit)
            copytext = f.formatted(conv.to_number, conv.to_unit,
                                   show_unit=COPY_UNIT)
            arg = f.formatted(conv.to_number, conv.to_unit, thousands=False,
                              show_unit=COPY_UNIT)

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
                '{} {} as default unit for {}'.format(
                    name, symbol(conv.to_unit), conv.dimensionality))
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
    # Cache parsed definitions: saves ~80 ms per keystroke. Don't log the
    # built-in units file's deliberate redefinitions on every keystroke.
    ureg = UnitRegistry(DEFAULT_UNIT_DEFINITIONS,
                        cache_folder=wf.cachefile('pint'),
                        on_redefinition='ignore')
    ureg.formatter.default_format = 'P'

    wf.magic_arguments['appkey'] = open_currency_instructions

    if not len(wf.args):
        return

    query = wf.args[0]
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
    text = (query.translate(SYMBOLS) + custom_units).lower()
    if exchange_rates and any(s.lower() in text for s in exchange_rates):
        register_exchange_rates(exchange_rates)

    start_update(wf)

    if is_running('update'):
        wf.rerun = 0.5
        if exchange_rates is None:  # No data cached yet
            wf.add_item('Fetching exchange rates…',
                        'Currency conversions will be momentarily possible',
                        icon=ICON_INFO)
        else:
            wf.add_item('Updating exchange rates…',
                        icon=ICON_INFO)

    return convert(query)


if __name__ == '__main__':
    wf = Workflow(help_url=HELP_URL)
    log = wf.logger
    sys.exit(wf.run(main))
