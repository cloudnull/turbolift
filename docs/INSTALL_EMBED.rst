Install Python Source and Turbolift
###################################
:date: 2012-02-14 16:22
:tags: rackspace, upload, mass, Cloud Files, files, api
:category: \*nix


Installing Dependencies
^^^^^^^^^^^^^^^^^^^^^^^

**To install Python 2.6/2.7 on a system that does not have it, you will need the following.**

* build-essential
* git-core
* curl
* openssl
* libssl-dev

*Overview*:
  You must have root (sudo) access to your system and or the ability to locally compile. You need to have GCC and make, which will be used to compile python. You will also need to have git, openssl and the ssl development files installed on your system.


Note:
  I tested this installation on Ubuntu 8.04LTS which was shipped with Python 2.5. Here is the Ubuntu ISO I used : http://old-releases.ubuntu.com/releases/hardy/


Here is the command that I ran to get the needed system dependencies in Ubuntu 8.04

.. code-block:: bash

    apt-get update && apt-get install build-essential git-core curl openssl libssl-dev


Installing Python2.7
^^^^^^^^^^^^^^^^^^^^

Information based on http://docs.python.org/2/using/unix.html#getting-and-installing-the-latest-version-of-python

.. code-block:: bash

    # go to temp dir 
    cd /tmp
     
    # Get the source 
    wget http://python.org/ftp/python/2.7.5/Python-2.7.5.tgz
     
    # uncompress and go to directory
    tar -xzf Python-2.7.5.tgz
    cd Python-2.7.5
     
    # Configure the build with a prefix (install dir) of /opt/python27, compile, and install.
    ./configure --prefix=/opt/python27
    make
    make install
     
    # now go to your new installation of python and test.
    /opt/python27/bin/python -V


You are going to need the package `setuptools` as well, so we might as well install that now. Information found here https://pypi.python.org/pypi/setuptools/0.8#installation-instructions

.. code-block:: bash

    # Install setuptools python module
    wget --no-check-certificate https://bitbucket.org/pypa/setuptools/raw/0.8/ez_setup.py -O - | /opt/python27/bin/python


Installing Turbolift
^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

    # Information based on https://github.com/cloudnull/turbolift
     
    # Get the source
    git clone git://github.com/cloudnull/turbolift.git
     
    # go to the turbolift directory
    cd turbolift
     
    # Install turbolift with the new version of Python
    /opt/python27/bin/python setup.py install


Your path to the turbolift application will be `/opt/python27/bin/turbolift`


Done. That was easy
^^^^^^^^^^^^^^^^^^^

I recommend that you add the new installation of Python to your local Path, however this is not required. 

.. code-block:: bash

    # to make the application more accessible, add /opt/python27/bin to your PATH.
    echo 'PATH=$PATH:/opt/python27/bin' >> $HOME/.bashrc

