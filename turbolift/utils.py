# =============================================================================
# Copyright [2013] [Kevin Carter]
# License Information :
# This software has no warranty, it is provided 'as is'. It is your
# responsibility to validate the behavior of the routines and its accuracy
# using the code provided. Consult the GNU General Public license for further
# details (see GNU General Public License).
# http://www.gnu.org/licenses/gpl.html
# =============================================================================


def reporter(msg, prt=True, lvl='info', log=False, color=False):
    """Print Messages and Log it.

    :param msg:
    :param prt:
    :param lvl:
    """

    from turbolift.worker import ARGS
    from turbolift.worker import LOG

    # Print a Message
    if ARGS.get('quiet') is None:
        if prt is True or ARGS.get('verbose') is True:
            if lvl is 'error':
                if ARGS.get('colorized') is True:
                    msg = bcolors(msg, lvl)
                print(msg)
            else:
                if ARGS.get('colorized') is True:
                    msg = bcolors(msg, lvl)
                print(msg)

    # Log message
    if any([ARGS.get('verbose') is True,
            lvl in ['debug', 'warn', 'error'],
            log is True]):
        logger = getattr(LOG, lvl)
        if ARGS.get('colorized'):
            logger(bcolors(msg, lvl))
        else:
            logger(msg)


def bcolors(msg, color):
    """return a colorizes string.

    :param msg:
    :param color:
    :return str:
    """

    # TODO(kevin) need a better method for this.
    import turbolift as clds

    # Available Colors
    colors = {'debug': '\033[94m',
              'info': '\033[92m',
              'warn': '\033[93m',
              'error': '\033[91m',
              'critical': '\033[91m',
              'ENDC': '\033[0m'}

    if color in colors:
        return '%s%s%s' % (colors[color], msg, colors['ENDC'])
    else:
        raise clds.SystemProblem('"%s" was not a known color.' % color)


def time_stamp():
    """Setup time functions

    :return (fmt, date, date_delta, now):
    """

    import datetime

    # Time constants
    fmt = '%Y-%m-%dT%H:%M:%S.%f'
    date = datetime.datetime
    date_delta = datetime.timedelta
    now = datetime.datetime.utcnow()

    return fmt, date, date_delta, now


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


def create_tmp():
    """Create a tmp file.

    :return str:
    """
    import tempfile

    return tempfile.mktemp()


def remove_file(filename):
    """Remove a file if its found.

    :param filename:
    """

    import os

    if file_exists(filename):
        try:
            os.remove(filename)
        except OSError:
            pass


def file_exists(filename):
    import os

    if os.path.exists(filename):
        return True
    else:
        return False


def basic_queue(iters=None):
    """Uses a manager Queue, from multiprocessing.

    All jobs will be added to the queue for processing.
    :param iters:
    """

    import multiprocessing

    worker_q = multiprocessing.Queue()
    if iters is not None:
        for _dt in iters:
            worker_q.put(_dt)
    return worker_q


def manager_dict(dictionary):
    """Create and return a Manger Dictionary.

    :param dictionary:
    :return dict:
    """

    import multiprocessing

    manager = multiprocessing.Manager()
    return manager.dict(dictionary)


def batcher(num_files):
    """Check the batch size and return it.

    :param num_files:
    :return int:
    """

    from turbolift.worker import ARGS

    batch_size = ARGS.get('batch_size')
    reporter(
        msg='Job process MAX Batch Size is "%s"' % batch_size,
        lvl='debug',
        log=True,
        prt=False
    )
    if num_files > batch_size:
        ops = num_files / batch_size + 1
        reporter(
            msg='This will take "%s" operations to complete.' % ops,
            lvl='warn',
            log=True,
            prt=True
        )
    return batch_size


def batch_gen(data, batch_size, count):
    """This is a batch Generator which is used for large data sets.

    NOTE ORIGINAL CODE FROM: Paolo Bergantino
    http://stackoverflow.com/questions/760753/iterate-over-a-python-sequence\
    -in-multiples-of-n

    :param data:
    :param batch_size:
    :return list:
    """

    for dataset in range(0, count, batch_size):
        yield data[dataset:dataset + batch_size]


def get_from_q(queue):
    """Returns the file or a sentinel value.

    :param queue:
    :return item|None:
    """

    import Queue

    try:
        wfile = queue.get(timeout=5)
    except Queue.Empty:
        return None
    else:
        return wfile


def emergency_kill(reclaim=None):
    """Exit process.

    :return kill pid:
    """

    import os
    import signal

    if reclaim is not None:
        return os.kill(os.getpid(), signal.SIGKILL)
    else:
        return os.kill(os.getpid(), signal.SIGCHLD)


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
        reporter(
            msg='MESSAGE: We are creating %s Processes' % ccr,
            prt=False
        )
        return ccr

    _cc = args.get('cc')

    if _cc > file_count:
        reporter(
            msg=('MESSAGE: There are less things to do than the number of'
                 ' concurrent processes specified by either an override'
                 ' or the system defaults. I am leveling the number of'
                 ' concurrent processes to the number of jobs to perform.'),
            lvl='warn'
        )
        return verbose(ccr=file_count)
    else:
        return verbose(ccr=_cc)


def worker_proc(job_action, concurrency, queue, t_args=None, opt=None):
    """Requires the job_action and num_jobs variables for functionality.

    :param job_action: What function will be used
    :param concurrency: The number of jobs that will be processed
    :param queue: The Queue
    :param t_args: Optional

    All threads produced by the worker are limited by the number of concurrency
    specified by the user. The Threads are all made active prior to them
    processing jobs.
    """

    import multiprocessing

    if opt is not None:
        jobs = [multiprocessing.Process(target=job_action,
                                        args=(queue, t_args, opt))
                for _ in xrange(concurrency)]
    else:
        jobs = [multiprocessing.Process(target=job_action,
                                        args=(queue, t_args))
                for _ in xrange(concurrency)]

    for _job in jobs:
        _job.Daemon = True
        _job.start()

    for job in jobs:
        job.join()


def job_processer(num_jobs, objects, job_action, concur, payload, opt=None):
    """Process all jobs in batches.

    :param num_jobs:
    :param objects:
    :param job_action:
    :param concur:
    :param payload:
    """

    from turbolift import methods

    count = 0
    batch_size = batcher(num_files=num_jobs)
    for work in batch_gen(data=objects,
                          batch_size=batch_size,
                          count=num_jobs):
        count += 1
        reporter(msg='Job Count %s' % count)
        work_q = basic_queue(work)
        with methods.spinner(work_q=work_q):
            worker_proc(job_action=job_action,
                        concurrency=concur,
                        t_args=payload,
                        queue=work_q,
                        opt=opt)


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
                'The path provided, "%s", is either occupied and can\'t be'
                ' used as a directory or the permissions will not allow you to'
                ' write to this location.' % path
            )


def get_sfile(ufile, source):
    """Return the source file

    :param ufile:
    :param source:
    :return file_name:
    """

    import os

    from turbolift.worker import ARGS

    if ARGS.get('preserve_path'):
        return os.path.join(source, ufile).lstrip(os.sep)
    if os.path.isfile(source):
        return os.path.basename(source)
    elif source is '.':
        return os.getcwd()
    else:
        base, sfile = ufile.split(source)
        return os.sep.join(sfile.split(os.sep)[1:])


def real_full_path(object):
    """Return a string with the real full path of an object.

    :param object:
    :return str:
    """

    import os

    return os.path.realpath(
        os.path.expanduser(
            object
        )
    )


def get_local_source(args):
    """Understand the Local Source and return it.

    :param args:
    :return source:
    """

    import os

    local_path = real_full_path(args.get('source'))
    if os.path.isdir(local_path):
        return local_path.rstrip(os.sep)
    else:
        return os.path.split(local_path)[0].rstrip(os.sep)


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


def response_get(conn, retry, resp_only=False):
    """Get the response information and return it.

    :param conn:
    :param retry:
    :param ret_read:
    :param mcr:
    """

    import httplib
    import traceback

    import turbolift as clds

    try:
        if resp_only is True:
            return conn.getresponse()
        else:
            resp = conn.getresponse()
            if resp is None:
                raise clds.DirectoryFailure('Response Was NONE.')
            else:
                read = resp.read()
    except httplib.BadStatusLine as exp:
        reporter(msg=('BAD STATUS-LINE ON METHOD MESSAGE %s -'
                      ' INFO: conn %s retry %s'
                      % (exp, conn, retry)),
                 lvl='error',
                 prt=True)
        retry()
    except httplib.ResponseNotReady as exp:
        reporter(msg=('RESPONSE NOT READY MESSAGE %s -'
                      ' INFO: conn %s retry %s'
                      % (exp, conn, retry)),
                 lvl='error',
                 prt=True)
        retry()
    except Exception as exp:
        reporter(msg=('Failure, System will retry. DATA: %s %s %s\nTB:%s'
                      % (exp, conn, retry, traceback.format_exc())),
                 lvl='error',
                 prt=True)
        retry()
    else:
        return resp, read


def ustr(obj):
    """If an Object is unicode convert it.

    :param object:
    :return:
    """
    if obj is not None and isinstance(obj, unicode):
        return str(obj.encode('utf8'))
    else:
        return obj


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

    def _base_headers(headers):
        """Set and return custom headers.

        :param headers:
        :return headers:
        """

        return headers.update(ARGS.get('base_headers'))

    # Set the headers if some custom ones were specified
    if ARGS.get('base_headers'):
        _base_headers(headers=headers)

    return headers


class return_diff(object):
    def __init__(self):
        """Compare the target list to the source list and return the diff."""

        self.target = None
        self.opt = None

    def _checker(self, work_q, payload):
        """Check if an object is in the target, if so append to manager list.

        :param work_q:
        :param payload:
        """
        while True:
            sobj = get_from_q(work_q)
            if sobj is None:
                break
            elif sobj not in self.target:
                if self.opt is not None:
                    self.opt(sobj)
                else:
                    payload.append(sobj)

    def difference(self, target, source, opt=None):
        """Process the diff.

        :param target:
        :param source:
        :param opt: THIS IS AN OPTIONAL FUNCTION...
                    ... which the difference "result" will run.
        :return list:
        """

        import multiprocessing

        # Load the target into the class
        self.target = target
        if opt is not None:
            self.opt = opt

        manager = multiprocessing.Manager()
        proxy_list = manager.list()

        # Get The rate of concurrency
        num_files = len(source)
        concurrency = multiprocessing.cpu_count() * 32
        if concurrency > 128:
            concurrency = 128

        job_processer(num_jobs=num_files,
                      objects=source,
                      job_action=self._checker,
                      concur=concurrency,
                      payload=proxy_list)

        return list(proxy_list)


def prep_payload(auth, container, source, args):
    """Create payload dictionary.

    :param auth:
    :param container:
    :param source:
    :return (dict, dict): payload and headers
    """

    # Unpack the values from Authentication
    token, tenant, user, inet, enet, cnet, aurl, acfep = auth

    # Get the headers ready
    headers = set_headers({'X-Auth-Token': token})

    if args.get('internal'):
        url = inet
    else:
        url = enet

    # Set the upload Payload
    return manager_dict({'c_name': container,
                         'source': source,
                         'tenant': tenant,
                         'headers': headers,
                         'user': user,
                         'cnet': cnet,
                         'aurl': aurl,
                         'url': url,
                         'acfep': acfep})


def restor_perms(local_file, headers):
    """Restore Permissions, UID, GID from metadata.

    :param local_file:
    :param headers:
    """

    import grp
    import os
    import pwd

    # Restore Permissions.
    os.chmod(
        local_file,
        int(headers['x-object-meta-perms'], 8)
    )

    # Lookup user and group name and restore them.
    os.chown(
        local_file,
        pwd.getpwnam(headers['x-object-meta-owner']).pw_uid,
        grp.getgrnam(headers['x-object-meta-group']).gr_gid
    )


def stat_file(local_file):
    """Stat a file and return the Permissions, UID, GID.

    :param local_file:
    :return dict:
    """

    import grp
    import os
    import pwd

    obj = os.stat(local_file)
    return {'X-Object-Meta-perms': oct(obj.st_mode)[-4:],
            'X-Object-Meta-owner': pwd.getpwuid(obj.st_uid).pw_name,
            'X-Object-Meta-group': grp.getgrgid(obj.st_gid).gr_name}


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

        from turbolift import methods
        from turbolift import utils

        with methods.operation(retry=utils.emergency_kill()):
            while self.system:
                busy_chars = ['|', '/', '-', '\\']
                for _cr in busy_chars:
                    # Fixes Errors with OS X due to no sem_getvalue support
                    if self.work_q is not None:
                        if not sys.platform.startswith('darwin'):
                            size = self.work_q.qsize()
                            if size > 0:
                                _qz = 'Number of Jobs in Queue = %s ' % size
                            else:
                                _qz = 'Waiting for in-process Jobs to finish '
                        else:
                            _qz = 'Waiting for in-process Jobs to finish. '
                    else:
                        _qz = 'Please Wait... '
                    sys.stdout.write('\rProcessing - [ %(spin)s ] - %(qsize)s'
                                     % {"qsize": _qz, "spin": _cr})
                    sys.stdout.flush()
                    time.sleep(.05)
                    self.system = self.system

    def indicator_thread(self):
        """indicate that we are performing work in a thread."""

        import multiprocessing

        job = multiprocessing.Process(target=self.indicator)
        job.start()
        return job
