# =============================================================================
# Copyright [2013] [Kevin Carter]
# License Information :
# This software has no warranty, it is provided 'as is'. It is your
# responsibility to validate the behavior of the routines and its accuracy
# using the code provided. Consult the GNU General Public license for further
# details (see GNU General Public License).
# http://www.gnu.org/licenses/gpl.html
# =============================================================================

import codecs
import ConfigParser
import os
import sys


class ConfigurationSetup(object):
    """Setup the config."""

    def __init__(self, args):
        """Setup Turbolift Configuration.

        :param args:
        """

        self.args = args
        self.config_file = args['system_config']
        self.check_perms()

    def check_perms(self):
        """check parameters."""

        # If config file is specified, check that it exists
        if self.config_file:
            confpath = self.config_file
            if not os.path.isfile(os.path.realpath(confpath)):
                print('File "%s" was not found'
                      % os.path.realpath(confpath))

    def config_args(self):
        """setup the parser for safe config parsing with a no value."""

        # Added per - https://github.com/cloudnull/turbolift/issues/2
        if sys.version_info >= (2, 7, 0):
            parser = ConfigParser.SafeConfigParser(allow_no_value=True)
        else:
            parser = ConfigParser.SafeConfigParser()

        # Load the configuration file for parsing
        with codecs.open(self.config_file, 'r', encoding='utf-8') as cfg:
            parser.readfp(cfg)

        # Ensure that there is atleast one section in the configuration file
        if len(parser.sections()) < 1:
            sys.exit('No sections were placed into the configuration file as'
                     ' such I have quit.')
        else:
            # Parse all sections for the configuration file and load them
            for section_name in parser.sections():
                for name, value in parser.items(section_name):
                    name = name.encode('utf8')
                    value = value.encode('utf8')
                    self.args.update({name: value})
        return self.args
