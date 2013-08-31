# =============================================================================
# Copyright [2013] [kevin]
# License Information :
# This software has no warranty, it is provided 'as is'. It is your
# responsibility to validate the behavior of the routines and its accuracy
# using the code provided. Consult the GNU General Public license for further
# details (see GNU General Public License).
# http://www.gnu.org/licenses/gpl.html
# =============================================================================
import operator
import os
import sys

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

    def sorter(index):
        """Return a sorted list based on files size.

        :param index:
        :return:
        """

        return sorted(u_index, key=operator.itemgetter(1), reverse=True)

    def sizeer(sfile):
        """Get file size and return it.

        :param sfile:
        :return:
        """

        return os.path.getsize(sfile)

    def indexer(location):
        """Return a list of indexed files.

        :param location:
        :return:
        """

        _location = os.path.realpath(location.encode('utf8'))
        if os.path.isdir(_location):
            root_dir = '%s%s' % (_location, os.sep)
            r_walk = os.walk(root_dir)
            indexes = [(root, fls) for root, sfs, fls in r_walk]
            return [utils.jpath(root=inx[0], inode=ind)
                    for inx in indexes for ind in inx[1]]
        elif os.path.isfile(location):
            filename = os.path.split(_location)
            return filename
        else:
            raise clds.NoFileProvided('No Path was Found for %s' % _location)

    try:
        d_paths = ARGS.get('source')
        if not isinstance(d_paths, list):
            d_paths = [d_paths]

        c_index = [indexer(location=d_path) for d_path in d_paths]

        if ARGS.get('no_sort') is not None:
            f_index = [item for subl in c_index
                       for item in subl if not_list(item=item)]
        else:
            u_index = [(item, sizeer(sfile=item)) for subl in c_index
                       for item in subl if not_list(item=item)]
            f_index = [item[0] for item in sorter(index=u_index)]
    except Exception as exp:
        raise clds.SystemProblem('Died for some reason. MESSAGE:\t%s' % exp)
    else:
        LOG.debug('FILE LIST:\t%s', f_index)
        return f_index
