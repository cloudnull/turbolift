import time
import sys
import os

# Local Modules
from turbolift import info

def manager_list(bl=None):
    """
    OPTIONAL Variable :
    bl = 'Base List'

    Create a shared list using multiprocessing Managers
    If you use the "bl" variable you can specify a prebuilt list
    The default is that bl=None
    """
    import multiprocessing
    manager = multiprocessing.Manager()
    if bl:
        managed_dictionary = manager.list(bl)
    else:
        managed_dictionary = manager.list()
    return managed_dictionary


def manager_dict(bd=None):
    """
    OPTIONAL Variable :
    bd = 'Base Dictionary'
    
    Create a shared dictionary using multiprocessing Managers
    If you use the "bd" variable you can specify a prebuilt dict
    the default is that bd=None
    """
    import multiprocessing
    manager = multiprocessing.Manager()
    if bd:
        managed_dictionary = manager.dict(bd)
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
    for dt in iters:
        worker_q.put(dt)
    return worker_q


def worker_proc(job_action, num_jobs, t_args=None):
    """
    job_action="What function will be used",

    num_jobs="The number of jobs that will be processed"

    Requires the job_action and num_jobs variables for functionality.
    All threads produced by the worker are limited by the number of concurrency specified by the user.
    The Threads are all made active prior to them processing jobs.
    """
    import multiprocessing
    # prep the List for actions
    processes = []

    # Enable for multiprocessing Debug
    #multiprocessing.log_to_stderr(level='DEBUG')

    if num_jobs < (multiprocessing.cpu_count()):
        num_threads = num_jobs
    else:
        num_threads = (multiprocessing.cpu_count())
    
    proc_name = '%s-%s-Worker' % (info.__name__, str(job_action).split()[2])
    
    for _ in range(num_threads):
            processes = [multiprocessing.Process(name=proc_name,
                                                 target=job_action,) for _ in range(num_jobs)]

    for j in processes:
        j.start()

    for j in processes:
        j.join()


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
    for i in range(attempts): 
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