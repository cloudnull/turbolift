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
import json
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
        log = logger.LogSetup(
            debug_logging=args.get('debug', False),
            log_dir=args.get('log_location', '/var/log'),
            log_name=args.get('log_file')
        ).default_logger(enable_stream=args.get('log_streaming'))

        log.debug('set arguments [ %s ]', json.dumps(args, indent=2))

        import turbolift.utils.basic_utils as basic
        args = basic.dict_pop_none(dictionary=args)
        load_constants(args=args)

        try:
            from turbolift import worker
            worker.start_work()
        except KeyboardInterrupt:
            turbo.emergency_kill(reclaim=True)
        finally:
            if args.get('quiet') is not True:
                print('All Done!')
            log.info('Job Finished.')


if __name__ == "__main__":
    run_turbolift()
