#!/bin/sh
sudo rm -rf work

if [ ! -d "work" ]; then
  echo -n "• Creating database volume: "
  mkdir -p work/init work/data
  cp db.sql work/init
  podman unshare chown -R 27:27 work
else
  sudo rm -fr work/init
fi
echo "OK"

echo -n "• Launching database: "
podman run -d \
  --name mysql \
  -e MYSQL_DATABASE=items \
  -e MYSQL_USER=user1 \
  -e MYSQL_PASSWORD=mypa55 \
  -e MYSQL_ROOT_PASSWORD=r00tpa55 \
  -v $PWD/work/data:/var/lib/mysql/data:Z \
  -v $PWD/work/init:/var/lib/mysql/init:Z \
  -p 30306:3306 \
  registry.redhat.io/rhel8/mysql-80:1 &>/dev/null
echo "OK"

echo -n "• Importing database: "
until podman exec -it mysql bash -c "mysql -u root -e 'show databases;'" &>/dev/null; do
  sleep 2
done

podman exec mysql bash \
  -c "cat /var/lib/mysql/init/db.sql | mysql -u root items"
echo "OK"

echo -n "• Launching To Do application: "
podman run -d \
  --name todoapi \
  -p 30080:30080 \
  -e MYSQL_DATABASE=items \
  -e MYSQL_USER=user1 \
  -e MYSQL_PASSWORD=mypa55 \
  -e MYSQL_SERVICE_HOST="workstation.lab.example.com" \
  -e MYSQL_SERVICE_PORT=30306 \
  do180/todonodejs &>/dev/null

podman run -d \
  --name todo_frontend \
  -p 30000:8080 \
  do180/todo_frontend &>/dev/null
echo "OK"
