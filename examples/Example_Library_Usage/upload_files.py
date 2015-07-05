# =============================================================================
# Copyright [2015] [Kevin Carter]
# License Information :
# This software has no warranty, it is provided 'as is'. It is your
# responsibility to validate the behavior of the routines and its accuracy
# using the code provided. Consult the GNU General Public license for further
# details (see GNU General Public License).
# http://www.gnu.org/licenses/gpl.html
# =============================================================================
import os

HOME = os.getenv('HOME')


# Set some default args
import turbolift
args = turbolift.ARGS = {
    'os_user': 'YOURUSERNAME',    # Username
    'os_apikey': 'YOURAPIKEY',    # API-Key
    'os_rax_auth': 'YOURREGION',  # RAX Region, must be UPPERCASE
    'error_retry': 5,             # Number of failure retries
    'source': '/tmp/files',       # local source for files to be uploaded
    'container': 'test9000',      # Name of the container
    'quiet': True,                # Make the application not print stdout
    'batch_size': 30000           # The number of jobs to do per cycle
}


# Load our Logger
from turbolift.logger import logger
log_method = logger.load_in(
    log_level='info',
    log_file='turbolift_library',
    log_location=HOME
)


# Load our constants
turbolift.load_constants(log_method, args)


# Authenticate against the swift API
from turbolift.authentication import auth
authentication = auth.authenticate()


# Package up the Payload
import turbolift.utils.http_utils as http
payload = http.prep_payload(
    auth=auth,
    container=args.get('container'),
    source=args.get('source'),
    args=args
)


# Load all of our available cloud actions
from turbolift.clouderator import actions
cf_actions = actions.CloudActions(payload=payload)


# Upload file(s)
# =============================================================================
import turbolift.utils.multi_utils as multi
from turbolift import methods

f_indexed = methods.get_local_files()   # Index all of the local files
num_files = len(f_indexed)              # counts the indexed files

kwargs = {
    'url': payload['url'],              # Defines the Upload URL
    'container': payload['c_name'],     # Sets the container
    'source': payload['source'],        # Defines the local source to upload
    'cf_job': cf_actions.object_putter  # sets the job
}

# Perform the upload job
multi.job_processer(
    num_jobs=num_files,
    objects=f_indexed,
    job_action=multi.doerator,
    concur=25,
    kwargs=kwargs
)
