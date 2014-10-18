# =============================================================================
# Copyright [2014] [Kevin Carter]
# License Information :
# This software has no warranty, it is provided 'as is'. It is your
# responsibility to validate the behavior of the routines and its accuracy
# using the code provided. Consult the GNU General Public license for further
# details (see GNU General Public License).
# http://www.gnu.org/licenses/gpl.html
# =============================================================================

import multiprocessing
import sys
import time


class IndicatorThread(object):
    """Creates a visual indicator while normally performing actions."""

    def __init__(self, work_q=None, run=True, debug=False, quiet=False,
                 msg=None):
        """Create an indicator thread while a job is running.

        :param work_q: ``Queue.Queue`` object
        :param run:  ``bol`` default: True
        :param debug: ``bol`` default: False
        :param quiet: ``bol`` default: False

        Context Manager Usage:
        >>> with IndicatorThread():
        ...     # Your awesome work here...
        ...     print('hello world')

        Object Usage:
        >>> spinner = IndicatorThread()
        >>> job = spinner.indicator_thread()
        >>> # Your amazing work here...
        >>> print('hello world')
        >>> job.terminate()
        """

        self.debug = debug
        self.work_q = work_q
        self.quiet = quiet
        self.run = run
        self.job = None
        self.msg = msg

    def __enter__(self):
        if not self.debug and not self.quiet:
            return self.indicator_thread()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.run = False
        if not self.debug and not self.quiet:
            print('Done.')

        if not self.debug:
            self.job.terminate()

    def indicator(self):
        """Produce the spinner."""

        while self.run:
            busy_chars = ['|', '/', '-', '\\']
            for bc in busy_chars:
                try:
                    size = self.work_q.qsize()
                    if size > 0:
                        note = 'Number of Jobs in Queue = %s ' % size
                    else:
                        note = 'Waiting for in-process Jobs to finish '
                except Exception:
                    note = 'Please Wait... '

                if self.msg:
                    note += self.msg

                sys.stdout.write('\rProcessing - [ %s ] - %s' % (bc, note))
                sys.stdout.flush()
                time.sleep(.1)
                self.run = self.run

    def indicator_thread(self):
        """indicate that we are performing work in a thread."""

        self.job = multiprocessing.Process(target=self.indicator)
        self.job.start()
        return self.job
