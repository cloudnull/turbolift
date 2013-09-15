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
import datetime
import os
import tarfile
import traceback

import turbolift as clds
from turbolift import info
from turbolift import utils
from turbolift.worker import ARGS
from turbolift.worker import LOG


def get_local_files():
    """Find all files specified in the "source" path.

    This creates a list for all of files using the full path.
    """

    def not_list(item):
        """Exclude items.

        :param item:
        :return True|False:
        """
        if all([not os.path.islink(item),
                not os.path.ismount(item)]):
            if not os.path.getsize(item) > 4831838208:
                return True
        else:
            return False

    def indexer(location):
        """Return a list of indexed files.

        :param location:
        :return:
        """

        _location = utils.real_full_path(
            location.encode('utf8')
        )
        if os.path.isdir(_location):
            r_walk = os.walk(_location)
            indexes = [(root, fls) for root, sfs, fls in r_walk]
            return [utils.jpath(root=inx[0], inode=ind)
                    for inx in indexes for ind in inx[1]]
        elif os.path.isfile(_location):
            return [_location]
        else:
            raise clds.NoFileProvided('No Path was Found for %s' % _location)

    try:
        d_paths = ARGS.get('source')
        if not isinstance(d_paths, list):
            d_paths = [d_paths]

        # Local Index Path
        c_index = [indexer(location=d_path) for d_path in d_paths]

        # make sure my files are only files, and compare it with the not_list
        f_index = [item for subl in c_index
                   for item in subl if not_list(item=item)]
    except Exception as exp:
        raise clds.SystemProblem('Died for some reason. MESSAGE:\t%s' % exp)
    else:
        LOG.debug('FILE LIST:\t%s', f_index)
        return f_index


@contextlib.contextmanager
def spinner(work_q=None):
    """Show a fancy spinner while we have work running.

    :param work_q:
    :return:
    """

    # Stop Spinning
    if any([ARGS.get('verbose') is True, ARGS.get('quiet') is True]):
        yield
    else:
        try:
            set_itd = utils.IndicatorThread(work_q=work_q)
            itd = set_itd.indicator_thread()
            yield
        finally:
            itd.terminate()


@contextlib.contextmanager
def operation(retry, conn=None, obj=None, cleanup=None):
    """This is an operation wrapper, which wraps an operation in try except.

    If clean up is used, a clean up operation will be run should an exception
    happen.

    :param retry:
    :param conn:
    :param obj:
    :param cleanup:
    :return:
    """
    try:
        yield retry
    except clds.NoSource as exp:
        utils.reporter(
            msg=('No Source. Message: %s\nADDITIONAL DATA: %s\nTB: %s'
                 % (traceback.format_exc(), exp, obj)),
            lvl='error'
        )
        retry()
    except clds.SystemProblem as exp:
        utils.reporter(
            msg='System Problems Found %s\nADDITIONAL DATA: %s' % (exp, obj),
            lvl='error'
        )
        retry()
    except KeyboardInterrupt:
        if cleanup is not None:
            cleanup()
        utils.emergency_kill(reclaim=True)
    except IOError as exp:
        utils.reporter(
            msg=('IO ERROR: %s. ADDITIONAL DATA: %s'
                 '\nMESSAGE %s will retry.'
                 '\nSTACKTRACE: %s'
                 % (exp, obj, info.__appname__, traceback.format_exc())),
            lvl='error'
        )
        retry()
    except Exception as exp:
        utils.reporter(
            msg=('Failed Operation. ADDITIONAL DATA: %s\n%s will retry\nTB: %s'
                 % (obj, info.__appname__, traceback.format_exc())),
            lvl='error'
        )
        retry()
    finally:
        if cleanup is not None:
            cleanup()
        if conn is not None:
            conn.close()


def compress_files(file_list):
    """If the archive function is used, create a compressed archive.

    :param file_list:

    This function allows for multiple sources to be added to the
    compressed archive.
    """

    tmp_file = None
    try:
        # Set date and time
        date_format = '%a%b%d.%H.%M.%S.%Y'
        today = datetime.datetime.today()
        _ts = today.strftime(date_format)

        # Get Home Directory
        home_dir = os.getenv('HOME')

        # Set the name of the archive.
        set_name = ARGS.get('tar_name', '%s_%s' % ('Archive', _ts))
        file_name = '%s.tgz' % set_name

        # Set the working File.
        tmp_file = utils.jpath(root=home_dir, inode=file_name)

        # Begin creating the Archive.
        tar = tarfile.open(tmp_file, 'w:gz')
        for name in file_list:
            if utils.file_exists(name) is True:
                tar.add(name)
        tar.close()

        utils.reporter(msg='ARCHIVE CREATED: %s' % tmp_file, prt=False)

        if ARGS.get('verify'):
            tar_len = tarfile.open(tmp_file, 'r')
            ver_array = []
            for member_info in tar_len.getmembers():
                ver_array.append(member_info.name)

            count = len(ver_array)
            orig_count = len(file_list)
            if orig_count != count:
                raise clds.SystemProblem(
                    'ARCHIVE NOT VERIFIED: Archive and File List do not Match.'
                    ' Original File Count = %s, Found Archive Contents = %s'
                    % (orig_count, count)
                )
            utils.reporter(
                msg='ARCHIVE CONTENTS VERIFIED: %s files' % count,
            )
    except KeyboardInterrupt:
        if utils.file_exists(tmp_file):
            utils.remove_file(tmp_file)
        utils.emergency_exit('I have stopped at your command,'
                             ' I removed Local Copy of the Archive')
    except Exception as exp:
        if utils.file_exists(tmp_file):
            utils.remove_file(tmp_file)
            utils.emergency_exit(
                'I am sorry i just don\'t know what you put into me, Removing'
                ' Local Copy of the Archive.'
            )
        utils.emergency_exit(
            'Exception while working on the archive. MESSAGE: %s' % exp
        )
    else:
        return tmp_file
