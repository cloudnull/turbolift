# =============================================================================
# Copyright [2013] [Kevin Carter]
# License Information :
# This software has no warranty, it is provided 'as is'. It is your
# responsibility to validate the behavior of the routines and its accuracy
# using the code provided. Consult the GNU General Public license for further
# details (see GNU General Public License).
# http://www.gnu.org/licenses/gpl.html
# =============================================================================
import datetime
import errno
import grp
import json
import os
import pwd
import random
import re
import string
import tempfile
import time

import turbolift as turbo
import turbolift.utils.report_utils as report



def json_encode(read):
    """Return a json encoded object.

    :param read:
    :return:
    """

    return json.loads(read)


def dict_pop_none(dictionary):
    """Parse all keys in a dictionary for Values that are None.

    :param dictionary: all parsed arguments
    :returns dict: all arguments which are not None.
    """

    return dict([(key, value) for key, value in dictionary.iteritems()
                 if value is not None if value is not False])


def jpath(root, inode):
    """Return joined directory / path

    :param root:
    :param inode:
    :return "root/inode":
    """

    return os.path.join(root, inode)


def rand_string(length=15):
    """Generate a Random string."""

    chr_set = string.ascii_uppercase
    output = ''

    for _ in range(length):
        output += random.choice(chr_set)
    return output


def create_tmp():
    """Create a tmp file.

    :return str:
    """

    return tempfile.mkstemp()[1]


def remove_file(filename):
    """Remove a file if its found.

    :param filename:
    """

    if file_exists(filename):
        try:
            os.remove(filename)
        except OSError:
            pass


def file_exists(filename):
    """Return True|False if a File Exists.

    :param filename:
    :return True|False:
    """

    return os.path.exists(filename)


def batcher(num_files):
    """Check the batch size and return it.

    :param num_files:
    :return int:
    """

    batch_size = turbo.ARGS.get('batch_size')
    report.reporter(
        msg='Job process MAX Batch Size is "%s"' % batch_size,
        lvl='debug',
        log=True,
        prt=False
    )
    ops = num_files / batch_size + 1
    report.reporter(
        msg='This will take "%s" operations to complete.' % ops,
        lvl='warn',
        log=True,
        prt=True
    )
    return batch_size


def collision_rename(file_name):
    """Rename file on Collision.

    If the file name is a directory and already exists rename the file to
    %s.renamed, else return the file_name

    :param file_name:
    :return file_name:
    """
    if os.path.isdir(file_name):
        return '%s.renamed' % file_name
    else:
        return file_name


def mkdir_p(path):
    """'mkdir -p' in Python

    Original Code came from :
    stackoverflow.com/questions/600268/mkdir-p-functionality-in-python
    :param path:
    """

    try:
        if not os.path.isdir(path):
            os.makedirs(path)
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise turbo.DirectoryFailure(
                'The path provided, "%s", is either occupied and can\'t be'
                ' used as a directory or the permissions will not allow you to'
                ' write to this location.' % path
            )


def set_unique_dirs(object_list, root_dir):
    """From an object list create a list of unique directories.

    :param object_list:
    :param root_dir:
    """

    unique_dirs = []
    for obj in object_list:
        if obj:
            full_path = jpath(root=root_dir, inode=obj.lstrip(os.sep))
            dir_path = os.path.dirname(full_path)
            unique_dirs.append(dir_path)
    return set(unique_dirs)


def get_sfile(ufile, source):
    """Return the source file

    :param ufile:
    :param source:
    :return file_name:
    """

    if turbo.ARGS.get('preserve_path'):
        return os.path.join(source, ufile).lstrip(os.sep)
    if os.path.isfile(source):
        return os.path.basename(source)
    elif source is '.':
        return os.getcwd()
    else:
        try:
            base, sfile = ufile.split(source)
            return os.sep.join(sfile.split(os.sep)[1:])
        except ValueError:
            report.reporter(
                msg='ValueError Error when unpacking - %s %s' % (ufile, source)
            )
            return None


def real_full_path(object):
    """Return a string with the real full path of an object.

    :param object:
    :return str:
    """

    return os.path.realpath(
        os.path.expanduser(
            object
        )
    )


def get_local_source():
    """Understand the Local Source and return it.

    :param turbo.ARGS:
    :return source:
    """

    local_path = real_full_path(turbo.ARGS.get('source'))
    if os.path.isdir(local_path):
        return local_path.rstrip(os.sep)
    else:
        return os.path.split(local_path)[0].rstrip(os.sep)


def restor_perms(local_file, headers):
    """Restore Permissions, UID, GID from metadata.

    :param local_file:
    :param headers:
    """

    # Restore Permissions.
    os.chmod(
        local_file,
        int(headers['x-object-meta-perms'], 8)
    )

    # Lookup user and group name and restore them.
    os.chown(
        local_file,
        pwd.getpwnam(headers['x-object-meta-owner']).pw_uid,
        grp.getgrnam(headers['x-object-meta-group']).gr_gid
    )
