#!/usr/bin/env python

# - title        : Upload for Swift(Rackspace Cloud Files)
# - description  : Want to upload a bunch files to cloud files? This will do it.
# - License      : GPLv3+
# - author       : Kevin Carter
# - date         : 2011-11-09
# - notes        : This is a Swift(Rackspace Cloud Files) Upload Script
# - Python       : >= 2.6

"""
License Inforamtion

This software has no warranty, it is provided 'as is'. It is your
responsibility to validate the behavior of the routines and its
accuracy using the code provided. Consult the GNU General Public
license for further details (see GNU General Public License).

http://www.gnu.org/licenses/gpl.html
"""

import os
import setuptools
import sys
import turbolift
from turbolift import info


if sys.version_info < (2, 6, 0):
    sys.stderr.write("Turbolift Presently requires Python 2.6.0 or greater \n")
    sys.exit('\nUpgrade python because you version of it is VERY deprecated\n')


TM = ['argparse', 'datetime']


setuptools.setup(
    name='turbolift',
    version=turbolift.info.VN,
    author='Kevin Carter',
    author_email='kevin@bkintegration.com',
    description='OpenStack Swift -Cloud Files- Uploader'
        ,
    long_description=open(os.path.realpath('README.rst')).read(),
    license='GPLv3',
    packages=['turbolift'],
    url='https://github.com/cloudnull/turbolift.git',
    install_requires=TM,
    classifiers=[
              "Development Status :: Stable",
              "Intended Audience :: Devlopers and Users",
              "Intended Audience :: Information Technology",
              "License :: GPLv3",
              "Operating System :: OS Independent",
              "Programming Language :: Python",
              ],
    entry_points={
                 "console_scripts" :
                 ["turbolift = turbolift.executable:run_turbolift"]
                 }
                 )
