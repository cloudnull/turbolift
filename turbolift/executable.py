#!/usr/bin/env python
# =============================================================================
# Copyright [2015] [Kevin Carter]
# License Information :
# This software has no warranty, it is provided 'as is'. It is your
# responsibility to validate the behavior of the routines and its accuracy
# using the code provided. Consult the GNU General Public license for further
# details (see GNU General Public License).
# http://www.gnu.org/licenses/gpl.html
# =============================================================================

import sys

from cloudlib import arguments
from cloudlib import logger

import turbolift
from turbolift import worker


def execute():
    """This is the run section of the application Turbolift."""

    if len(sys.argv) <= 1:
        raise SystemExit(
            'No Arguments provided. use [--help] for more information.'
        )

    # Capture user arguments
    _args = arguments.ArgumentParserator(
        arguments_dict=turbolift.ARGUMENTS,
        env_name='TURBO',
        epilog=turbolift.VINFO,
        title='Turbolift',
        detail='Multiprocessing Swift CLI tool.',
        description='Manage Swift easily and fast.'
    )
    user_args = _args.arg_parser()
    user_args['run_indicator'] = True
    debug_log = False
    stream_logs = True

    # Load system logging
    if user_args.get('debug'):
        debug_log = True
        user_args['run_indicator'] = False

    # Load system logging
    if user_args.get('quiet'):
        stream_logs = False
        user_args['run_indicator'] = False

    _logging = logger.LogSetup(
        debug_logging=debug_log,
        colorized_messages=user_args.get('colorized', False)
    )
    _logging.default_logger(name='turbolift', enable_stream=stream_logs)
    job = worker.Worker(job_args=user_args)
    job.run_manager()


if __name__ == "__main__":
    execute()
