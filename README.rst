Turbolift, the Cloud Files Uploader
###################################
:date: 2012-02-14 16:22
:tags: rackspace, upload, mass, Cloud Files, files, api
:category: \*nix

Turbolift Files to Rackspace Cloud Files
========================================

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
  * Upload a directory, recursively 
  * Upload a single file
  * Syncs a local directory with a Cloud Files Container
  * Compresses a Local Directory, then uploads it
  * Creates a Container if it does not already exist
  * Properly Encodes files upon upload

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
  If you are installing on a system that is not Running Python => 2.6 but < 3.0, please review the document `INSTALL_EMBED.rst`. This is a tested installation Turbolift on Ubuntu 8.04, which ships with Python 2.5. The guide is a simple walk through for compiling stand alone python and installing Turbolift in that stand alone installation. 

Python Modules Needed, for full operation :
  NOTE : All of the modules needed should be part of the "standard" Library as of Python 2.6.  The setup file will
  install the two needed dependencies which may not have made it onto your system.


Application Usage
-----------------

Here is the Basic Usage


.. code-block:: bash

    turbolift -u [CLOUD-USERNAME] -a [CLOUD-API-KEY] --os-auth-url [CLOUD-AUTH-URL] -r [DATACENTER-ENDPOINT] upload -s [PATH-TO-DIRECTORY] -c [CONTAINER-NAME]


Run ``turbolift -h`` for a full list of available flags and operations


Authentication Arguments:
~~~~~~~~~~~~~~~~~~~~~~~~~

  - ``os-user`` | Username for the Cloud Account
  - ``os-apikey`` | APIKEY for the Cloud Account
  - ``os-password`` | Password for the Cloud Account
  - ``os-region`` | Specify an Endpoint
  - ``os-auth-url`` | Specify the Auth URL
  - ``os-rax-auth`` | Specify a Rackspace Cloud Auth-URL and Endpoint [ dfw, ord, lon ].  At this time their is no ability for accounts to uploaded to both US and UK data centers.


Positional Arguments:
~~~~~~~~~~~~~~~~~~~~~

  - ``upload`` | Use the Upload Function for a local Source.
  - ``tsync`` | Use the TSync function for a local Source. This function Operates Similar to RSYNC; uploading files that are not found currently on Cloud Files. This function validates the md5 checksum on the local system against what is found in Cloud Files prior to upload and if the checksums are different the local file will be uploaded.
  - ``archive`` | Compress files or directories into a single archive. Multiple Source Directories can be added to a single Archive.
  - ``con-per-dir`` | Uploads everything from a given source creating a single Container per Directory. Not as fast as other methods for uploading.
  - ``delete`` | Deletes all of the files that are found in a container, This will also delete the container by default.
  - ``download`` | Downloads all of the files in a container to a provided source. This also downloads all of the pesudo directories and its contents, while preserving the structure. 


Appliction Flags can be passed to the program on the command line:
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

  - ``container`` | Cloud Files Container that we are uploading too. If the container is not already in your Cloud Files repository the container will be created.
  - ``source`` | Specify the Local Content to be uploaded.
  - ``no-cleanup`` | [OPTIONAL] [ARCHIVE ONLY] Used to keep the compressed Archive after Upload. The archive will be left in the Users Home Folder
  - ``tar-name`` | [OPTIONAL] [ARCHIVE ONLY] Name To Use for the Archive


Optional Arguments:
~~~~~~~~~~~~~~~~~~~

  - ``preserve-path`` | Preserves the File Path when uploading to a container. Useful for pesudo directory structure.
  - ``error-retry`` | Allows for a retry integer to be set, Default is 5
  - ``base-headers`` | Allows for the use of customer heads as the base Header
  - ``container-headers`` | Allows for Metadata to be set on Container(s)
  - ``object-headers`` | Allows for Metadata to be set on Object(s)
  - ``cc`` | Operational Concurrency
  - ``internal`` | Use ServiceNet Endpoint for Cloud Files
  - ``quiet`` | Makes Turbolift Quiet
  - ``system-config`` | Allows Turbolift to use a config file for it's credentials. The file MUST be set to permissions 400 or 600
  - ``verbose`` | Shows Progress While Uploading
  - ``debug`` | Turn up verbosity to over 9000
  - ``help`` | Show helpful information on the script and its available functions
  - ``version`` | Gives Version Number
  


CDN Arguments:
~~~~~~~~~~~~~~

  - ``cdn-enabled`` | Allows for container(s) to become CDN Enabled
  - ``cdn-ttl`` | Provides for the TTL, default it 72 hours
  - ``cdn-logs`` | Enables the Access Logs for the CDN Enabled Container, Default is False


Environment Variables
---------------------

Turbolift can be set to use a Configuration file for easy integration into an with an account or multiple accounts. If you use a configuration file you will need to set the following values, however any parsable input allowed in Turbolift can be used in the configuration file::

    [BasicConfiguration]
    os_user = Your_Username
    os_rax_auth = Your_RAX_DC
    os_apikey  = Your_API_Key


Environment Variables
---------------------

The Application can except Environment Variables for simpler authentication if you are commonly uploading files to the same user environment::

    export OS_USERNAME=your-username
    export OS_API_KEY=random-stuff
    export OS_PASSWORD=your-password
    export OS_AUTH_URL=optional.override.url.for.auth
    export OS_REGION_NAME=the-region-for-your-repository


NOTE: that these variables are compatible with the Openstack NOVA compute project's NOVA client.
You'll may want to read more about the `Rackspace NOVA Client`_


Systems Tested on
-----------------

The application has been tested on :
  * Debian 6
  * Ubuntu 10.04 - 12.04 
  * Mac OS X 10.8
  * CentOS[RHEL] 6


Bench Marks
-----------

To show the speed of the application here are some benchmarks on uploading 30,000 64K files to a single container.


Definitions and Information:
  * ``ServiceNet`` - is the internal network found on all Rackspace Cloud Servers. When Using ServiceNet Uploads are sent over the internal network interface to the Cloud Files repository found in the same Data Center. `You can NOT use ServiceNet to upload to a different Data Center.`
  * ``Public Network`` - Uploads sent over the general internet to a Cloud Files repository 
  * Total Size of all 30,000 files ``1875M``
  * Test performed on a Rackspace Cloud Server at the size 512MB

    * 20 Mbps Public interface
    * 40 Mbps Internal Interface


Command Used For Tests::

    time turbolift --cc 150 --os-rax-auth $location upload --source /tmp/uptest/ --container $location-Test-$num


**Note that the username and api authentication key have been exported into local environment variables**


Test Results Using ServiceNet :
  :Test 1:  7m25.459s
  :Test 2:  7m25.459s
  :Test 3:  7m26.990s
  :Avg Time: 7 Minutes, 25.9 Seconds


Test Results Using The Public Network :
  :Test 1: 14m43.879s
  :Test 2: 14m1.751s
  :Test 3: 13m37.173s
  :Avg Time: 13 Minutes, 9.95 Seconds

.. _Rackspace NOVA Client: https://github.com/rackspace/rackspace-novaclient

