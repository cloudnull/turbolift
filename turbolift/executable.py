#!/usr/bin/env python
# ==============================================================================
# Copyright [2013] [Kevin Carter]
# License Information :
# This software has no warranty, it is provided 'as is'. It is your
# responsibility to validate the behavior of the routines and its accuracy using
# the code provided. Consult the GNU General Public license for further details
# (see GNU General Public License).
# http://www.gnu.org/licenses/gpl.html
# ==============================================================================

"""
License Information

This software has no warranty, it is provided 'as is'. It is your
responsibility to validate the behavior of the routines and its
accuracy using the code provided. Consult the GNU General Public
license for further details (see GNU General Public License).

http://www.gnu.org/licenses/gpl.html
"""
from multiprocessing import freeze_support

# Local Files to Import
from turbolift.operations import baseofoperations
from turbolift import arguments


def run_turbolift():
    """
    This is the run section of the application Turbolift.
    """
    freeze_support()
    tur_arg = arguments.GetArguments().get_values()
    try:
        ops = baseofoperations.BaseCamp(tur_arg)

        if tur_arg['con_per_dir']:
            ops.con_per_dir()

        elif tur_arg['archive']:
            ops.archive()

        elif tur_arg['upload'] or tur_arg['tsync']:
            ops.file_upload()

        elif tur_arg['download'] or tur_arg['delete']:
            ops.delete_download()

    except KeyboardInterrupt:
        print 'Caught KeyboardInterrupt, I\'M ON FIRE!!!!'

if __name__ == "__main__":
    freeze_support()
    run_turbolift()
