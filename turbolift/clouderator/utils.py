# =============================================================================
# Copyright [2015] [Kevin Carter]
# License Information :
# This software has no warranty, it is provided 'as is'. It is your
# responsibility to validate the behavior of the routines and its accuracy
# using the code provided. Consult the GNU General Public license for further
# details (see GNU General Public License).
# http://www.gnu.org/licenses/gpl.html
# =============================================================================

import datetime
import functools
import random
import time
import urllib


def retry(ExceptionToCheck, tries=3, delay=1, backoff=1):
    """Retry calling the decorated function using an exponential backoff.

    http://www.saltycrane.com/blog/2009/11/trying-out-retry-decorator-python/
    original from: http://wiki.python.org/moin/PythonDecoratorLibrary#Retry

    :param ExceptionToCheck: the exception to check. may be a tuple of
                             exceptions to check
    :type ExceptionToCheck: Exception or tuple
    :param tries: number of times to try (not retry) before giving up
    :type tries: int
    :param delay: initial delay between retries in seconds
    :type delay: int
    :param backoff: backoff multiplier e.g. value of 2 will double the delay
                    each retry
    :type backoff: int
    """
    def deco_retry(f):
        @functools.wraps(f)
        def f_retry(*args, **kwargs):
            mtries, mdelay = tries, delay
            while mtries > 1:
                try:
                    return f(*args, **kwargs)
                except ExceptionToCheck:
                    time.sleep(mdelay)
                    mtries -= 1
                    mdelay *= backoff
            return f(*args, **kwargs)
        return f_retry  # true decorator
    return deco_retry


def stupid_hack(most=10, wait=None):
    """Return a random time between 1 - 10 Seconds."""

    # Stupid Hack For Public Cloud so it is not overwhelmed with API requests.
    if wait is not None:
        time.sleep(wait)
    else:
        time.sleep(random.randrange(1, most))


def time_stamp():
    """Setup time functions

    :returns: ``tuple``
    """

    # Time constants
    fmt = '%Y-%m-%dT%H:%M:%S.%f'
    date = datetime.datetime
    date_delta = datetime.timedelta
    now = datetime.datetime.utcnow()

    return fmt, date, date_delta, now


def unique_list_dicts(dlist, key):
    """Return a list of dictionaries which are sorted for only unique entries.

    :param dlist:
    :param key:
    :return list:
    """

    return list(dict((val[key], val) for val in dlist).values())


class TimeDelta(object):
    def __init__(self, job_args, last_modified, compare_time=None):
        """Check to see if a date delta exists based on filter for an object.

        :param job_args:
        :param last_modified:
        :param compare_time:
        :returns: ``bol``
        """

        self.job_args = job_args
        self.last_modified = last_modified
        self.compare_time = compare_time

    @staticmethod
    def hours(delta, factor):
        return delta(hours=factor)

    @staticmethod
    def days(delta, factor):
        return delta(days=factor)

    @staticmethod
    def weeks(delta, factor):
        return delta(weeks=factor)

    def get_delta(self):
        fmt, date, delta, now = time_stamp()

        # Set time objects
        odate = date.strptime(self.last_modified, fmt)

        if self.compare_time:
            # Time Options
            time_factor = self.job_args.get('time_factor', 1)
            offset = self.job_args.get('time_offset')
            offset_method = getattr(self, offset)

            if (odate + offset_method(delta=delta, factor=time_factor)) > now:
                return False
            else:
                return True
        else:
            if date.strptime(self.compare_time, fmt) > odate:
                return True
            else:
                return False


def quoter(obj):
    """Return a Quoted URL.

    The quote function will return a URL encoded string. If there is an 
    exception in the job which results in a "KeyError" the original
    string will be returned as it will be assumed to already be URL
    encoded.

    :param obj: ``basestring``
    :return: ``str``
    """

    try:
        try:
            return urllib.quote(obj)
        except AttributeError:
            return urllib.parse.quote(obj)
    except KeyError:
        return obj

