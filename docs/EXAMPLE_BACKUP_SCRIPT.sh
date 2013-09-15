#!/usr/bin/env bash
# =============================================================================
# Copyright [2013] [Kevin Carter]
# License Information :
# This software has no warranty, it is provided 'as is'. It is your
# responsibility to validate the behavior of the routines and its accuracy
# using the code provided. Consult the GNU General Public license for further
# details (see GNU General Public License).
# http://www.gnu.org/licenses/gpl.html
# =============================================================================

APIKEY="<API-KEY>"
USERNAME="<USER-NAME>"
REGION="<BACKUP-REGION>"
AUTHURL="identity.api.rackspacecloud.com/v2.0"


# Space Separated list of places or objects you want backed up.
# Example: BACKUP_LIST="/home/kevin /etc/something /some/other/dir"
BACKUP_LIST=""


# THESE ARGUMENTS ARE NOT REQUIRED
# ================================

# OPTIONAL! Turbolift Arguments, see `turbolift -h` for more information.
OPTIONAL_ARGS=""

# OPTIONAL! Turbolift Additional Arguments, see `turbolift upload -h` for more information.
ADDITIONAL_ARGS="--sync"


# THIS IS THE PART YOU SHOULD NOT TOUCH UNLESS YOU KNOW WHAT YOU ARE DOING.
# =========================================================================

# Set Turbolift
TURBOLIFT="turbolift -u ${USERNAME} -a ${APIKEY} --os-auth-url ${AUTHURL} --os-region ${REGION} ${OPTIONAL_ARGS}"

# Backup Action
for BACKUP_DIR in ${BACKUP_LIST}
do
${TURBOLIFT} upload ${ADDITIONAL_ARGS} -s ${BACKUP_DIR} -c ${HOSTNAME}-$(echo ${BACKUP_DIR} | sed 's/\//\_/g') --sync 
sleep 5
done
