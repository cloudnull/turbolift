#!/usr/bin/env python

# - title        : Upload for Swift(Rackspace Cloud Files)
# - description  : Want to upload a bunch files to cloud files? This will do it.
# - License      : GPLv3+
# - author       : Kevin Carter
# - date         : 2011-11-09
# - notes        : This is a Swift(Rackspace Cloud Files) Upload Script
# - Python       : >= 2.6

"""
License Information

This software has no warranty, it is provided 'as is'. It is your
responsibility to validate the behavior of the routines and its
accuracy using the code provided. Consult the GNU General Public
license for further details (see GNU General Public License).

http://www.gnu.org/licenses/gpl.html
"""

import os
import operator

class GetDirsAndFiles(object):
    def __init__(self, tur_arg):
        self.tur_arg = tur_arg
        self.dname = []
        self.cpd = {}


    def get_dir_and_files(self):
        """
        Find all files and folders in all directories, this creates a Dictionary for all directories with a list
        for all of the files found in all of the directories.
        """

        if not self.tur_arg['source'].endswith(os.sep):
            directorypath = '%s%s' % (self.tur_arg['source'], os.sep)
        else:
            directorypath = self.tur_arg['source']

        for (root, directory, file) in os.walk(directorypath, topdown=True, onerror=None, followlinks=False):
            self.dname.append(root)

        for dir in self.dname:
            fs = []
            for fname in os.listdir(dir):
                if os.path.isfile('%s/%s' % (dir, fname)) is True:
                    if fname is not None:
                        fs.append('%s%s%s' % (dir, os.sep, fname))

                    get_file_size = [ [files, os.path.getsize(files)] for files in fs ]
                    sort_size = sorted(get_file_size, key=operator.itemgetter(1), reverse=True)
                    flist = []

                    for file_name, size in sort_size:
                        flist.append(os.path.normpath(file_name))

            if flist:
                self.cpd[os.path.basename(dir)] = flist

        base_dir = os.path.basename(directorypath.rstrip(os.sep))
        self.cpd[base_dir] = self.cpd['']
        del self.cpd['']
        return self.cpd