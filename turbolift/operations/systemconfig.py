import sys
import os
import ConfigParser
import codecs
import stat

class ConfigureationSetup(object):
    def __init__(self, args):
        self.args = args
        self.config_file = args['system_config']
        self.check_perms()
        
    def check_perms(self):
        # If config file is specified, check that it exists and is the proper permissions
        if self.config_file:
            confpath = self.config_file
            if os.path.isfile(os.path.realpath(confpath)):
                mode = oct(stat.S_IMODE(os.stat(confpath).st_mode))
                if not mode == '0600' or not mode == '0400':
                    sys.exit('To use a configuration file the permissions '
                                    'need to be "0600" or "0400"')

    def config_args(self):
        # setup the parser to for safe config parsing with a no value argument
        parser = ConfigParser.SafeConfigParser(allow_no_value=True)

        # Load the configuration file for parsing
        with codecs.open(self.config_file, 'r', encoding='utf-8') as f:
            parser.readfp(f)
        
        # Ensure that there is atleast one section in the configuration file
        if len(parser.sections()) < 1:
            sys.exit('No sections were placed into the configuration file as such I have quit.')
        else:
            # Parse all sections for the configuration file and load them into the shared args
            for section_name in parser.sections():
                for name, value in parser.items(section_name):
                    name = name.encode('utf8')
                    value = value.encode('utf8')
                    self.args.update({name:value})

        return self.args