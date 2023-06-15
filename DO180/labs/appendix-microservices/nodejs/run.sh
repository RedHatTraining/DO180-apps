#!/bin/sh
network='do180-app-bridge'
sudo rm -rf work

if [ ! -d "work" ]; then
  echo -n "• Creating database volume: "
  mkdir -p work/init work/data
  cp db.sql work/init
  sudo chcon -Rt svirt_sandbox_file_t work
  sudo chown -R 27:27 work
else
  sudo rm -fr work/init
fi
echo "OK"

echo -n "• Creating sudo podman network: "
sudo podman network create --attachable ${network} &>/dev/null
echo "OK"

echo -n "• Launching database: "
sudo podman run -d \
  --name mysql \
  -e MYSQL_DATABASE=items \
  -e MYSQL_USER=user1 \
  -e MYSQL_PASSWORD=mypa55 \
  -e MYSQL_ROOT_PASSWORD=r00tpa55 \
  -v $PWD/work/data:/var/lib/mysql/data \
  -v $PWD/work/init:/var/lib/mysql/init \
  --network ${network} \
  -p 30306:3306 \
  do180/mysql-56-rhel7

echo -n "• Importing database: "
until sudo podman exec -it mysql bash -c "mysql -u root -e 'show databases;'" &>/dev/null; do
  sleep 2
done

sudo podman exec mysql bash \
  -c "cat /var/lib/mysql/init/db.sql | mysql -u root items"
echo "OK"

echo -n "• Launching To Do application: "
sudo podman run -d \
  --name todoapi \
  -p 30080:30080 \
  --network ${network} \
  do180/todoapi_nodejs

sudo podman run -d \
  --name todoui \
  -p 30000:80 \
  --network ${network} \
  do180/todo_frontend
