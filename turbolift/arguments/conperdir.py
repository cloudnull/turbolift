# =============================================================================
# Copyright [2013] [kevin]
# License Information :
# This software has no warranty, it is provided 'as is'. It is your
# responsibility to validate the behavior of the routines and its accuracy
# using the code provided. Consult the GNU General Public license for further
# details (see GNU General Public License).
# http://www.gnu.org/licenses/gpl.html
# =============================================================================


def conperdir_actions(subparser, multi_source_args, cdn_args):
    """Container Per Local Directory actions.

    :param subparser:
    :param multi_source_args:
    :param cdn_args:
    """

    cpdaction = subparser.add_parser('con-per-dir',
                                     parents=[multi_source_args, cdn_args],
                                     help=('Uploads everything from a'
                                           ' given source creating a single'
                                           ' Container per Directory'))
    cpdaction.set_defaults(con_per_dir=True)