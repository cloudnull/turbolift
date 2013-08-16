# =============================================================================
# Copyright [2013] [Kevin Carter]
# License Information :
# This software has no warranty, it is provided 'as is'. It is your
# responsibility to validate the behavior of the routines and its accuracy
# using the code provided. Consult the GNU General Public license for further
# details (see GNU General Public License).
# http://www.gnu.org/licenses/gpl.html
# =============================================================================
import datetime
import os
import sys
import tarfile


class Compressor(object):
    """Compress files and folders into a tar ball."""

    def __init__(self, tur_arg, filelist):
        """Begin the compression of files and folders.

        :param tur_arg:
        :param filelist:
        """

        self.tur_arg = tur_arg
        self.filelist = filelist

    def compress_files(self):
        """If the archive function is used, create a compressed archive.

        From all of files found from the "source" argument. This function
        allows for multiple sources to be added to the compressed archive.
        """
        tmp_file = None
        try:
            # create a tar archive
            print('MESSAGE\t: Creating a Compressed Archive, This may'
                  ' take a minute.')
            date_format = '%a%b%d.%H.%M.%S.%Y'
            today = datetime.datetime.today()
            _ts = today.strftime(date_format)
            home_dir = '%s%s' % (os.getenv('HOME'), os.sep)
            noname_loc = '%s_%s' % ('Archive', _ts)
            print('I Could be == %s' % noname_loc)
            print('I am == %s' % self.tur_arg['tar_name'])
            if self.tur_arg.get('tar_name'):
                set_name = self.tur_arg.get('tar_name', noname_loc)
            else:
                set_name = noname_loc
            print('info %s' % set_name)
            file_name = '%s.tgz' % set_name
            print(file_name)
            tmp_file = '%s%s' % (home_dir, file_name)

            tar = tarfile.open(tmp_file, 'w:gz')
            for name in self.filelist:
                tar.add(name)
            tar.close()

            # Set the Base Path for uploading the file
            self.tur_arg['source'] = tmp_file

            if self.tur_arg['verbose']:
                print('ARCHIVE\t:', tmp_file)

            if self.tur_arg['verify']:
                tar_len = tarfile.open(tmp_file, 'r')
                ver_array = []
                for member_info in tar_len.getmembers():
                    ver_array.append(member_info.name)
                print('ARCHIVE CONTENTS : %s files' % len(ver_array))
        except KeyboardInterrupt:
            print('Caught KeyboardInterrupt, terminating workers\n'
                  'MESSAGE\t: Removing Local Copy of the Archive')
            if os.path.exists(tmp_file):
                os.remove(tmp_file)
            sys.exit('I have stopped at your command')
        except Exception as exp:
            print('ERROR\t: Removing Local Copy of the Archive')
            if os.path.exists(tmp_file):
                os.remove(tmp_file)
                print('I am sorry i just don\'t know what you put into me,'
                      ' Maybe this helps')
                print(exp)
            else:
                print('File "%s" Did not exist yet so there was nothing to'
                      ' delete. here some data you should read'
                      % tmp_file)
                print(exp)
        else:
            return tmp_file
