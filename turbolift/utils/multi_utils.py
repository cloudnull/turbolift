# =============================================================================
# Copyright [2013] [Kevin Carter]
# License Information :
# This software has no warranty, it is provided 'as is'. It is your
# responsibility to validate the behavior of the routines and its accuracy
# using the code provided. Consult the GNU General Public license for further
# details (see GNU General Public License).
# http://www.gnu.org/licenses/gpl.html
# =============================================================================
import contextlib
import multiprocessing
import Queue
import sys
import time

import turbolift as turbo
import turbolift.utils.basic_utils as basic
import turbolift.utils.report_utils as report

from turbolift import ARGS
from turbolift import methods


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

        with methods.operation(retry=turbo.emergency_kill):
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
                    time.sleep(.1)
                    self.system = self.system

    def indicator_thread(self):
        """indicate that we are performing work in a thread."""

        job = multiprocessing.Process(target=self.indicator)
        job.start()
        return job


def manager_dict(dictionary):
    """Create and return a Manger Dictionary.

    :param dictionary:
    :return dict:
    """

    manager = multiprocessing.Manager()
    return manager.dict(dictionary)


def basic_queue(iters=None):
    """Uses a manager Queue, from multiprocessing.

    All jobs will be added to the queue for processing.
    :param iters:
    """

    worker_q = multiprocessing.Queue()
    if iters is not None:
        for _dt in iters:
            worker_q.put(_dt)
    return worker_q


def get_from_q(queue):
    """Returns the file or a sentinel value.

    :param queue:
    :return item|None:
    """

    try:
        wfile = queue.get(timeout=5)
    except Queue.Empty:
        return None
    else:
        return wfile


def worker_proc(job_action, concurrency, queue, kwargs, opt):
    """Requires the job_action and num_jobs variables for functionality.

    :param job_action: What function will be used
    :param concurrency: The number of jobs that will be processed
    :param queue: The Queue
    :param t_args: Optional

    All threads produced by the worker are limited by the number of concurrency
    specified by the user. The Threads are all made active prior to them
    processing jobs.
    """

    arguments = []
    for item in [queue, opt, kwargs]:
        if item is not None:
            arguments.append(item)

    jobs = [multiprocessing.Process(target=job_action,
                                    args=tuple(arguments))
            for _ in xrange(concurrency)]

    report.reporter(
        msg='Tread Starting Cycle',
        lvl='info',
        log=True,
        prt=True
    )
    join_jobs = []
    for _job in jobs:
        basic.stupid_hack(wait=.01)
        join_jobs.append(_job)
        _job.Daemon = True
        _job.start()

    for job in join_jobs:
        job.join()


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

        job_processer(
            num_jobs=num_files,
            objects=source,
            job_action=self._checker,
            concur=concurrency,
            opt=proxy_list
        )

        return list(proxy_list)


def job_processer(num_jobs, objects, job_action, concur, kwargs=None,
                  opt=None):
    """Process all jobs in batches.

    :param num_jobs:
    :param objects:
    :param job_action:
    :param concur:
    :param payload:
    """

    count = 0
    batch_size = basic.batcher(num_files=num_jobs)
    for work in basic.batch_gen(data=objects,
                                batch_size=batch_size,
                                count=num_jobs):
        count += 1
        report.reporter(msg='Job Count %s' % count)
        work_q = basic_queue(work)
        with spinner(work_q=work_q):
            worker_proc(job_action=job_action,
                        concurrency=concur,
                        queue=work_q,
                        opt=opt,
                        kwargs=kwargs)


def set_concurrency(args, file_count):
    """Concurrency is a user specified variable when the arguments parsed.

    :param args:

    However if the number of things Turbo lift has to do is less than the
    desired concurency, then turbolift will lower the concurency rate to
    the number of operations.
    """

    def verbose(ccr):
        report.reporter(
            msg='MESSAGE: We are creating %s Processes' % ccr,
            prt=False
        )
        return ccr

    _cc = args.get('cc')

    if _cc > file_count:
        report.reporter(
            msg=('MESSAGE: There are less things to do than the number of'
                 ' concurrent processes specified by either an override'
                 ' or the system defaults. I am leveling the number of'
                 ' concurrent processes to the number of jobs to perform.'),
            lvl='warn'
        )
        return verbose(ccr=file_count)
    else:
        return verbose(ccr=_cc)


def doerator(work_q, kwargs):
    """Do Jobs until done.

    :param work_q:
    :param job:
    """
    job = kwargs.pop('cf_job')
    while True:
        # Get the file that we want to work with
        wfile = get_from_q(queue=work_q)

        # If Work is None return None
        if wfile is None:
            break
        try:
            # Do the job that was provided
            kwargs['u_file'] = wfile
            job(**kwargs)
        except EOFError:
            turbo.emergency_kill()
        except KeyboardInterrupt:
            turbo.emergency_kill(reclaim=True)


@contextlib.contextmanager
def spinner(work_q=None):
    """Show a fancy spinner while we have work running.

    :param work_q:
    :return:
    """

    if any([ARGS.get('verbose') is True, ARGS.get('quiet') is True]):
        yield
    else:
        set_itd = IndicatorThread(work_q=work_q)
        try:
            itd = set_itd.indicator_thread()
            yield
        finally:
            itd.terminate()
