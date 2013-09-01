# =============================================================================
# Copyright [2013] [kevin]
# License Information :
# This software has no warranty, it is provided 'as is'. It is your
# responsibility to validate the behavior of the routines and its accuracy
# using the code provided. Consult the GNU General Public license for further
# details (see GNU General Public License).
# http://www.gnu.org/licenses/gpl.html
# =============================================================================
from contextlib import contextmanager
import operator
import os
import sys
import traceback

from turbolift import info
import turbolift as clds
from turbolift import utils
from turbolift.worker import LOG
from turbolift.worker import ARGS


def get_local_files():
    """Find all files specified in the "source" path.

    This creates a list for all of files using the full path.
    """

    def not_list(item):
        """

        :param item:
        :return:
        """
        if all([not os.path.islink(item),
                not os.path.ismount(item)]):
            return True
        else:
            return False

    def indexer(location):
        """Return a list of indexed files.

        :param location:
        :return:
        """

        location = os.path.expanduser(location.encode('utf8'))
        if os.path.isdir(location):
            root_dir = '%s' % location
            r_walk = os.walk(root_dir)
            indexes = [(root, fls) for root, sfs, fls in r_walk]
            return [utils.jpath(root=inx[0], inode=ind)
                    for inx in indexes for ind in inx[1]]
        elif os.path.isfile(location):
            return [location]
        else:
            raise clds.NoFileProvided('No Path was Found for %s' % location)

    try:
        d_paths = ARGS.get('source')
        if not isinstance(d_paths, list):
            d_paths = [d_paths]

        # Local Index Pathh
        c_index = [indexer(location=d_path) for d_path in d_paths]

        # make sure my files are only files, and compare it with the not_list
        f_index = [item for subl in c_index
                   for item in subl if not_list(item=item)]
    except Exception as exp:
        raise clds.SystemProblem('Died for some reason. MESSAGE:\t%s' % exp)
    else:
        LOG.debug('FILE LIST:\t%s', f_index)
        return f_index


@contextmanager
def spinner(work_q=None):
    from turbolift.worker import ARGS
    from turbolift import utils

    if not ARGS.get('verbose'):
        itd = utils.IndicatorThread(
            work_q=work_q
        ).indicator_thread()

    yield

    if not ARGS.get('verbose'):
        itd.terminate()

    print('Operation Complete.')


@contextmanager
def operation(retry, conn=None):
    try:
        yield retry
    except clds.RetryError:
        print(
            '\nFailed to perform action after "%s" times'
            % ARGS.get('error_retry')
        )
        LOG.error('Retry has failed.\nMessage: %s', traceback.format_exc())
    except clds.NoSource as exp:
        LOG.error('No Source.\nMessage: %s => %s', traceback.format_exc())
        retry()
    except clds.SystemProblem as exp:
        LOG.error('System Problems Found. Message %s', exp)
        print(
            '\nSystem Problems Found %s' % exp
        )
        retry()
    except KeyboardInterrupt:
        utils.emergency_exit('You killed me with the power of CTRL-C')
    except IOError as exp:
        print(
            '\nIO ERROR: %s. MESSAGE %s will retry.' % (exp, info.__appname__)
        )
        LOG.error('IO ERROR. Message: %s', exp)
        retry()
    except Exception as exp:
        print(
            '\nFailed Operation. %s will retry' % info.__appname__
        )
        LOG.error('General Exception Traceback %s', traceback.format_exc())
        retry()
    finally:
        if conn is not None:
            conn.close()
