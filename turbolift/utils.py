# =============================================================================
# Copyright [2015] [Kevin Carter]
# License Information :
# This software has no warranty, it is provided 'as is'. It is your
# responsibility to validate the behavior of the routines and its accuracy
# using the code provided. Consult the GNU General Public license for further
# details (see GNU General Public License).
# http://www.gnu.org/licenses/gpl.html
# =============================================================================


def check_basestring(item):
    """Return ``bol`` on string check item.

    :param item: Item to check if its a string
    :type item: ``str``
    :returns: ``bol``
    """
    try:
        return isinstance(item, (basestring, unicode))
    except NameError:
        return isinstance(item, str)


def byte_encode(string):
    try:
        return string.encode('utf-8')
    except AttributeError:
        return string
