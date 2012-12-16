Turbolift, the Cloud Files Uploader
###################################
:date: 2012-12-16 16:22
:tags: rackspace, upload, mass, Cloud Files, files, api
:category: linux 

Turbolift Files to Rackspace Cloud Files
========================================

General Overview
----------------

If you have found yourself in a situation where you needed or wanted to upload a whole bunch of files to Cloud Files quickly, this is what you are looking for. Turbolift is an assistant for uploading files to the the Rackspace Cloud Files Repository with a bunch of options.

You'll also probably want to read `Rackspace's Cloud Files API guide`__ (PDF) :
The guide will provide you an overview of all of the available functions for Cloud Files.

__ http://docs.rackspace.com/files/api/v1/cf-devguide/cf-devguide-latest.pdf

The Process by which this application works is simple. All you have to do is Literally fill in the command line arguments and press enter. The application is a multiprocessing Cloud Files Uploader which will upload any directory or file provided to it.

Functions of the Application :
  * Upload a directory, recursively 
  * Upload a single file
  * Syncs a local directory with a Cloud Files Container
  * Compresses a Local Directory, then uploads it
  * Creates a Container if it does not already exist
  * Properly Encodes files upon upload

Prerequisites :
  * Python => 2.6 but < 3.0
  * A File or some Files you want uploaded

Installation :
  Installation is simple::

    git clone git://github.com/cloudnull/turbolift.git
    cd turbolift
    python setup.py install



Python Modules Needed, for full operation :
  NOTE : All of the modules needed should be part of the "standard" Library as of Python 2.6.  The setup file will install the two needed dependencies which may not have made it onto your system.


Application Usage
-----------------

Here is the Basic Usage::

    turbolift -u [CLOUD-USERNAME] -a [CLOUD-API-KEY] -e [DATACENTER-ENDPOINT] [POSITIONAL-ARGUMENT] -s [PATH-TO-DIRECTORY] -c [CONTAINER-NAME]

Run ``turbolift -h`` for a full list of available flags and operations


Authentication Arguments:
  :user: Username for the Cloud Account
  :apikey: APIKEY for the Cloud Account
  :password: Password for the Cloud Account
  :region: Specify the Swift Endpoint
  :url: [OPTIONAL] Sets an Override for the Auth URL
  :rax-auth: Specify the Rackspace Cloud Endpoint [ dfw, ord, lon ].  At this time their is no ability for accounts to uploaded to both US and UK data centers.


Positional Arguments:
  :upload: Use the Upload Function for a provided Source.
  :tsync: Use the TSync function for a local source to Cloud Files. This function Operates Similar to RSYNC uploading files that are not found currently on Cloud Files. This function validates the md5 checksum on the local system against what is found in Cloud Files prior to upload and if the checksums are different the local file will be uploaded.


Appliction Flags can be passed to the program on the command line:
  :container: Cloud Files Container that we are uploading too. If the container is not already in your Cloud Files repository the container will be created.
  :source: Specify the Local Content to be uploaded.
  :compress: [OPTIONAL] Compress a file or directory into a single archive


Optional Arguments:
  :cc: [OPTIONAL] File Upload Concurrency
  :internal: [OPTIONAL] Use ServiceNet Endpoint for Cloud Files
  :progress: [OPTIONAL] Shows Progress While Uploading
  :debug: [OPTIONAL] Turn up verbosity to over 9000
  :help: Show helpful information on the script and its available functions
  :version: Gives Version Number



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

To show the speed of the application here are some benchmarks on uploading 15,000 64K files to a single container.

Definitions:
  * ``ServiceNet`` - is the internal network found on all Rackspace Cloud Servers. When Using ServiceNet Uploads are sent over the internal network interface to the Cloud Files repository found in the same Data Center. `You can NOT use ServiceNet to upload to a different Data Center.`
  * ``Public Network`` - Uploads sent over the general internet to a Cloud Files repository 

Total Size of all 30,000 files ``1875M``

Using ServiceNet :
  :Test 1:  7m25.459s
  :Test 2:  7m25.459s
  :Test 3:  7m26.990s
  :Avg Time: 7 Minutes, 25.9 Seconds

Using The Public Network :
  :Test 1: 14m43.879s
  :Test 2: 14m1.751s
  :Test 3: 13m37.173s
  :Avg Time: 13 Minutes, 9.95 Seconds

.. _Rackspace NOVA Client: https://github.com/rackspace/rackspace-novaclient
