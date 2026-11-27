#!/usr/bin/env python3
#
# Copyright (c) 2017 Dean Jackson <deanishe@deanishe.net>
#
# MIT Licence. See http://opensource.org/licenses/MIT
#
# Created on 2017-07-16
#

"""defaults.py (save|delete) <dimensionality> <unit>

Save/delete default units for given dimensionality.

"""

from collections import defaultdict
import os

from workflow import Workflow


log = None

# Defaults for a dimensionality the user hasn't saved any for, in Pint's
# names for the units, as saved defaults are
STARTER_DEFAULTS = {
    '[length]': ['centimeter', 'meter', 'kilometer', 'inch', 'foot', 'mile'],
    '[mass]': ['gram', 'kilogram', 'ounce', 'pound'],
    '[temperature]': ['degree_Celsius', 'degree_Fahrenheit'],
    '[length] ** 2': ['meter²', 'hectare', 'foot²', 'acre'],
    '[length] ** 3': ['milliliter', 'liter', 'fluid_ounce', 'cup', 'gallon'],
    '[length] / [time]': ['kilometer_per_hour', 'mile_per_hour'],
    '[time]': ['second', 'minute', 'hour', 'day'],
    '[currency]': ['USD', 'EUR'],
}


class Defaults:
    """Manage default units for dimensionalities.

    Saves default units in workflow's settings file.

    """

    def __init__(self, wf):
        """Create new `Defaults` for workflow.

        Args:
            wf (Workflow): Active Workflow object.
        """
        self._wf = wf
        self._defs = self._load()

    def defaults(self, dimensionality):
        """Default units for dimensionality.

        Args:
            dimensionality (str): Dimensionality to return units for

        Returns:
            list: Sequence of default units

        """
        return self._defs[dimensionality][:]

    def add(self, dimensionality, unit):
        """Save ``unit`` as default for ``dimensionality``.

        Args:
            dimensionality (str): Dimensionality
            unit (str): Unit

        """
        if not self.is_default(dimensionality, unit):
            self._defs[dimensionality].append(unit)
            self._save()

    def remove(self, dimensionality, unit):
        """Remove ``unit`` as default for ``dimensionality``.

        Args:
            dimensionality (str): Dimensionality
            unit (str): Unit

        """
        if self.is_default(dimensionality, unit):
            self._defs[dimensionality].remove(unit)
            self._save()

    def is_default(self, dimensionality, unit):
        """Check whether ``unit`` is a default for ``dimensionality``.

        Args:
            dimensionality (str): Dimensionality
            unit (str): Unit

        Returns:
            bool: ``True`` if ``unit`` is a default.

        """
        return unit in self._defs[dimensionality]

    def _load(self):
        # Copies, so saving a change doesn't change STARTER_DEFAULTS
        defs = defaultdict(list, {dim: units[:] for dim, units
                                  in STARTER_DEFAULTS.items()})
        defs.update(self._wf.settings.get('default_units', {}))
        return defs

    def _save(self):
        self._wf.settings['default_units'] = dict(self._defs)


def main(wf):
    """Run script."""
    log.debug('args=%r', wf.args)
    action, dimensionality, unit = wf.args

    defs = Defaults(wf)
    log.debug('defaults=%r', defs._defs)
    # As the result's subtitle said it, e.g. "km/h as default unit for
    # velocity"
    label = os.getenv('label') or '{} as default unit for {}'.format(
        unit, dimensionality)

    if action == 'save':
        defs.add(dimensionality, unit)
        print('Saved ' + label)
        return

    if action == 'delete':
        defs.remove(dimensionality, unit)
        print('Removed ' + label)
        return


if __name__ == '__main__':
    wf = Workflow()
    log = wf.logger
    wf.run(main)
