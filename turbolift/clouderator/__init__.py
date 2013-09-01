# =============================================================================
# Copyright [2013] [kevin]
# License Information :
# This software has no warranty, it is provided 'as is'. It is your
# responsibility to validate the behavior of the routines and its accuracy
# using the code provided. Consult the GNU General Public license for further
# details (see GNU General Public License).
# http://www.gnu.org/licenses/gpl.html
# =============================================================================
from turbolift.worker import ARGS
from turbolift.worker import LOG
from turbolift import utils
import turbolift as clds


def md5_checker(resp, local_f):
    """Check for different Md5 in CloudFiles vs Local File.

    If the md5 sum is different, return True else False

    :param resp:
    :param local_f:
    :return True|False:
    """

    import os
    import hashlib

    def calc_hash():
        """Read the hash.

        :return data_hash.read():
        """

        return data_hash.read(128 * md5.block_size)

    if os.path.isfile(local_f) is True:
        rmd5sum = resp.getheader('etag')
        md5 = hashlib.md5()

        with open(local_f, 'rb') as data_hash:
            for chk in iter(calc_hash, ''):
                md5.update(chk)

        lmd5sum = md5.hexdigest()

        if rmd5sum != lmd5sum:
            if ARGS.get('debug'):
                print('MESSAGE:\t CheckSumm Mis-Match %s != %s\n'
                      '\t  STATUS : %s %s - Local File %s'
                      % (lmd5sum, rmd5sum, resp.status, resp.reason, local_f))
            elif ARGS.get('verbose'):
                print('MESSAGE\t: CheckSum Mis-Match', lmd5sum)
            return True
        else:
            if ARGS.get('verbose'):
                print('MESSAGE\t: CheckSum Match', lmd5sum)

            return False
    else:
        if ARGS.get('verbose'):
            print('MESSAGE\t: Local File Not Found %s' % local_file)

        return True
