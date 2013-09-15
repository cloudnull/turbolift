#!/usr/bin/env python
# =============================================================================
# Copyright [2013] [Kevin Carter]
# License Information :
# This software has no warranty, it is provided 'as is'. It is your
# responsibility to validate the behavior of the routines and its accuracy
# using the code provided. Consult the GNU General Public license for further
# details (see GNU General Public License).
# http://www.gnu.org/licenses/gpl.html
# =============================================================================
import os
import setuptools
import sys

from turbolift import info

REQUIRES = []

if sys.version_info < (2, 6, 0):
    sys.stderr.write("Turbolift Presently requires Python 2.6.0 or greater \n")
    sys.exit('\nUpgrade python because you version of it is VERY deprecated\n')
elif sys.version_info < (2, 7, 0):
    REQUIRES.append('argparse')

path = os.path.join(os.getcwd(), 'docs')
if os.path.exists(path):
    first = ['README']
    for doc in first + sorted(os.listdir(path)):
        if doc is 'README':
            fpath = doc
        else:
            fpath = os.path.join(path, doc)

        with open(fpath, 'rb') as docr:
            objr = docr.read()
        with open('README', 'ab') as readme:
            readme.write(objr)

with open('README', 'rb') as r_file:
    LDINFO = r_file.read()

setuptools.setup(
    name=info.__appname__,
    version=info.__version__,
    author=info.__author__,
    author_email=info.__email__,
    description=info.__description__,
    long_description=LDINFO,
    license='GNU General Public License v3 or later (GPLv3+)',
    packages=['turbolift',
              'turbolift.arguments',
              'turbolift.authentication',
              'turbolift.clouderator',
              'turbolift.logger',
              'turbolift.methods'],
    url=info.__url__,
    install_requires=REQUIRES,
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Information Technology',
        'Intended Audience :: System Administrators',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        ('License :: OSI Approved :: GNU General Public License v3 or later'
         ' (GPLv3+)'),
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Topic :: Utilities',
        'Topic :: Software Development :: Libraries :: Python Modules'],
    entry_points={
        "console_scripts": ["turbolift = turbolift.executable:run_turbolift"]}
)
