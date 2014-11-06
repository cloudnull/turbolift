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

import turbolift as turbo
import turbolift.utils.basic_utils as basic
import turbolift.utils.report_utils as report

from turbolift import ARGS
from turbolift import info


def get_local_files():
    """Find all files specified in the "source" path.

    This creates a list for all of files using the full path.
    """

    def not_list(item):
        """Exclude items.

        :param item:
        :return True|False:
        """

	if os.path.islink(item):
	    dest = os.readlink(item)
	    if not os.path.exists(dest):
		return True
	elif not os.path.ismount(item):
            if not os.path.getsize(item) > 4831838208:
                return True
        return False

    def indexer(location):
        """Return a list of indexed files.

        :param location:
        :return:
        """

        _location = basic.real_full_path(
            location.encode('utf8')
        )
        if os.path.isdir(_location):
            r_walk = os.walk(_location)
            objects = list()
            for root_inx, inx in [(root, fls) for root, sfs, fls in r_walk]:
                for inode in inx:
                    object_path = basic.jpath(root=root_inx, inode=inode)
                    objects.append(unicode(object_path.decode('utf-8')))
            else:
                return objects

        elif os.path.isfile(_location):
            return [_location]
        else:
            raise turbo.NoFileProvided('No Path was Found for %s' % _location)

    try:
        d_paths = ARGS.get('source')
        if not isinstance(d_paths, list):
            d_paths = [d_paths]

        # Local Index Path
        c_index = [indexer(location=d_path) for d_path in d_paths]

        # make sure my files are only files, and not in the the not_list
        f_index = [item for subl in c_index
                   for item in subl if not_list(item=item)]

        if ARGS.get('exclude'):
            for item in f_index:
                for exclude in ARGS['exclude']:
                    if exclude in item:
                        try:
                            index = f_index.index(item)
                        except ValueError:
                            pass
                        else:
                            f_index.pop(index)

    except Exception as exp:
        raise turbo.SystemProblem('Died for some reason. MESSAGE:\t%s' % exp)
    else:
        report.reporter(
            msg='FILE LIST:\t%s' % f_index,
            lvl='debug',
            prt=False
        )
        return f_index


@contextlib.contextmanager
def operation(retry, obj=None, cleanup=None):
    """This is an operation wrapper, which wraps an operation in try except.

    If clean up is used, a clean up operation will be run should an exception
    happen.

    :param retry:
    :param obj:
    :param cleanup:
    :return:
    """

    try:
        yield retry
    except turbo.NoSource as exp:
        report.reporter(
            msg=('No Source. Message: %s\nADDITIONAL DATA: %s\nTB: %s'
                 % (traceback.format_exc(), exp, obj)),
            lvl='error'
        )
        retry()
    except turbo.SystemProblem as exp:
        report.reporter(
            msg='System Problems Found %s\nADDITIONAL DATA: %s' % (exp, obj),
            lvl='error'
        )
        retry()
    except turbo.AuthenticationProblem as exp:
        retry()
    except KeyboardInterrupt:
        if cleanup is not None:
            cleanup()
        turbo.emergency_kill(reclaim=True)
    except IOError as exp:
        report.reporter(
            msg=('IO ERROR: %s. ADDITIONAL DATA: %s'
                 '\nMESSAGE %s will retry.'
                 '\nSTACKTRACE: %s'
                 % (exp, obj, info.__appname__, traceback.format_exc())),
            lvl='error'
        )
        retry()
    except Exception:
        report.reporter(
            msg=('Failed Operation. ADDITIONAL DATA: %s\n%s will retry\nTB: %s'
                 % (obj, info.__appname__, traceback.format_exc())),
            lvl='error'
        )
        retry()
    finally:
        if cleanup is not None:
            cleanup()


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
        tmp_file = basic.jpath(root=home_dir, inode=file_name)

        # Begin creating the Archive.
        tar = tarfile.open(tmp_file, 'w:gz')
        for name in file_list:
            if basic.file_exists(name) is True:
                tar.add(name)
        tar.close()

        report.reporter(msg='ARCHIVE CREATED: %s' % tmp_file, prt=False)

        if ARGS.get('verify'):
            tar_len = tarfile.open(tmp_file, 'r')
            ver_array = []
            for member_info in tar_len.getmembers():
                ver_array.append(member_info.name)

            count = len(ver_array)
            orig_count = len(file_list)
            if orig_count != count:
                raise turbo.SystemProblem(
                    'ARCHIVE NOT VERIFIED: Archive and File List do not Match.'
                    ' Original File Count = %s, Found Archive Contents = %s'
                    % (orig_count, count)
                )
            report.reporter(
                msg='ARCHIVE CONTENTS VERIFIED: %s files' % count,
            )
    except KeyboardInterrupt:
        if basic.file_exists(tmp_file):
            basic.remove_file(tmp_file)
        turbo.emergency_exit('I have stopped at your command,'
                             ' I removed Local Copy of the Archive')
    except Exception as exp:
        if basic.file_exists(tmp_file):
            basic.remove_file(tmp_file)
            turbo.emergency_exit(
                'I am sorry i just don\'t know what you put into me, Removing'
                ' Local Copy of the Archive.'
            )
        turbo.emergency_exit(
            'Exception while working on the archive. MESSAGE: %s' % exp
        )
    else:
        return tmp_file
