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
import sys

from turbolift.operations import exceptions


class FileNames(object):
    def __init__(self, tur_arg):
        """Index File Names.

        :param tur_arg:
        """

        self.tur_arg = tur_arg

    def get_filenames(self):
        """Find all files specified in the "source" path.

        This creates a list for all of files using the full path.
        """

        filelist = []
        final_files = []

        if self.tur_arg.get('archive'):
            directory_list = self.tur_arg['source']
        else:
            directory_list = [self.tur_arg['source']]

        for directorypath in directory_list:
            try:
                if os.path.isdir(directorypath):
                    rootdir = '%s%s' % (os.path.realpath(directorypath),
                                        os.sep)
                    for root, sfs, files in os.walk(rootdir.encode('utf8')):
                        for _fl in files:
                            inode = os.path.join(root, _fl)
                            if os.path.exists(inode):
                                filelist.append(inode)
                        if self.tur_arg.get('debug'):
                            print('File List\t: %s' % files)
                    if self.tur_arg.get('no_sort') is True:
                        final_files = filelist
                    else:
                        get_file_size = [[files, os.path.getsize(files)]
                                         for files in filelist]
                        sort_size = sorted(get_file_size,
                                           key=operator.itemgetter(1),
                                           reverse=True)
                        for file_name, size in sort_size:
                            final_files.append(file_name)
                elif not os.path.isdir(directorypath):
                    _full_path = os.path.realpath(
                        directorypath.encode('utf8'))
                    if os.path.exists(_full_path):
                        final_files.append(_full_path)
                    else:
                        raise exceptions.NoFileProvided('No Real Path was'
                                                        ' Found for %s'
                                                        % _full_path)
                else:
                    print('ERROR\t: path %s does not exist, is not a'
                          ' directory, or is a broken symlink' % directorypath)
                    sys.exit('MESSAGE\t: Try Again but this time with a valid'
                             ' directory path')
            except Exception as exp:
                sys.exit('Died for some reason... and here it is\n%s' % exp)
        return final_files
