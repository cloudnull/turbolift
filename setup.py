#!/usr/bin/env python
# ==============================================================================
# Copyright [2013] [Kevin Carter]
# License Information :
# This software has no warranty, it is provided 'as is'. It is your
# responsibility to validate the behavior of the routines and its accuracy using
# the code provided. Consult the GNU General Public license for further details
# (see GNU General Public License).
# http://www.gnu.org/licenses/gpl.html
# ==============================================================================
import setuptools
import sys
import turbolift


if sys.version_info < (2, 6, 0):
    sys.stderr.write("Turbolift Presently requires Python 2.6.0 or greater \n")
    sys.exit('\nUpgrade python because you version of it is VERY deprecated\n')

with open('README') as r_file:
    long_description = r_file.read()

setuptools.setup(
    name='turbolift',
    version=turbolift.info.__VN__,
    author='Kevin Carter',
    author_email='kevin@bkintegration.com',
    description='OpenStack Swift -Cloud Files- Uploader',
    long_description=long_description,
    license='GNU General Public License v3 or later (GPLv3+)',
    packages=['turbolift',
              'turbolift.operations'],
    url='https://github.com/cloudnull/turbolift.git',
    install_requires=['argparse',
                      'datetime'],
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Information Technology',
        'Intended Audience :: System Administrators',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Topic :: Utilities',
        'Topic :: Software Development :: Libraries :: Python Modules'],
    entry_points={"console_scripts": ["turbolift = turbolift.executable:run_turbolift"]}
    )
