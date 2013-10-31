#!/usr/bin/env bash

#    Copyright (C) 2013 Alexandru Iacob
#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License along
#    with this program; if not, write to the Free Software Foundation, Inc.,
#    51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
######################################################################################################
set -o nounset
set -o pipefail    # if you fail on this line, get a newer version of BASH.
######################################################################################################
# IMPORTANT !!!
# check if we are the only running instance
#
PDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
LOCK_FILE=`basename $0`.lock

if [ -f "${LOCK_FILE}" ]; then
	# The file exists so read the PID
	# to see if it is still running
	MYPID=`head -n 1 "${LOCK_FILE}"`
 
	TEST_RUNNING=`ps -p ${MYPID} | grep ${MYPID}`
 
	if [ -z "${TEST_RUNNING}" ]; then
		# The process is not running
		# Echo current PID into lock file
		# echo "Not running"
		echo $$ > "${LOCK_FILE}"
	else
		echo "`basename $0` is already running [${MYPID}]"
    exit 0
	fi
else
	echo $$ > "${LOCK_FILE}"
fi
# make sure the LOCK_FILE is removed when we exit
trap "rm -f ${LOCK_FILE}" INT TERM EXIT

######################################################################################################
# 					Text color variables
bold=$(tput bold)             	# Bold
red=${bold}$(tput setaf 1) 		# Red
blue=${bold}$(tput setaf 4) 	# Blue
green=${bold}$(tput setaf 2) 	# Green
txtreset=$(tput sgr0)          	# Reset
######################################################################################################
#                 Checking availability of turbolift                  
which turbolift &> /dev/null

[ $? -ne 0 ]  && \
echo "" && \
echo "${red}Turbolift utility is not available ... Install it${txtreset}" &&  \
echo "" && \
echo "${green}Prerequisites :${txtreset}" && \
echo "For all the things to work right please make sure you have python-dev" && \
echo "All systems require the python-setuptools package." && \
echo "Python => 2.6 but < 3.0" && \
echo "A File or some Files you want uploaded" && \
echo "" && \
echo "${green}Installation :${txtreset}" && \
echo "git clone git://github.com/cloudnull/turbolift.git" && \
echo "cd turbolift" && \
echo "python setup.py install" && \
echo "" && \
echo "${red}Script terminated.${txtreset}" && \
exit 1
######################################################################################################
#	GLOBALS
SCRIPT_SOURCE="${BASH_SOURCE[0]}"
SCRIPT_DIR="$( cd -P "$( dirname "$SCRIPT_SOURCE" )" && pwd )"
SCRIPT_NAME="${0##*/}"
shopt -s globstar
_now=$(date +"%Y-%m-%d_%T")

# we will clean the obsolete files from the CDN container at specified time
# Store some timestamps for comparison.
declare -i _elapsed=$(date +%s)
# change below according to your needs
declare -i _clean_time=$(date -d "03:30:00 Saturday" +%s)

declare -r LOG_DIR="/var/log/cdn-sync"
declare -r log_file="$LOG_DIR/CDN-sync_$_now"
declare -r CDN_log_file="$LOG_DIR/CDN-log"  							
declare -r log_removed="$LOG_DIR/CDN-remove_$_now"						

# Some default values
CDN_ID=""                                                            # add your ID
CDN_KEY=""                              # add your API KEY
# Rackspace currently has five compute regions which may be used:
# dfw -> Dallas/Forth Worth
# ord -> Chicago
# syd -> Sydney
# lon -> London
# iad -> Northern Virginia
# Note: Currently the LON region is only avaiable with a UK account, and UK accounts cannot access other regions (check with Rackspace)
CDN_REGION=""                                                        # specify region
CDN_CONTAINER=""                                          # specify container name
SFTP_CONTAINER=""    # change this
SFTP_FILES="$LOG_DIR/sftp-files"                                        
######################################################################################################
#       Turbolift requires root privileges
ROOT_UID=0             # Root has $UID 0.
E_NOTROOT=101          # Not root user error. 

function check_if_root (){       # is root running the script?
                      
  if [ "$UID" -ne "$ROOT_UID" ]
  then
	echo ""
    echo "$(tput bold)${red}Ooops! Must be root to run this script.${txtreset}"
    echo ""
    #clear
    exit $E_NOTROOT
  fi
} 
######################################################################################################
#       Prepare LOG ENV
function make_log_env(){
	echo ""
	echo "Checking for LOG ENVIRONMENT in $(tput bold)${green}$LOG_DIR${txtreset}"
		if [ ! -d "$LOG_DIR" ]; then
			echo "$(tput bold)${red}LOG environment not present...${txtreset}" && \
			echo "${green}Creating log environment..."
			if [ `mkdir -p $LOG_DIR` ]; then
				echo "ERROR: $* (status $?)" 1>&2
				exit 1
			else
				# success
				echo "$(tput bold)${green}Success.${txtreset} Log environment created in ${green}$LOG_DIR${txtreset}"
				echo ""
				echo "Moving on...."
				echo ""
			fi
		else
			# success
			echo "$(tput bold)${green}OK.${txtreset} Log environment present in $(tput bold)${green}$LOG_DIR${txtreset}"
			echo ""
			echo "Moving on...."
			echo ""
		fi
}
######################################################################################################
function cdn_sync(){

	#	UPLOAD new files first
	turbolift -u $CDN_ID -a $CDN_KEY --os-rax-auth $CDN_REGION --verbose --colorized upload --sync -s $SFTP_CONTAINER -c $CDN_CONTAINER

	# LIST the files on CDN and save them 
	turbolift -u $CDN_ID -a $CDN_KEY --os-rax-auth $CDN_REGION list -c $CDN_CONTAINER > $log_file
cat >> $CDN_log_file <<EOF
${green}***********************************************************
***	CDN Files - $_now
***********************************************************${txtreset}
EOF

	cat $log_file >> $CDN_log_file	# keep the original CDN-log

	# LIST the current files present on SFTP
	# CDN -> we canot have containers inside containers.
	# BUT, users have the habit to upload full directories to SFTP, so we need to parse them.
	# on CDN, the files will have the full PATH as name.
	# we need to remove the first X chars from 'find' output where X -> lenght of SFTP_CONTAINER
	exclude_str=${#SFTP_CONTAINER}
	
	# now we have the lenght of SFTP_CONTAINER. 
	# we need to +1 - this will include an extra char for the trailing slash
	((exclude_str++))
	
	# now generate the LOG file for SFTP side;
	find $SFTP_CONTAINER -type f | sed  "s/^.\{$exclude_str\}//g" > $SFTP_FILES

	# format CDN file list
	tail -n +6 $log_file | head -n -3 > log_file-new && mv log_file-new $log_file
	sed -e 's/|\(.*\)|/\1/' $log_file > CDN-new && mv CDN-new $log_file
	awk -F'|' '{print $2}' $log_file > CDN-new && mv CDN-new $log_file

	# keep the files that are ONLY on CDN and NOT on SFTP in a separate list.
	# this files will be REMOVED
	fgrep -vf $SFTP_FILES $log_file > $log_removed
}
######################################################################################################
#       Clean the obsolete files from the CDN container
#		this function will ONLY run only at specific time.
#		Check lines 63-66 to change the values
function remove_obsolete_files(){
	if [[ $_clean_time -lt $_elapsed ]]; then
		echo "Cleaning up CDN Container ... "
		while read line
		do
			deleted_file=$line
			echo "Removing obsolete file - $deleted_file"
			turbolift -u $CDN_ID -a $CDN_KEY --os-rax-auth $CDN_REGION --verbose --colorized delete --container $CDN_CONTAINER --object $deleted_file
		done < $log_removed
	fi	
}
######################################################################################################
#       Clean-up. Unset variables
function unset_vars(){
		unset CDN_ID
		unset CDN_KEY
		unset CDN_REGION
		unset CDN_CONTAINER
		unset SFTP_CONTAINER
		unset SFTP_FILES
		unset _elapsed
}
######################################################################################################
#       Remove OLD log-files
function clean_logs(){
	# run rm only once at the end instead of each time a file is found.
	echo "" && \
	echo "${green}Cleaning $1...${txtreset}Removing files older than 3 days..." && \
	echo ""
	if [ `find $1 -type f -mtime +3 -exec rm '{}' '+'` ]; then
		echo "ERROR: $* (status $?)" 1>&2
		exit 1
	else
		echo "Done."
	fi
}
######################################################################################################
main() {
	
	check_if_root
	make_log_env
	cdn_sync
	
	# Remove obsolete files from the CDN container - ONLY if the time is right :)
	remove_obsolete_files
	
	# Clean up
	clean_logs "$LOG_DIR"
	unset_vars

	# remove lock
	rm -f ${LOCK_FILE}
	exit 0
}
main "$@"
