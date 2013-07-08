# =============================================================================
# Copyright [2013] [Kevin Carter]
# License Information :
# This software has no warranty, it is provided 'as is'. It is your
# responsibility to validate the behavior of the routines and its accuracy
# using the code provided. Consult the GNU General Public license for further
# details (see GNU General Public License).
# http://www.gnu.org/licenses/gpl.html
# =============================================================================
import time

# Local Modules
from turbolift import info


def manager_list(_bl=None):
    """
    OPTIONAL Variable :
    bl = 'Base List'

    Create a shared list using multiprocessing Managers
    If you use the "bl" variable you can specify a prebuilt list
    The default is that bl=None
    """
    import multiprocessing
    manager = multiprocessing.Manager()
    if _bl:
        managed_dictionary = manager.list(_bl)
    else:
        managed_dictionary = manager.list()
    return managed_dictionary


def manager_dict(_bd=None):
    """
    OPTIONAL Variable :
    bd = 'Base Dictionary'
    Create a shared dictionary using multiprocessing Managers
    If you use the "bd" variable you can specify a prebuilt dict
    the default is that bd=None
    """
    import multiprocessing
    manager = multiprocessing.Manager()
    if _bd:
        managed_dictionary = manager.dict(_bd)
    else:
        managed_dictionary = manager.dict()
    return managed_dictionary


def manager_queue(iters):
    """
    iters="The iterable variables"

    Uses a manager Queue, from multiprocessing.
    All jobs will be added to the queue for processing.
    """
    import multiprocessing
    manager = multiprocessing.Manager()
    worker_q = manager.Queue()
    for _dt in iters:
        worker_q.put(_dt)
    return worker_q


def worker_proc(job_action, multipools, work_q):
    """
    job_action="What function will be used",
    multipools="The number Threads we are working on"
    num_jobs="The total Number of Jobs we need to do"
    Requires the job_action and num_jobs variables for functionality.
    All threads produced by the worker are limited by the number of
    concurrency specified by the user. The Threads are all made active prior
    to them processing jobs.
    """
    import multiprocessing

    # Enable for multiprocessing Debug
    # multiprocessing.log_to_stderr(level='DEBUG')

    proc_name = 'Turbolift-%s-Worker' % info.__appname__
    processes = []
    for _ in xrange(multipools):
        _jo = multiprocessing.Process(name=proc_name,
                                      target=job_action,
                                      args=(work_q,))
        processes.append(_jo)
        _jo.daemon = True
        _jo.start()

    for _ in range(multipools):
        work_q.put(None)

    for _jo in processes:
        _jo.join()


# ACTIVE STATE retry loop
# http://code.activestate.com/recipes/578163-retry-loop/
class RetryError(Exception):
    pass


def retryloop(attempts, timeout=None, delay=None, backoff=1):
    """
    Enter the amount of retries you want to perform.
    The timeout allows the application to quit on "X".
    delay allows the loop to wait on fail. Useful for making REST calls.
    Example:
        Function for retring an action.
        for retry in retryloop(attempts=10, timeout=30, delay=1, backoff=1):
            something
            if somecondition:
                retry()
    """
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
    raise RetryError
