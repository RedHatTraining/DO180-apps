#!/bin/sh

if [ -d "work" ]; then
  sudo rm -fr work
fi

echo "Create database volume..."
mkdir -p work/init work/data
cp db.sql work/init
sudo chcon -Rt container_file_t work
sudo chown -R 27:27 work

# TODO Add podman run for mysql image here
# Assign the container an IP from range defined the RFC 1918: 10.88.0.0/16


sleep 9

# TODO Add podman run for todonodejs image here

sudo podman run -d --name mysql -e MYSQL_DATABASE=items -e MYSQL_USER=user1 \
-e MYSQL_PASSWORD=mypa55 -e MYSQL_ROOT_PASSWORD=r00tpa55 \
-v $PWD/work/data:/var/lib/mysql/data \
-v $PWD/work/init:/var/lib/mysql/init -p 30306:3306 \
--ip 10.88.100.101 do180/mysql-57-rhel7

sleep 9

sudo podman run -d --name todoapi -e MYSQL_DATABASE=items -e MYSQL_USER=user1 \
-e MYSQL_PASSWORD=mypa55 -p 30080:30080 \
do180/todonodejs
