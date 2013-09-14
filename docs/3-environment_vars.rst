Turbolift, the Cloud Files Uploader
###################################
:date: 2013-09-05 09:51
:tags: rackspace, upload, mass, Cloud Files, files, api
:category: \*nix

Turbolift Files to Rackspace Cloud Files -Swift-
================================================

Environment Variables
---------------------

The Application can except Environment Variables for simpler authentication if you are commonly uploading files to the same user environment::

    # COMMON TURBOLIFT ENVS, THESE ARE THE BASIC REQUIREMENTS
    # =======================================================
    export OS_USERNAME=YOU_USERNAME
    export OS_API_KEY=SOME_RANDOM_SET_OF_THINGS
    export OS_RAX_AUTH=THE_NAME_OF_THE_TARGET_REGION


    # NOT REQUIRED FOR AUTH
    #export OS_PASSWORD=USED_FOR_PASSWORD_AUTH
    #export OS_TENANT=OPENSTACK_TENANT_NAME 
    #export OS_TOKEN=USED_FOR_TOKEN_AUTH
    #export OS_REGION_NAME=REGION_NAME
    #export OS_AUTH_URL=AUTH_URL_SET_IF_NEEDED

    # NOT REQUIRED OPTIONS
    #export TURBO_CONFIG=PATH_TO_CONFIG_FILE
    #export TURBO_LOGS=LOG_LOCATION
    #export TURBO_ERROR_RETRY=INT
    #export TURBO_CONCURRENCY=INT
    #export TURBO_QUIET=True|False
    #export TURBO_VERBOSE=True|False
    #export TURBO_DEBUG=True|False
    #export TURBO_INTERNAL=True|False


NOTE: that these variables are similar with the Openstack NOVA compute project's NOVA client environment variables. You'll may want to read more about the `Rackspace NOVA Client`_ which contains more information on these variables and the inner workings of The Rackspace Public Cloud.


.. _Rackspace NOVA Client: https://github.com/rackspace/rackspace-novaclient