# =============================================================================
# Copyright [2013] [Kevin Carter]
# License Information :
# This software has no warranty, it is provided 'as is'. It is your
# responsibility to validate the behavior of the routines and its accuracy
# using the code provided. Consult the GNU General Public license for further
# details (see GNU General Public License).
# http://www.gnu.org/licenses/gpl.html
# =============================================================================

import operator
import os


class GetDirsAndFiles(object):
    """Index all files and folders."""

    def __init__(self, tur_arg):
        """Index files and Directories.

        :param tur_arg:
        """

        self.tur_arg = tur_arg
        self.dname = []
        self.cpd = {}

    def get_dir_and_files(self):
        """Find all files and folders in all directories.

        this creates a dictionary for all directories with a list for all of
        the files found in all of the directories.
        """
        for source in self.tur_arg['source']:
            if not source.endswith(os.sep):
                directorypath = '%s%s' % (source, os.sep)
            else:
                directorypath = source
            for root, directory, file_n in os.walk(directorypath,
                                                   topdown=True,
                                                   onerror=None,
                                                   followlinks=False):
                self.dname.append(root)

        for dir_n in self.dname:
            _fs = []
            flist = []
            for fname in os.listdir(dir_n):
                if fname is not None:
                    inode = '%s%s%s' % (dir_n, os.sep, fname)
                    if all([os.path.isfile(inode), os.path.exists(inode)]):
                        _fs.append(inode)
            if self.tur_arg.get('no_sort'):
                flist = _fs
            else:
                get_file_size = [[files, os.path.getsize(files)]
                                 for files in _fs]
                sort_size = sorted(get_file_size,
                                   key=operator.itemgetter(1),
                                   reverse=True)
                for file_name, size in sort_size:
                    flist.append(os.path.realpath(file_name))
            if flist:
                self.cpd[os.path.basename(dir_n)] = flist
        # gets rid of an open container name
        base_dir = os.path.basename(directorypath.rstrip(os.sep))
        self.cpd[base_dir] = self.cpd['']
        del self.cpd['']
        return self.cpd
