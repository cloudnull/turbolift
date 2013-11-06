Turbolift, the Cloud Files Uploader
###################################
:date: 2013-09-05 09:51
:tags: rackspace, upload, mass, Cloud Files, files, api
:category: \*nix

Turbolift Files to Rackspace Cloud Files -Swift-
================================================

Command Line Arguments
----------------------

Authentication Arguments:
~~~~~~~~~~~~~~~~~~~~~~~~~

  - ``os-apikey`` | APIKEY for the Cloud Account
  - ``os-password`` | Password for the Cloud Account
  - ``os-user`` | Username for the Cloud Account
  - ``os-tenant`` | Specify the users tenantID
  - ``os-token`` | Specify a token for TOKEN Authentication
  - ``os-region`` | Specify an Endpoint
  - ``os-rax-auth`` | Specify a Rackspace Cloud Auth-URL and Endpoint [ dfw, ord, lon, iad, syd, hkg ].
  - ``os-hp-auth`` | Specify an HP Cloud Auth-URL and Endpoint [ region-b.geo-1 ]. Notice that HP only have ONE Swift region at this time.
  - ``os-auth-url`` | Specify the Auth URL
  - ``os-version`` | Gives Version Number

  
Optional Arguments:
~~~~~~~~~~~~~~~~~~~

  - ``help`` | Show helpful information on the script and its available functions
  - ``preserve-path`` | Preserves the File Path when uploading to a container. Useful for pesudo directory structure.
  - ``internal`` | Use ServiceNet Endpoint for Cloud Files
  - ``error-retry`` | Allows for a retry integer to be set, Default is 5
  - ``cc`` | Operational Concurrency
  - ``service-type`` | Override the service type 
  - ``system-config`` | Allows Turbolift to use a config file for it's credentials.
  - ``quiet`` | Makes Turbolift Quiet
  - ``verbose`` | Shows Progress While Uploading
  - ``debug`` | Turn up verbosity to over 9000


Header Arguments:
~~~~~~~~~~~~~~~~~

  - ``base-headers`` | Allows for the use of custom headers as the base Header
  - ``container-headers`` | Allows for custom headers to be set on Container(s)
  - ``object-headers`` | Allows for custom headers to be set on Object(s)


Positional Arguments:
~~~~~~~~~~~~~~~~~~~~~

  - ``upload`` | Use the Upload Function for a local Source.
  - ``tsync`` | DEPRECATED, use ``upload --sync``
  - ``archive`` | Compress files or directories into a single archive. Multiple Source Directories can be added to a single Archive.
  - ``delete`` | Deletes all of the files that are found in a container, This will also delete the container by default.
  - ``download`` | Downloads all of the files in a container to a provided source. This also downloads all of the pesudo directories and its contents, while preserving the structure.
  - ``list`` | List all containers or objects in a container.
  - ``show`` | Information on a container or object in a container.
  - ``clone`` | Clone a container to another container to the same or different region.
  - ``cdn-command`` | Enable / Disable the CDN on a Container. Additional Headers can be set with this function.

All Positional arguments ALL have additional Help information. To see this additional help information, please use ``<THE_COMMAND> -h/--help``
