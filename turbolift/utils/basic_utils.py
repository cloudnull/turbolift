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
import time

import turbolift as turbo
import turbolift.utils.report_utils as report


def time_stamp():
    """Setup time functions

    :return (fmt, date, date_delta, now):
    """

    # Time constants
    fmt = '%Y-%m-%dT%H:%M:%S.%f'
    date = datetime.datetime
    date_delta = datetime.timedelta
    now = datetime.datetime.utcnow()

    return fmt, date, date_delta, now


def json_encode(read):
    """Return a json encoded object.

    :param read:
    :return:
    """

    return json.loads(read)


def unique_list_dicts(dlist, key):
    """Return a list of dictionaries which have sorted for only unique entries.

    :param dlist:
    :param key:
    :return list:
    """

    return dict((val[key], val) for val in dlist).values()


def dict_pop_none(dictionary):
    """Parse all keys in a dictionary for Values that are None.

    :param dictionary: all parsed arguments
    :returns dict: all arguments which are not None.
    """

    return dict([(key, value) for key, value in dictionary.iteritems()
                 if value is not None if value is not False])


def keys2dict(chl):
    """Take a list of strings and turn it into dictionary.

    :param chl:
    :return {}|None:
    """

    if chl:
        return dict([_kv.split('=') for _kv in chl])
    else:
        return None


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
    import tempfile

    return tempfile.mktemp()


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
    if num_files > batch_size:
        ops = num_files / batch_size + 1
        report.reporter(
            msg='This will take "%s" operations to complete.' % ops,
            lvl='warn',
            log=True,
            prt=True
        )
    return batch_size


def batch_gen(data, batch_size, count):
    """This is a batch Generator which is used for large data sets.

    NOTE ORIGINAL CODE FROM: Paolo Bergantino
    http://stackoverflow.com/questions/760753/iterate-over-a-python-sequence\
    -in-multiples-of-n

    :param data:
    :param batch_size:
    :return list:
    """

    for dataset in range(0, count, batch_size):
        yield data[dataset:dataset + batch_size]


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
    :param source:
    """

    unique_dirs = []
    for obj in object_list:
        full_path = jpath(root=root_dir, inode=obj.lstrip(os.sep))
        dir_path = full_path.split(
            os.path.basename(full_path)
        )[0].rstrip(os.sep)
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
        base, sfile = ufile.split(source)
        return os.sep.join(sfile.split(os.sep)[1:])


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


def ustr(obj):
    """If an Object is unicode convert it.

    :param object:
    :return:
    """
    if obj is not None and isinstance(obj, unicode):
        return str(obj.encode('utf8'))
    else:
        return obj


def retryloop(attempts, timeout=None, delay=None, backoff=1, obj=None):
    """Enter the amount of retries you want to perform.

    The timeout allows the application to quit on "X".
    delay allows the loop to wait on fail. Useful for making REST calls.

    ACTIVE STATE retry loop
    http://code.activestate.com/recipes/578163-retry-loop/

    Example:
        Function for retring an action.
        for retry in retryloop(attempts=10, timeout=30, delay=1, backoff=1):
            something
            if somecondition:
                retry()

    :param attempts:
    :param timeout:
    :param delay:
    :param backoff:
    """

    starttime = time.time()
    success = set()
    for _ in range(attempts):
        success.add(True)
        yield success.clear
        if success:
            return
        duration = time.time() - starttime
        if timeout is not None and duration > timeout:
            break
        if delay:
            time.sleep(delay)
            delay = delay * backoff
    report.reporter(
        msg=('RetryError: FAILED TO PROCESS "%s" after "%s" Attempts'
             % (obj, attempts)),
        lvl='critical',
        log=True
    )


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


def stat_file(local_file):
    """Stat a file and return the Permissions, UID, GID.

    :param local_file:
    :return dict:
    """

    obj = os.stat(local_file)
    return {'X-Object-Meta-perms': oct(obj.st_mode)[-4:],
            'X-Object-Meta-owner': pwd.getpwuid(obj.st_uid).pw_name,
            'X-Object-Meta-group': grp.getgrgid(obj.st_gid).gr_name}


def stupid_hack(most=10, wait=None):
    """Return a random time between 1 - 10 Seconds."""

    # Stupid Hack For Public Cloud so it is not overwhelmed with API requests.
    if wait is not None:
        time.sleep(wait)
    else:
        time.sleep(random.randrange(1, most))


def match_filter(idx_list, pattern, dict_type=False, dict_key='name'):
    """Match items in indexed files.

    :param idx_list:
    :return list
    """

    if idx_list:
        if dict_type is False:
            return [obj for obj in idx_list
                    if re.search(pattern, obj)]
        elif dict_type is True:
            return [obj for obj in idx_list
                    if re.search(pattern, obj.get(dict_key))]
    else:
        return idx_list
