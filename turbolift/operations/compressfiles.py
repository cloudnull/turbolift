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
import os
from urllib2 import quote
import datetime
import time


class Compressor(object):
    def __init__(self, tur_arg, filelist):
        self.tur_arg = tur_arg
        self.filelist = filelist


    #noinspection PyBroadException
    def compress_files(self):
        """
        If the archive function is used, create a compressed archive from all of files found from the "source" argument.
        This function allows for multiple sources to be added to the compressed archive.
        """
        try:
            # create a tar archive
            print 'MESSAGE\t: Creating a Compressed Archive, This may take a minute.'
            date_format = '%a%b%d-%H.%M.%S.%Y.'
            today = datetime.datetime.today()
            ts = today.strftime(date_format)
    
            if self.tur_arg['tar_name']:
                tmp_file = '%s%s.tgz' % (ts, self.tur_arg['tar_name'])
            else:
                home_dir = '%s%s' % (os.getenv('HOME'), os.sep)
                file_name = '%s%s.tgz' % (ts, self.tur_arg['container'])
                tmp_file = '%s%s' % (home_dir, file_name)
    
            tar = tarfile.open(tmp_file, 'w:gz')
    
            busy_chars = ['|','/','-','\\']
            for name in self.filelist:
                tar.add(name)
                for c in busy_chars:
                    sys.stdout.write("\rCompressing - [ %s ] " % c)
                    sys.stdout.flush()
                    time.sleep(.01)
            tar.close()

            # Set the Base Path for uploading the file
            self.tur_arg['source'] = tmp_file

            if self.tur_arg['verbose']:
                print 'ARCHIVE\t:', tmp_file
    
            if self.tur_arg['verify']:
                tar_len = tarfile.open(tmp_file, 'r')
                ver_array = []
                for member_info in tar_len.getmembers():
                    ver_array.append(member_info.name)
                    for c in busy_chars:
                        sys.stdout.write("\rComputing Number of files - [ %s ] " % c)
                        sys.stdout.flush()
                        time.sleep(.01)
                print 'ARCHIVE CONTENTS : %s files' % len(ver_array)

            return tmp_file

        except KeyboardInterrupt:
            print('Caught KeyboardInterrupt, terminating workers\n'
                  'MESSAGE\t: Removing Local Copy of the Archive')
            if os.path.exists(tmp_file):
                os.remove(tmp_file)
            sys.exit('I have stopped at your command')
        except Exception, e:
            print('ERROR\t: Removing Local Copy of the Archive')
            if os.path.exists(tmp_file):
                os.remove(tmp_file)
                print 'I am sorry i just don\'t know what you put into me, Maybe this helps'
                print e, sys.exc_info()[1]
            else:
                print('File "%s" Did not exist yet so there was nothing to delete. '
                      'here some data you should read' % tmp_file)
                print e, sys.exc_info()[1]
