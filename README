Turbolift, the Cloud Files Uploader
###################################
:date: 2013-09-05 09:51
:tags: rackspace, upload, mass, Cloud Files, files, api
:category: \*nix

Turbolift Files to Rackspace Cloud Files -Swift-
================================================

General Overview
----------------

If you have found yourself in a situation where you needed or wanted to upload a whole bunch of files to Cloud Files
quickly, this is what you are looking for. Turbolift is an assistant for uploading files to the the Rackspace Cloud
Files Repository with a bunch of options.

You'll also probably want to read `The Rackspace Cloud Files API guide`__ (PDF) :
The guide will provide you an overview of all of the available functions for Cloud Files.

__ http://docs.rackspace.com/files/api/v1/cf-devguide/cf-devguide-latest.pdf

The Process by which this application works is simple. All you have to do is Literally fill in the command line
arguments and press enter. The application is a multiprocessing Cloud Files Uploader which will upload any directory
or file provided to it.

Functions of the Application :
  * Upload a directory, (recursively)
  * Upload a single file
  * Upload a local directory (recursively) and sync it with a Cloud Files Container
  * Download a Container to a local directory
  * Download changed objects from a Container to a local directory 
  * Compresses a Local Directory, then uploads it
  * List all Containers
  * List all Objects in a Container
  * Delete an Object in a Container
  * Delete an entire Container
  * Clone one Container in one region to another Container in the same or Different Region.
  * Set Custom headers on Objects/Containers


Turbolift can be managed with a config file. The option ``--system-config`` references a config file.
Additionally, the Environment Variable ``TURBO_CONFIG`` can be used to reference a config file as well.
All of Turbolift's options can be set in the config file. This makes managing Turbolift very simple.

Please read `command_line_args`_ for more information on Command Line Arguments and functions.


If you would like to setup Turbolift to use an environment variable file I would recommend you have a look at the `turboliftrc_example`_ file and the `environment_vars`_ document.


Please also review the `Turbolift Wiki`_ for more information.


Prerequisites :
  * For all the things to work right please make sure you have ``python-dev``.
  * All systems require the ``python-setuptools`` package.
  * Python => 2.6 but < 3.0
  * A File or some Files you want uploaded

Installation :
  Installation is simple::

    git clone git://github.com/cloudnull/turbolift.git
    cd turbolift
    python setup.py install

Installation NOTICE :
  If you are installing on a system that is not Running Python => 2.6 but < 3.0, please review the document `INSTALL_EMBED`_. This is a tested installation of Turbolift on Ubuntu 8.04, which ships with Python 2.5. The guide is a simple walk through for compiling stand alone python and installing Turbolift in that stand alone installation.

Python Modules Needed, for full operation :
  NOTE : All of the modules needed should be part of the "standard" Library as of Python 2.6.  The setup file will
  install the two needed dependencies which may not have made it onto your system.


Application Usage
-----------------

Here is the Basic Usage


.. code-block:: bash

    turbolift -u [CLOUD-USERNAME] -a [CLOUD-API-KEY] --os-rax-auth [REGION] upload -s [PATH-TO-DIRECTORY] -c [CONTAINER-NAME]


Run ``turbolift -h`` for a full list of available flags and operations


Turbolift can easily be set to run on via script or as a CRON job, please see, `turbolift_example_script`_ for more ideas / information on using Turbolift as a script.


Systems Tested on
-----------------

The application has been tested on :
  * Debian 6
  * Ubuntu 10.04 - 12.04 
  * Mac OS X 10.8
  * CentOS[RHEL] 6


For information on Benchmarks from my own testing, please have a look here at the `benchmarks`_ file.


Turbolift is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation. The License in service for this program is GPLv3. please see http://www.gnu.org/licenses/gpl-3.0.txt for more information.


.. _INSTALL_EMBED: https://github.com/cloudnull/turbolift/wiki/Install-Embed-Ubuntu
.. _command_line_args: https://github.com/cloudnull/turbolift/wiki/Command-Line-Args
.. _environment_vars: https://github.com/cloudnull/turbolift/wiki/Environment-Vars
.. _benchmarks: https://github.com/cloudnull/turbolift/wiki/Benchmarks
.. _turboliftrc_example: https://github.com/cloudnull/turbolift/wiki/Turbolift.rc-Example
.. _turbolift_example_script: https://github.com/cloudnull/turbolift/wiki/Example-Script
.. _Turbolift Wiki: https://github.com/cloudnull/turbolift/wiki
