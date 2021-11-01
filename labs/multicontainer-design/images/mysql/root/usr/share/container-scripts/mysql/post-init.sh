#!/bin/bash

mysql_flags="-u root --socket=/tmp/mysql.sock"
admin_flags="--defaults-file=$MYSQL_DEFAULTS_FILE $mysql_flags"
DIRECTORY=/var/lib/mysql/init

if [ -d $DIRECTORY ]; then
        for F in `ls $DIRECTORY`; do
             if [ -n "${MYSQL_DATABASE-}" ]; then
                echo "Running init script: $DIRECTORY/$F"
                mysql $admin_flags $MYSQL_DATABASE < $DIRECTORY/$F
             fi
        done
fi

