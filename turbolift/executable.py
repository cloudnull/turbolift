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
import sys
import multiprocessing

from turbolift import arguments
from turbolift.logger import logger
from turbolift import worker


def run_turbolift():
    """This is the run section of the application Turbolift."""

    multiprocessing.freeze_support()

    if len(sys.argv) <= 1:
        arguments.get_help()
        sys.exit('Give me something to do and I will do it')
    else:
        args = arguments.get_args()
        log = logger.load_in(log_level=args.get('log_level', 'info'))
        log.debug('set arguments %s', args)
        worker.load_constants(log_method=log, args=args)
        try:
            worker.start_work()
        except KeyboardInterrupt:
            sys.exit('I have been Murdered.')
        finally:
            print('All Done!')


if __name__ == "__main__":
    multiprocessing.freeze_support()
    run_turbolift()
