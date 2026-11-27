#!/usr/bin/env python3
# encoding: utf-8
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

from __future__ import print_function, absolute_import

from collections import defaultdict

from workflow import Workflow


log = None


class Defaults(object):
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
        defs = defaultdict(list)
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

    if action == 'save':
        defs.add(dimensionality, unit)
        print(u'Saved {} as default unit for {}'.format(unit, dimensionality))
        return

    if action == 'delete':
        defs.remove(dimensionality, unit)
        print(u'Removed {} as default unit for {}'.format(unit, dimensionality))
        return


if __name__ == '__main__':
    wf = Workflow()
    log = wf.logger
    wf.run(main)
