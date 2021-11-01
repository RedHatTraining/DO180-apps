#!/bin/bash -x

sudo rm -rf data init
mkdir -p work/data work/init
cp -p test/testdata.sql work/init
sudo chcon -Rt container_file_t work
sudo chown -R 27:27 work

sudo podman run -d --name test-mysql -p 30306:3306 \
 -e MYSQL_USER=testuser -e MYSQL_PASSWORD=secret -e MYSQL_DATABASE=contacts \
 -v $PWD/work/data:/var/lib/mysql/data \
 -v $PWD/work/init:/var/lib/mysql/init \
 do180/mysql-56-rhel7
sleep 9
source  /opt/rh/mysql56/enable
# Expected result is single table named "contacts"
mysqlshow -P30306 -h127.0.0.1 -utestuser -psecret contacts
# Expected result is single row for "John Doe"
mysql -P30306 -h127.0.0.1 -utestuser -psecret  contacts < test/query.sql
# Expected result is ibdata and ib_logfile* files under data
ls work/data
# Expected result is contacts.frm and db.opt files
sudo ls work/data/contacts
