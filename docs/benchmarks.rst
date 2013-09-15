Turbolift, the Cloud Files Uploader
###################################
:date: 2013-09-05 09:51
:tags: rackspace, upload, mass, Cloud Files, files, api
:category: \*nix

Turbolift Files to Rackspace Cloud Files -Swift-
================================================

Bench Marks
-----------

To show the speed of the application here are some benchmarks on uploading 30,000 64K files to a single container.


Definitions and Information:
  * ``ServiceNet`` - is the internal network found on all Rackspace Cloud Servers. When Using ServiceNet Uploads are sent over the internal network interface to the Cloud Files repository found in the same Data Center. `You can NOT use ServiceNet to upload to a different Data Center.`
  * ``Public Network`` - Uploads sent over the general Internet to a Cloud Files repository 
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
  


