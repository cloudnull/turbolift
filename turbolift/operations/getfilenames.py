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

class FileNames(object):
    def __init__(self, tur_arg):
        self.tur_arg = tur_arg


    def get_filenames(self):
        """
        Find all files specified in the "source" path, then create a list for all of files using the full path.
        """
        filelist = []
        directorypath = self.tur_arg['source']

        if os.path.isdir(directorypath):
            rootdir = '%s%s' % (os.path.realpath(directorypath), os.sep)
            for (root, subfolders, files) in os.walk(rootdir.encode('utf-8')):
                for file in files:
                    filelist.append(os.path.join(root.encode('utf-8'), file.encode('utf-8')))

            if self.tur_arg['debug']:
                print '\n', rootdir, '\n'

            get_file_size = [ [files, os.path.getsize(files)] for files in filelist ]
            sort_size = sorted(get_file_size, key=operator.itemgetter(1), reverse=True)
            files = []

            for file_name, size in sort_size:
                files.append(file_name)
            return files

        elif not os.path.isdir(directorypath):
            filelist.append(os.path.realpath(directorypath.encode('utf-8')))

            if self.tur_arg['debug']:
                print 'File Name\t:', filelist
            return filelist
        else:
            print 'ERROR\t: path %s does not exist, is not a directory, or is a broken symlink' % directorypath
            sys.exit('MESSAGE\t: Try Again but this time with a valid directory path')