# =============================================================================
# Copyright [2013] [kevin]
# License Information :
# This software has no warranty, it is provided 'as is'. It is your
# responsibility to validate the behavior of the routines and its accuracy
# using the code provided. Consult the GNU General Public license for further
# details (see GNU General Public License).
# http://www.gnu.org/licenses/gpl.html
# =============================================================================
import prettytable

import turbolift as turbo

from turbolift.logger import logger


LOG = logger.getLogger('turbolift')


def print_horiz_table(data):
    """Print a horizontal pretty table from data."""

    table = prettytable.PrettyTable(dict(data[0]).keys())

    for info in data:
        table.add_row(dict(info).values())
    for tbl in table.align.keys():
        table.align[tbl] = 'l'
    return table


def print_virt_table(data):
    """Print a vertical pretty table from data."""

    table = prettytable.PrettyTable()
    table.add_column('Keys', data.keys())
    table.add_column('Values', data.values())
    for tbl in table.align.keys():
        table.align[tbl] = 'l'
    return table


def reporter(msg, prt=True, lvl='info', log=True, color=False):
    """Print Messages and Log it.

    :param msg:
    :param prt:
    :param lvl:
    """

    # Print a Message
    if prt is True or turbo.ARGS.get('verbose') is True:
        if lvl is 'error':
            if turbo.ARGS.get('colorized') is True:
                msg = bcolors(msg, lvl)
            print(msg)
        else:
            if turbo.ARGS.get('quiet') is None:
                if turbo.ARGS.get('colorized') is True:
                    msg = bcolors(msg, lvl)
                print(msg)

    # Log message
    log_checks = [
        turbo.ARGS.get('verbose') is True,
        lvl in ['debug', 'warn', 'error']
    ]
    if any(log_checks) and log is True:
        logger = getattr(LOG, lvl)
        if turbo.ARGS.get('colorized'):
            logger(bcolors(msg, lvl))
        else:
            logger(msg)


def bcolors(msg, color):
    """return a colorizes string.

    :param msg:
    :param color:
    :return str:
    """

    # Available Colors
    colors = {'debug': '\033[94m',
              'info': '\033[92m',
              'warn': '\033[93m',
              'error': '\033[91m',
              'critical': '\033[95m',
              'ENDC': '\033[0m'}

    if color in colors:
        return '%s%s%s' % (colors[color], msg, colors['ENDC'])
    else:
        raise turbo.SystemProblem('"%s" was not a known color.' % color)
