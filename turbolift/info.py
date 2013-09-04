# =============================================================================
# Copyright [2013] [Kevin Carter]
# License Information :
# This software has no warranty, it is provided 'as is'. It is your
# responsibility to validate the behavior of the routines and its accuracy
# using the code provided. Consult the GNU General Public license for further
# details (see GNU General Public License).
# http://www.gnu.org/licenses/gpl.html
# =============================================================================

__author__ = "Kevin Carter"
__contact__ = "Kevin Carter"
__email__ = "kevin@bkintegration.com"
__copyright__ = "2013 All Rights Reserved"
__license__ = "GPLv3+"
__date__ = "2013-08-21"
__version__ = "1.5.0"
__status__ = "Production"
__appname__ = "turbolift"
__description__ = 'OpenStack Swift -Cloud Files- Uploader'
__url__ = 'https://github.com/cloudnull/turbolift.git'

# Service Information
__rax_regions__ = ['dfw', 'ord', 'iad', 'lon', 'syd']
__srv_types__ = ['cloudFilesCDN', 'cloudFiles', 'objectServer']

# The Version Of the Application
__VN__ = '%s' % __version__

# The Version and Information for the application
VINFO = ('GNU Turbolift %(version)s, '
         'developed by %(author)s, '
         'Licenced Under %(license)s, '
         'FYI : %(copyright)s' % {'version': __version__,
                                  'author': __author__,
                                  'license': __license__,
                                  'copyright': __copyright__})
