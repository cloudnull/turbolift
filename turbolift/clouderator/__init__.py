# =============================================================================
# Copyright [2013] [Kevin Carter]
# License Information :
# This software has no warranty, it is provided 'as is'. It is your
# responsibility to validate the behavior of the routines and its accuracy
# using the code provided. Consult the GNU General Public license for further
# details (see GNU General Public License).
# http://www.gnu.org/licenses/gpl.html
# =============================================================================
import hashlib
import os

import turbolift.utils.basic_utils as basic
import turbolift.utils.report_utils as report

from turbolift import ARGS


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
        rmd5sum = resp.headers.get('etag')
        md5 = hashlib.md5()

        with open(local_f, 'rb') as data_hash:
            for chk in iter(calc_hash, ''):
                md5.update(chk)

        lmd5sum = md5.hexdigest()

        if rmd5sum != lmd5sum:
            if ARGS.get('verbose'):
                report.reporter(
                    msg=('MESSAGE: CheckSumm Mis-Match %s != %s STATUS'
                         ' : %s %s - Local File %s' % (lmd5sum,
                                                       rmd5sum,
                                                       resp.status_code,
                                                       resp.reason,
                                                       local_f))
                )
            return True
        else:
            report.reporter(
                msg='MESSAGE: CheckSum Match %s = %s' % (lmd5sum, rmd5sum),
                prt=False
            )

            return False
    else:
        report.reporter(
            msg='MESSAGE: Local File Not Found %s' % local_f,
            prt=False
        )

        return True


def time_delta(lmobj, compare_time=None):
    """Check to see if a date delta exists based on filter for an object.

    :param lmobj:
    :param compare_time:
    :return True|False:
    """

    def hours(delta, factor):
        return delta(hours=factor)

    def days(delta, factor):
        return delta(days=factor)

    def weeks(delta, factor):
        return delta(weeks=factor)

    fmt, date, delta, now = basic.time_stamp()

    # Set time objects
    odate = date.strptime(lmobj, fmt)

    if compare_time is None:
        # Time Options
        time_factor = ARGS.get('time_factor', 1)
        offset = ARGS.get('time_offset')
        offset_method = locals()[offset]

        if (odate + offset_method(delta=delta, factor=time_factor)) > now:
            return False
        else:
            return True
    else:
        if date.strptime(compare_time, fmt) > odate:
            return True
        else:
            return False
