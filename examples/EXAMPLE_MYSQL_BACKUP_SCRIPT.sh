#!/usr/bin/env bash
# =============================================================================
# Copyright [2015] [Kevin Carter]
# License Information :
# This software has no warranty, it is provided 'as is'. It is your
# responsibility to validate the behavior of the routines and its accuracy
# using the code provided. Consult the GNU General Public license for further
# details (see GNU General Public License).
# http://www.gnu.org/licenses/gpl.html
# =============================================================================

# Purpose:
# This script will backup all of the databases found in MySQL as individual
# databases. Once the backup is complete a tarball will be created of all
# databases which were found and dumped as ".sql" files.  Finally if
# Turbolift is installed and a settings file has been created containing
# your credentials the backed up databases will be saved in a cloudfiles
# container.

set -e

# Set .my.cnf variable
MYSQL_CRED_FILE="/root/.my.cnf"

# Set the database backup directory
BACKUP_LOCATION="/opt/backup/databases"

# Set the turbolift settings file
TURBOLIFT_CONFIG="/etc/turbolift.cfg"

export PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"

# Make sure mysql CLI clients are found.
if [ ! "$(which mysql)" ];then
  echo "mysql client not installed"
  exit 1
fi

# Make sure mysqldump CLI clients are found.
if [ ! "$(which mysqldump)" ];then
  echo "mysqldump client not installed"
  exit 1
fi

# Check if the my.cnf file exists
if [ ! -f "${MYSQL_CRED_FILE}" ];then
  echo "MySQL .my.cnf file was not found."
  exit 1
fi

# Check for backup directory
if [ ! -d "${BACKUP_LOCATION}" ];then
  mkdir -p ${BACKUP_LOCATION}
fi

# Get value from mysql file
function getcred(){
  grep "${1}" ${MYSQL_CRED_FILE} | awk -F'=' '{print $2}' | awk '{$1=$1}{ print }'
}

# Get a list of all of the databases
function getdatabases(){
  mysql --silent \
        --skip-column-names \
        -u"${MYSQL_USERNAME}" \
        -p"${MYSQL_PASSWORD}" \
        -e "show databases;" | grep -v "performance_schema"
}

MYSQL_USERNAME=$(getcred "user")
MYSQL_PASSWORD=$(getcred "password")
MYSQL_DATABASES=$(getdatabases)

# Backup the databases separately
for db in ${MYSQL_DATABASES};do
  mysqldump --events \
            --skip-lock-tables \
            -u"${MYSQL_USERNAME}" \
            -p"${MYSQL_PASSWORD}" \
            ${db} > ${BACKUP_LOCATION}/${db}.sql
done

# Compress all of the databases
tar -czf /tmp/database-tarball.tgz ${BACKUP_LOCATION} > /dev/null 2>&1
if [ -f "/tmp/database-tarball.tgz" ];then
  mv /tmp/database-tarball.tgz ${BACKUP_LOCATION}/database-tarball.tgz
fi

# Backup the databases which were just backed up
if [ "$(which turbolift)"  ];then
  if [ -f "${TURBOLIFT_CONFIG}" ];then
    turbolift --quiet \
              --system-config ${TURBOLIFT_CONFIG} \
              upload \
              -c backup-databases \
              -s "${BACKUP_LOCATION}"
  fi
fi


