#!/usr/bin/env python
# =============================================================================
# Copyright [2013] [Kevin Carter]
# License Information :
# This software has no warranty, it is provided 'as is'. It is your
# responsibility to validate the behavior of the routines and its accuracy
# using the code provided. Consult the GNU General Public license for further
# details (see GNU General Public License).
# http://www.gnu.org/licenses/gpl.html
# =============================================================================
import multiprocessing

# Local Files to Import
from turbolift import arguments
from turbolift.operations import baseofoperations


def run_turbolift():
    """This is the run section of the application Turbolift."""

    multiprocessing.freeze_support()
    tur_arg = arguments.get_values()
    try:
        ops = baseofoperations.BaseCamp(tur_arg)

        if tur_arg.get('con_per_dir'):
            ops.con_per_dir()

        elif tur_arg.get('archive'):
            ops.archive()

        elif any([tur_arg.get('upload'), tur_arg.get('tsync')]):
            ops.file_upload()

        elif any([tur_arg.get('download'), tur_arg.get('delete')]):
            ops.delete_download()

    except KeyboardInterrupt:
        print('Caught KeyboardInterrupt, I\'M ON FIRE!!!!')

if __name__ == "__main__":
    multiprocessing.freeze_support()
    run_turbolift()
