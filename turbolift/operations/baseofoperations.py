import sys
import os

from turbolift.operations import getdirsandfiles, compressfiles, getfilenames
from turbolift.operations import uploader, novacommands, generators


class BaseCamp(object):
    def __init__(self, tur_arg):
        self.tur_arg = generators.manager_dict(tur_arg)
        try:
            novacommands.NovaAuth(self.tur_arg).osauth()
        except Exception, e:
            print e
            sys.exit('Authentication against the NOVA API had issues, so I died')
            
    def set_concurency(self):            
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
        self.gfn = getfilenames.FileNames(self.tur_arg).get_filenames()
        self.tur_arg['fc'] = len(self.gfn)
        if self.tur_arg['verbose']:
            print('MESSAGE\t: "%s" files have been found.' % self.tur_arg['fc'])
        self.set_concurency()


    def con_per_dir(self):
        pay_load = getdirsandfiles.GetDirsAndFiles(self.tur_arg).get_dir_and_files()
        self.tur_arg['fc'] = len(pay_load.values())
        self.set_concurency()

        uploader.UploadAction(tur_arg=self.tur_arg,
                  pay_load=pay_load.items()).job_prep()


    def archive(self):
        self.tur_arg['multipools'] = 1
        self.basic_file_structure()
        cf = compressfiles.Compressor(self.tur_arg,
                                      self.gfn).compress_files()
        cfs = os.path.getsize(cf)
        print 'MESSAGE\t: Uploading... %s bytes' % cfs
        pay_load = {self.tur_arg['container']:[cf]}
        uploader.UploadAction(tur_arg=self.tur_arg,
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
        self.basic_file_structure()
        self.pay_load = {self.tur_arg['container']:self.gfn}

        if self.tur_arg['debug']:
            print('FILELIST\t: %s\n'
                  'ARGS\t: %s\n' % (self.pay_load, self.tur_arg))

        # Upload our built payload
        uploader.UploadAction(tur_arg=self.tur_arg,
                              pay_load=self.pay_load.items()).job_prep()