# =============================================================================
# Copyright [2013] [Kevin Carter]
# License Information :
# This software has no warranty, it is provided 'as is'. It is your
# responsibility to validate the behavior of the routines and its accuracy
# using the code provided. Consult the GNU General Public license for further
# details (see GNU General Public License).
# http://www.gnu.org/licenses/gpl.html
# =============================================================================


class IndicatorThread(object):
    def __init__(self, work_q=None, system=True):
        self.work_q = work_q
        self.system = system

    def indicator(self):
        import sys
        import time
        while self.system:
            busy_chars = ['|', '/', '-', '\\']
            for _cr in busy_chars:
                # Fixes Errors with OS X due to no sem_getvalue support
                if not self.work_q is None:
                    if not sys.platform.startswith('darwin'):
                        _qz = ('Number of Jobs Left [ %s ]'
                               % self.work_q.qsize())
                    else:
                        _qz = "OS X Can't Count... Please Wait."
                else:
                    _qz = ''
                sys.stdout.write('\rProcessing - [ %(spin)s ] - %(qsize)s'
                                 % {"qsize": _qz,
                                    "spin": _cr})
                sys.stdout.flush()
                time.sleep(.05)
                self.system = self.system

    def indicator_thread(self):
        """
        indicate that we are performing work
        """
        from multiprocessing import Process
        job = Process(target=self.indicator)
        job.start()
        return job
