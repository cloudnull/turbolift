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

import httplib
import tarfile
import sys
from urllib2 import quote

class Compressor(object):
    def __init__(self, tur_arg):
        self.tur_arg = tur_arg


    #noinspection PyBroadException
    def compress_files(self):
        """
        If the archive function is used, create a compressed archive from all of files found from the "source" argument.
        This function allows for multiple sources to be added to the compressed archive.
        """
        global tmp_file
        try:
            filelist = []

            for long_file_list in self.tur_arg['source']:
                directorypath = long_file_list

                if os.path.isdir(directorypath):
                    rootdir = '%s%s' % (os.path.realpath(directorypath), os.sep)
                    for (root, subfolders, files) in os.walk(rootdir.encode('utf-8')):
                        for file in files:
                            filelist.append(os.path.join(root.encode('utf-8'), file.encode('utf-8')))

                elif not os.path.isdir(directorypath):
                    filelist.append(os.path.realpath(directorypath.encode('utf-8')))

                else:
                    print 'ERROR\t: path %s does not exist, is not a directory, or is a broken symlink' % directorypath
                    sys.exit('MESSAGE\t: Try Again but this time with a valid directory path')

            if self.tur_arg['debug']:
                print '\n', filelist, '\n', self.tur_arg['source'], '\n'

            # create a tar archive
            print 'MESSAGE\t: Creating a Compressed Archive, This may take a minute.'
            format = '%a%b%d-%H.%M.%S.%Y.'
            today = datetime.datetime.today()
            ts = today.strftime(format)

            if self.tur_arg['tar_name']:
                tmp_file = '%s%s.tgz' % (ts, self.tur_arg['tar_name'])
            else:
                home_dir = '%s%s' % (os.getenv('HOME'), os.sep)
                file_name = '%s%s.tgz' % (ts, self.tur_arg['container'])
                tmp_file = '%s%s' % (home_dir, file_name)

            tar = tarfile.open(tmp_file, 'w:gz')

            busy_chars = ['|','/','-','\\']
            for name in filelist:
                tar.add(name)

                for c in busy_chars:
                    sys.stdout.write("\rCompressing - [ %s ] " % c)
                    sys.stdout.flush()
                    time.sleep(.01)

            tar.close()

            tarfile.path = tmp_file
            if self.tur_arg['verbose']:
                print 'ARCHIVE\t:', tarfile.path
            tar_len = tarfile.open(tarfile.path, 'r')
            ver_array = []
            for member_info in tar_len.getmembers():
                ver_array.append(member_info.name)
            print 'ARCHIVE CONTENTS : %s files' % len(ver_array)
            return tarfile.path

        except KeyboardInterrupt:
            print 'Caught KeyboardInterrupt, terminating workers'
            print 'MESSAGE\t: Removing Local Copy of the Archive'
            if os.path.exists(tmp_file):
                os.remove(tmp_file)
            sys.exit('\nI have stopped at your command\n')
        except:
            print 'ERROR\t: Removing Local Copy of the Archive'
            if os.path.exists(tmp_file):
                os.remove(tmp_file)
                print 'I am sorry i just don\'t know what you put into me Maybe this helps :\n', sys.exc_info()[1]
            else:
                print 'File "%s" Did not exist yet so there was nothing to delete.' % tmpfile
                print 'here some data you should read', sys.exc_info()[1]
