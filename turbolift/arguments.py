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

import argparse
import sys
import os

from turbolift import info

class GetArguments:
    """
    Class to get all of the needed arguments for Turbolift
    """

    #noinspection PyUnusedLocal
    def __init__(self):
        """
        Init for class
        """
        #noinspection PyMethodFirstArgAssignment
        self = None
    
    def get_values(self):
        """
        Look for flags, these are all of the available options for Turbolift.
        """

        defaultcc = 50
        parser = argparse.ArgumentParser(formatter_class=lambda prog: \
                                         argparse.HelpFormatter(prog, max_help_position=50),
                                         usage='%(prog)s',
                                         description='Uploads lots of Files Quickly Cloud Files %(prog)s',
                                         epilog=info.VINFO)

        subparser = parser.add_subparsers(title='Infrastructure Spawner', metavar='<Commands>\n')

        authgroup = parser.add_argument_group('Authentication', 'Authentication against the OpenStack API')
        optionals = parser.add_argument_group('Additional Options', 'Things you might want to add to your operation')



        upaction = subparser.add_parser('upload',
                                        help='Upload Action, Type of upload to be performed as well as '
                                             'Source and Destination')
        upaction.set_defaults(con_per_dir=None, tsync=None, archive=None, upload=True)

        
        taction = subparser.add_parser('tsync',
                                       help='T-Sync Action, Type of upload to be performed as well as '
                                            'Source and Destination')
        taction.set_defaults(con_per_dir=None, upload=None, archive=None, tsync=True)


        archaction = subparser.add_parser('archive',
                                          help='Compress files or directories into a single archive')
        archaction.set_defaults(con_per_dir=None, upload=None, tsync=None, archive=True)


        cpdaction = subparser.add_parser('con-per-dir',
                                                 help='Uploads everything from a given source creating a '
                                                      'single Container per Directory')
        cpdaction.set_defaults(con_per_dir=True, upload=None, tsync=None, archive=None,)


        authgroup.add_argument('-u',
                               '--user',
                               metavar='[USERNAME]',
                               help='Defaults to env[OS_USERNAME]',
                               default=os.environ.get('OS_USERNAME', None))

        authgroup.add_argument('-a',
                               '--apikey',
                               metavar='[API_KEY]',
                               help='Defaults to env[OS_API_KEY]',
                               default=os.environ.get('OS_API_KEY', None))

        authgroup.add_argument('-p',
                               '--password',
                               metavar='[PASSWORD]',
                               help='Defaults to env[OS_PASSWORD]',
                               default=os.environ.get('OS_PASSWORD', None))

        authgroup.add_argument('-r',
                               '--region',
                               metavar='[REGION]',
                               help='Defaults to env[OS_REGION_NAME]',
                               default=os.environ.get('OS_REGION_NAME', None))

        authgroup.add_argument('--auth-url', 
                               metavar='[AUTH_URL]',
                               help='Defaults to env[OS_AUTH_URL]',
                               default=os.environ.get('OS_AUTH_URL', None))

        authgroup.add_argument('--rax-auth',
                               choices=['dfw', 'ord', 'lon'],
                               help='Rackspace Cloud Authentication')
        
        taction.add_argument('-c', '--container',
                             metavar='<name>',
                             required=True,
                             help='Specifies the Container')
        
        taction.add_argument('-s', '--source',
                             metavar='<local>',
                             required=True,
                             help='Local content to be uploaded')

        upaction.add_argument('-c', '--container',
                              metavar='<name>',
                              required=True,
                              help='Specifies the Container')
        
        upaction.add_argument('-s', '--source',
                              metavar='<local>',
                              required=True,
                              help='Local content to be uploaded')

        cpdaction.add_argument('-s', '--source',
                                 metavar='<local>',
                                 required=True,
                                 help='Local content to be uploaded')


        archaction.add_argument('-c', '--container',
                                metavar='<name>',
                                required=True,
                                help='Specifies the Container')

        archaction.add_argument('-s', '--source',
                                metavar='<locals>',
                                default=[], 
                                action='append',
                                required=True,
                                help='Local content to be uploaded, this can be specified as many times as need be.')

        archaction.add_argument('--tar-name',
                                metavar='<name>',
                                help='Name To Use for the Archive')

        archaction.add_argument('--no-cleanup',
                                action='store_true',
                                help='Used to keep the compressed Archive. The archive will be left in the Users '
                                     'Home Folder')

        optionals.add_argument('-I',
                              '--internal',
                              action='store_true',
                              help='Use Service Network')

        optionals.add_argument('--cc',
                               metavar='[CONCURRENCY]',
                               type=int,
                               default=defaultcc,
                               help='Upload Concurrency')

        optionals.add_argument('--verbose',
                               action='store_true',
                               help='Be verbose While Uploading')

        optionals.add_argument('--debug',
                               action='store_true',
                               help='Turn up verbosity to over 9000')

        optionals.add_argument('--version',
                               action='version',
                               version=info.VN)

        args = parser.parse_args()

        if args.region:
            args.region = args.region.upper()

        if args.rax_auth:
            args.rax_auth = args.rax_auth.upper()

        args.defaultcc = defaultcc

        if not args.user:
            parser.print_help()
            sys.exit('\nNo Username was provided, use [--username]\n')
                
        if not (args.apikey or args.password):
            parser.print_help()
            sys.exit('\nNo API Key or Password was provided, use [--apikey]\n')
        
        if args.password and args.apikey:
            parser.print_help()
            sys.exit('\nYou can\'t use both [--apikey] and [--password] in the same command, so I quit...\n')

        if args.rax_auth and args.region:
            parser.print_help()
            sys.exit('\nYou can\'t use both [--rax-auth] and [--region] in the same command, so I quit...\n')

        if args.archive:
            args.cc = 1
            print '\nMESSAGE\t: Because I have not figured out how to multi-thread Archiving, the max Concurrency is 1'
        elif args.cc > 150:
            print '\nMESSAGE\t: You have set the Concurrency Override to', args.cc
            print '\t  This is a lot of Processes and could fork bomb your'
            print '\t  system or cause other nastiness.'
            raw_input('\t  You have been warned, Press Enter to Continue\n')
        elif args.cc != defaultcc:
            print 'MESSAGE\t: Setting a Concurrency Override of', args.cc

        if args.debug:
            args.verbose = True
            print args

        return vars(args)
