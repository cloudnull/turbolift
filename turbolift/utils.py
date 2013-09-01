# =============================================================================
# Copyright [2013] [kevin]
# License Information :
# This software has no warranty, it is provided 'as is'. It is your
# responsibility to validate the behavior of the routines and its accuracy
# using the code provided. Consult the GNU General Public license for further
# details (see GNU General Public License).
# http://www.gnu.org/licenses/gpl.html
# =============================================================================


def json_encode(read):
    """Return a json encoded object.

    :param read:
    :return:
    """

    import json

    return json.loads(read)


def unique_list_dicts(dlist, key):
    """Return a list of dictionaries which have sorted for only unique entries.

    :param dlist:
    :param key:
    :return list:
    """

    return dict((val[key], val) for val in dlist).values()


def dict_pop_none(dictionary):
    """Parse all keys in a dictionary for Values that are None.

    :param dictionary: all parsed arguments
    :returns dict: all arguments which are not None.
    """

    return dict([(key, value) for key, value in dictionary.iteritems()
                 if value is not None if value is not False])


def keys2dict(chl):
    """Take a list of strings and turn it into dictionary.

    :param chl:
    :return {}|None:
    """

    if chl:
        return dict([_kv.split('=') for _kv in chl])
    else:
        return None


def parse_url(url, auth=False):
    """Return a clean URL. Remove the prefix for the Auth URL if Found.

    :param url:
    :return aurl:
    """

    import urlparse

    def is_https(iurl):
        """Check URL to determine the Connection type.

        :param iurl:
        :return 'complete url string.':
        """

        if 'rackspace' in iurl:
            return 'https://%s' % iurl
        else:
            return 'http://%s' % iurl

    if all([auth is True, 'tokens' not in url]):
            url = urlparse.urljoin(url, 'tokens')

    if url.startswith(('http', 'https', '//')):
        if url.startswith('//'):
            return urlparse.urlparse(url, scheme='http')
        else:
            return urlparse.urlparse(url)
    else:
        return urlparse.urlparse(is_https(iurl=url))


def jpath(root, inode):
    """Return joined directory / path

    :param root:
    :param inode:
    :return "root/inode":
    """

    import os

    return os.path.join(root, inode)


def rand_string(length=15):
    """Generate a Random string."""

    import random
    import string

    chr_set = string.ascii_uppercase
    output = ''

    for _ in range(length):
        output += random.choice(chr_set)
    return output


def basic_queue(iters=None):
    """Uses a manager Queue, from multiprocessing.

    All jobs will be added to the queue for processing.
    :param iters:
    """

    import multiprocessing

    worker_q = multiprocessing.Queue()
    for _dt in iters:
        worker_q.put(_dt)
    return worker_q


def get_from_q(queue):
    """Returns the file or a sentinel value.

    :param queue:
    :return item|None:
    """

    from multiprocessing.queues import Empty

    try:
        return queue.get(timeout=2)
    except Empty:
        return None


def emergency_exit(msg):
    """Exit process.

    :param msg:
    :return exit.status:
    """

    import sys

    return sys.exit(msg)


def set_concurrency(args, file_count):
    """Concurrency is a user specified variable when the arguments parsed.

    :param args:

    However if the number of things Turbo lift has to do is less than the
    desired concurency, then turbolift will lower the concurency rate to
    the number of operations.
    """

    def verbose(ccr):
        if args.get('verbose'):
            print('MESSAGE\t: We are creating %s Processes\n' % ccr)
        return ccr

    _cc = args.get('cc')

    if _cc > file_count:
        print('MESSAGE\t: There are less things to do than the number of\n'
              '\t  concurrent processes specified by either an override\n'
              '\t  or the system defaults. I am leveling the number of\n'
              '\t  concurrent processes to the number of jobs to perform.')
        return verbose(ccr=file_count)
    else:
        return verbose(ccr=_cc)


def worker_proc(job_action, num_jobs, concurrency, queue, t_args=None):
    """Requires the job_action and num_jobs variables for functionality.

    :param job_action: What function will be used
    :param num_jobs: The number of jobs that will be processed
    :param t_args: Optional

    All threads produced by the worker are limited by the number of concurrency
    specified by the user. The Threads are all made active prior to them
    processing jobs.
    """

    import multiprocessing

    sem = multiprocessing.Semaphore(concurrency)
    jobs = [multiprocessing.Process(target=job_action,
                                    args=(queue, t_args))
            for _ in xrange(concurrency)]

    for _job in jobs:
        _job.Daemon = True
        _job.start()

    for job in jobs:
        job.join()

    print('\nWaiting for in-process Jobs to finish')


def mkdir_p(path):
    """'mkdir -p' in Python

    Original Code came from :
    stackoverflow.com/questions/600268/mkdir-p-functionality-in-python
    :param path:
    """

    import errno
    import os

    import turbolift as clds

    try:
        if not os.path.isdir(path):
            os.makedirs(path)
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise clds.DirectoryFailure(
                'The path provided "%s" is occupied and not be used as a '
                'directory. System was halted on Download, becaue The '
                'provided path is a file and can not be turned into a '
                'directory.'
            )


def get_sfile(ufile, source):
    """Return the source file

    :param ufile:
    :param source:
    :return file_name:
    """

    import os

    from turbolift.worker import ARGS

    if ARGS.get('preserve-path'):
        return source
    if os.path.isfile(source):
        return os.path.basename(source)
    elif source is '.':
        return os.getcwd()
    else:
        base, sfile = ufile.split(source)
        return os.sep.join(sfile.split(os.sep)[1:])


def get_local_source(args):
    """Understand the Local Source and return it.

    :param args:
    :return source:
    """

    import os

    _local_path = os.path.expanduser(args.get('source'))
    if os.path.isdir(_local_path):
        return _local_path.rstrip(os.sep)
    else:
        return os.path.split(_local_path)[0].rstrip(os.sep)


def open_connection(url):
    """Open an Http Connection and return the connection object.

    :param url:
    :return conn:
    """

    import httplib

    from turbolift.worker import ARGS

    try:
        if url.scheme == 'https':
            conn = httplib.HTTPSConnection(url.netloc)
        else:
            conn = httplib.HTTPConnection(url.netloc)
    except httplib.InvalidURL as exc:
        msg = 'ERROR: Making connection to %s\nREASON:\t %s' % (url, exc)
        raise httplib.CannotSendRequest(msg)
    else:
        if ARGS.get('debug'):
            conn.set_debuglevel(1)
        return conn


def response_get(conn):
    """Get the response information and return it.

    :param conn:
    :param rty:
    :param ret_read:
    :param mcr:
    """

    import httplib
    import time

    import turbolift as clds
    from turbolift.worker import ARGS

    for retry in retryloop(attempts=ARGS.get('error_retry'),
                           timeout=960,
                           delay=1):
        try:
            time.sleep(.2)
            resp = conn.getresponse()
            read = resp.read()
        except httplib.BadStatusLine as exp:
            retry()
        except httplib.ResponseNotReady:
            retry()
        else:
            return resp, read


def retryloop(attempts, timeout=None, delay=None, backoff=1):
    """Enter the amount of retries you want to perform.

    The timeout allows the application to quit on "X".
    delay allows the loop to wait on fail. Useful for making REST calls.

    ACTIVE STATE retry loop
    http://code.activestate.com/recipes/578163-retry-loop/

    Example:
        Function for retring an action.
        for retry in retryloop(attempts=10, timeout=30, delay=1, backoff=1):
            something
            if somecondition:
                retry()

    :param attempts:
    :param timeout:
    :param delay:
    :param backoff:
    """

    import time

    import turbolift as clds

    starttime = time.time()
    success = set()
    for _ in range(attempts):
        success.add(True)
        yield success.clear
        if success:
            return
        duration = time.time() - starttime
        if timeout is not None and duration > timeout:
            break
        if delay:
            time.sleep(delay)
            delay = delay * backoff
    raise clds.RetryError


def container_headers(headers):
    from turbolift.worker import ARGS

    return headers.update(ARGS.get('container_headers'))


def cdn_toggle(headers):
    from turbolift.worker import ARGS

    return headers.update({'X-CDN-Enabled': ARGS.get('cdn_toggle'),
                           'X-TTL': ARGS.get('cdn_ttl'),
                           'X-Log-Retention': ARGS.get('cdn_logs')})


def set_headers(headers):
    """Set the headers used in the Cloud Files Request.

    :return headers:
    """

    from turbolift.worker import ARGS

    def object_headers(headers):
        """Set and return custom headers.

        :param headers:
        :return headers:
        """

        return headers.update(ARGS.get('object_headers'))

    # Set the headers if some custom ones were specified
    if ARGS.get('object_headers'):
        return object_headers(headers=headers)
    else:
        return headers


def prep_payload(auth, container, source, args):
    """Create payload dictionary.

    :param auth:
    :param container:
    :param source:
    :return (dict, dict): payload and headers
    """

    # Unpack the values from Authentication
    token, tenant, user, inet, enet, cnet, aurl = auth

    # Get the headers ready
    headers = set_headers({'X-Auth-Token': token})

    if args.get('internal'):
        url = inet
    else:
        url = enet

    # Set the upload Payload
    return {'c_name': container,
            'source': source,
            'token': token,
            'tenant': tenant,
            'headers': headers,
            'user': user,
            'inet': inet,
            'enet': enet,
            'cnet': cnet,
            'aurl': aurl,
            'url': url}


def get_new_token():
    """Authenticate and return only a new token.

    :return token:
    """

    import turbolift.authentication.authentication as auth

    return auth.authenticate()[0]


def stupid_hack(max=10, wait=None):
    """Return a random time between 1 - 10 Seconds."""

    import random
    import time

    # Stupid Hack For Public Cloud so it is not overwhelmed with API requests.
    if wait is not None:
        time.sleep(wait)
    else:
        time.sleep(random.randrange(1, max))


class IndicatorThread(object):
    """Creates a visual indicator while normally performing actions."""

    def __init__(self, work_q=None, system=True):
        """System Operations Available on Load.

        :param work_q:
        :param system:
        """

        self.work_q = work_q
        self.system = system

    def indicator(self):
        """Produce the spinner."""

        import sys
        import time

        while self.system:
            busy_chars = ['|', '/', '-', '\\']
            for _cr in busy_chars:
                # Fixes Errors with OS X due to no sem_getvalue support
                if self.work_q is not None:
                    if not sys.platform.startswith('darwin'):
                        _qz = ('Number of Jobs Left in Queue = %s '
                               % self.work_q.qsize())
                    else:
                        _qz = "The System Can't Count... Please Wait."
                else:
                    _qz = ''
                sys.stdout.write('\rProcessing - [ %(spin)s ] - %(qsize)s'
                                 % {"qsize": _qz,
                                    "spin": _cr})
                sys.stdout.flush()
                time.sleep(.05)
                self.system = self.system

    def indicator_thread(self):
        """indicate that we are performing work in a thread."""

        import multiprocessing

        job = multiprocessing.Process(target=self.indicator)
        job.start()
        return job
