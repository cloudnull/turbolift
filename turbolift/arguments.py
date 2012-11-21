#!/usr/bin/python
# -*- coding: utf-8 -*-

# - title        : Upload for Swift(Rackspace Cloud Files)
# - description  : Want to upload a bunch files to cloud files? This will do it.
# - License      : GPLv3+
# - author       : Kevin Carter
# - date         : 2011-11-09
# - usage        : python turbolift.local.py
# - notes        : This is a Swift(Rackspace Cloud Files) Upload Script
# - Python       : >= 2.6

"""
License Inforamtion

This software has no warranty, it is provided 'as is'. It is your responsibility
to validate the behavior of the routines and its accuracy using the code provided.
Consult the GNU General Public license for further details (see GNU General Public License).

http://www.gnu.org/licenses/gpl.html
"""
import argparse
import sys
import os

# The Version Of the Application
version = '0.4'


class GetArguments:
    def get_values(self):
        """
        Look for flags
        """
        
        defaultcc = 50
        parser = argparse.ArgumentParser(formatter_class=lambda prog: \
                                         argparse.HelpFormatter(prog, max_help_position=50),
                                         usage='%(prog)s [-u] [-a | -p] [options]',
                                         description='Uploads lots of Files Quickly, Using the unpatented GPLv3 Cloud Files %(prog)s'
                                         )
        
        parser.add_argument('-u', '--user', nargs='?',
                            help='Defaults to env[OS_USERNAME]',
                            default=os.environ.get('OS_USERNAME', None))
        
        agroup = parser.add_mutually_exclusive_group()
        agroup.add_argument('-a', '--apikey', nargs='?',
                            help='Defaults to env[OS_API_KEY]',
                            default=os.environ.get('OS_API_KEY', None))
        agroup.add_argument('-p', '--password', nargs='?',
                            help='Defaults to env[OS_PASSWORD]',
                            default=os.environ.get('OS_PASSWORD', None))
        parser.add_argument('-r', '--region', nargs='?', required=True,
                            help='Defaults to env[OS_REGION_NAME]',
                            default=os.environ.get('OS_REGION_NAME', None))
        parser.add_argument('-c', '--container', nargs='?', required=True,
                            help='Specifies the Container')
        parser.add_argument('-s', '--source', nargs='?', required=True,
                            help='Local content to be uploaded')
        
        bgroup = parser.add_mutually_exclusive_group(required=True)
        bgroup.add_argument('-U', '--upload', action='store_true',
                            help='Upload a local Directory or File to Cloud Files')
        bgroup.add_argument('-T', '--tsync', action='store_true',
                            help='Sync a local Directory to Cloud Files. Similar to RSYNC')
        
        parser.add_argument('-I', '--internal', action='store_true',
                            help='Use Service Network')
        parser.add_argument('-P', '--progress', action='store_true',
                            help='Shows Progress While Uploading')
        parser.add_argument('-V', '--veryverbose', action='store_true',
                            help='Turn up verbosity to over 9000')
        
        cgroup = parser.add_mutually_exclusive_group()
        cgroup.add_argument('--compress', action='store_true',
                            help='Compress a file or directory into a single archive')
        cgroup.add_argument('--cc', nargs='?',
                            help='Container Upload Concurrency', type=int,
                            default=defaultcc)
        
        parser.add_argument('--url', nargs='?',
                            help='Defaults to env[OS_AUTH_URL]',
                            default=os.environ.get('OS_AUTH_URL', None))
        parser.add_argument('--version', action='version', version=version)
        
        args = parser.parse_args()
        args.region = args.region.upper()
        args.defaultcc = defaultcc
        
        if not args.user:
            print 'No Username was provided'
            
            parser.print_help()
            exit(1)
        
        if not (args.apikey or args.password):
            print 'No API Key or Password was provided'
            parser.print_help()
            exit(1)
        
        if args.tsync:
            if args.compress:
                print 'ERROR\t: You can not use compression with this function.', \
                    '\n', \
                    'MESSAGE\t: I have quit the application, please try again.'
                exit(1)
        
        if args.veryverbose:
            args.progress = True
        
        if args.upload or args.tsync:
            if args.cc:
                if args.cc > 150:
                    print '\nMESSAGE\t: You have set the Concurency Override to', \
                        args.cc
                    print '\t  This is a lot of Processes and could fork bomb your'
                    print '\t  system or cause other nastyness.'
                    raw_input('\t  You have been warned, Press Enter to Continue\n'
                              )
                
                if not args.cc == args.defaultcc:
                    print 'MESSAGE\t: Setting a Concurency Override of', \
                        args.cc
            
            if args.compress:
                args.multipools = 1
            else:
                args.multipools = args.cc
        return args
