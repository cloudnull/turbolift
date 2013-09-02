# =============================================================================
# Copyright [2013] [kevin]
# License Information :
# This software has no warranty, it is provided 'as is'. It is your
# responsibility to validate the behavior of the routines and its accuracy
# using the code provided. Consult the GNU General Public license for further
# details (see GNU General Public License).
# http://www.gnu.org/licenses/gpl.html
# =============================================================================
import os
import hashlib

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
            if ARGS.get('verbose'):
                utils.reporter(
                    msg=('MESSAGE: CheckSumm Mis-Match %s != %s STATUS'
                         ' : %s %s - Local File %s' % (lmd5sum,
                                                       rmd5sum,
                                                       resp.status,
                                                       resp.reason,
                                                       local_f))
                )
            return True
        else:
            utils.reporter(
                msg='MESSAGE: CheckSum Match %s = %s' % (lmd5sum, rmd5sum),
                prt=False
            )

            return False
    else:
        utils.reporter(
            msg='MESSAGE: Local File Not Found %s' % local_f,
            prt=False
        )

        return True
