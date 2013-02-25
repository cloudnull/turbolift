import sys
import os

from turbolift.operations import getdirsandfiles, compressfiles, getfilenames
from turbolift.operations import cfactions, novacommands, generators


class BaseCamp(object):
    def __init__(self, tur_arg):
        """
        tur_arg = 'Parsed Arguments'
        BaseCamp acts as a simple metthod for seperating out methods from one another.
        With base camp all start points are engaged.
        """
        self.tur_arg = generators.manager_dict(tur_arg)
        try:
            self.nova = novacommands.NovaAuth(self.tur_arg)
            self.nova.osauth()
        except Exception, e:
            print e
            sys.exit('Authentication against the NOVA API had issues, so I died')


    def set_concurency(self):
        """
        Concurency is a user specified variable when the arguments are parsed.
        However if the number of things Turbo lift has to do is less than the
        desired concurency, then turbolift will lower the concurency rate to
        the number of operations.
        """
        if self.tur_arg['cc'] > self.tur_arg['fc']:
            print('MESSAGE\t: There are less things to do than the number of concurrent\n'
                  '\t  processes specified by either an override or the system defaults.\n'
                  '\t  I am leveling the number of concurrent processes to the number of\n'
                  '\t  jobs to perform.')
            self.tur_arg['multipools'] = self.tur_arg['fc']
        else:
            self.tur_arg['multipools'] = self.tur_arg['cc']

        if self.tur_arg['verbose']:
            print('MESSAGE\t: We are going to create Processes : %s\n'
                   % (self.tur_arg['multipools']))


    def basic_file_structure(self):
        """
        This is a simple method for understanding the locations for all of
        the files that we are going to uploading
        """
        self.gfn = getfilenames.FileNames(self.tur_arg).get_filenames()
        self.tur_arg['fc'] = len(self.gfn)
        if self.tur_arg['verbose']:
            print('MESSAGE\t: "%s" files have been found.' % self.tur_arg['fc'])
        self.set_concurency()


    def con_per_dir(self):
        """
        con_per_dir is a method desigend to upload all of the contents of a directory into a container.
        Using this method will craete a new container for all directories found from within a path.
        """
        pay_load = getdirsandfiles.GetDirsAndFiles(self.tur_arg).get_dir_and_files()
        self.tur_arg['fc'] = len(pay_load.values())
        self.set_concurency()

        cfactions.CloudFilesActions(tur_arg=self.tur_arg,
                                    pay_load=pay_load.items()).job_prep()


    def archive(self):
        """
        The archive function was made to simply build a Tarball of all of the contents found from within a given path.
        With this method multiple "sources" can be used as they will simply preserve the upload source from within the tarball.
        """
        self.basic_file_structure()
        self.tur_arg['multipools'] = 1

        cf = compressfiles.Compressor(self.tur_arg,
                                      self.gfn).compress_files()
        cfs = os.path.getsize(cf)
        print 'MESSAGE\t: Uploading... %s bytes' % cfs
        pay_load = {self.tur_arg['container']:[cf]}
        cfactions.CloudFilesActions(tur_arg=self.tur_arg,
                                    pay_load=pay_load.items()).job_prep()

        # Nuke the left over file if there was one.
        if self.tur_arg['no_cleanup']:
            print 'MESSAGE\t: Archive Location = %s' % cf
        else:
            print 'MESSAGE\t: Removing Local Copy of the Archive'
            if os.path.exists(cf):
                os.remove(cf)
            else:
                print 'File "%s" Did not exist so there was nothing to delete.' % cf


    def file_upload(self):
        """
        This is the first and most basic method, using file_upload is to simply upload
        all files and folders to a specified container.
        """
        self.basic_file_structure()
        self.pay_load = {self.tur_arg['container']:self.gfn}

        if self.tur_arg['debug']:
            print('FILELIST\t: %s\n'
                  'ARGS\t: %s\n' % (self.pay_load, self.tur_arg))

        # Upload our built payload
        cfactions.CloudFilesActions(tur_arg=self.tur_arg,
                                    pay_load=self.pay_load.items()).job_prep()


    def delete_download(self):
        """
        Downloads all of the files in a container or
        Deletes all of the files in a container
        """
        resp = self.nova.container_check(self.tur_arg['container'])
        if resp.status == 404:
            sys.exit('The Container you want to use does not exist')
        cfl = self.nova.get_object_list(self.tur_arg['container'])
        self.tur_arg['fc'] = len(cfl)
        print('Processing "%s" Objects' % self.tur_arg['fc'])
        self.set_concurency()
        self.pay_load = {self.tur_arg['container']:cfl}

        if self.tur_arg['debug']:
            print('FILELIST\t: %s\n'
                  'ARGS\t: %s\n' % (self.pay_load, self.tur_arg))

        # Run our built payload
        cfactions.CloudFilesActions(tur_arg=self.tur_arg,
                                    pay_load=self.pay_load.items()).job_prep()

        # If we were deleting things check to see that they were deleted
        if self.tur_arg['delete']:
            self.check_deleted()


    def check_deleted(self):
        # Pull a file list, if 0 delete container
        cfl = self.nova.get_object_list(self.tur_arg['container'])
        self.tur_arg['fc'] = len(cfl)
        if self.tur_arg['fc'] > 0:
            print('We found that some scraps from within the '
                  'container that were not removed during the delete operation. '
                  'We are retrying the operation now...')
            self.delete_download()
        else:
            if not self.tur_arg['save_container']:
                # Remove the deleted container
                self.nova.container_deleter(self.tur_arg['container'])
                # Check that the container was deleted
                resp = self.nova.container_check(self.tur_arg['container'])
                if not resp.status == (404 or 204):
                    print('NOVA-API FAILURE ==> INFO: %s %s %s' % (resp.status,
                                                                     resp.reason,
                                                                     self.tur_arg['container']))
                    sys.exit('There was an issue removing the container.')