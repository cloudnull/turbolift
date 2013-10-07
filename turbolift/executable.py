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

import turbolift as turbo
from turbolift import arguments
from turbolift import load_constants
from turbolift.logger import logger


def run_turbolift():
    """This is the run section of the application Turbolift."""

    if len(sys.argv) <= 1:
        arguments.get_help()
        raise SystemExit('Give me something to do and I will do it')
    else:
        args = arguments.get_args()
        log = logger.load_in(log_level=args.get('log_level', 'info'),
                             log_location=args.get('log_location', '/var/log'))
        log.debug('set arguments %s', args)
        load_constants(log_method=log, args=args)
        try:
            from turbolift import worker
            worker.start_work()
        except KeyboardInterrupt:
            turbo.emergency_kill(reclaim=True)
        finally:
            print('All Done!')


if __name__ == "__main__":
    run_turbolift()
