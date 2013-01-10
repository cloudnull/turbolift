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

__author__ = "Kevin Carter"
__contact__ = "Kevin Carter"
__email__ = "kevin@bkintegration.com"
__copyright__ = "2013 All Rights Reserved"
__license__ = "GPLv3+"
__date__ = "2013-01-05"
__version__ = "1.3-Stable"
__status__ = "Production"

# The Version Of the Application
VN = '%s' % __version__

# The Version and Information for the application
VINFO = ('GNU Turbolift %(version)s, '
     'developed by %(author)s, '
     'Licenced Under %(license)s, '
     'FYI : %(copyright)s'
     % { 'version' : __version__,
         'author' : __author__,
         'license' : __license__,
         'copyright' : __copyright__ })