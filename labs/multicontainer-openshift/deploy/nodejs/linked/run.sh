#!/bin/sh
if [ ! -d "work" ]; then
  echo "Create database volume..."

  mkdir -p work/init work/data
  cp db.sql work/init
  sudo chcon -Rt svirt_sandbox_file_t work
  sudo chown -R 27:27 work
else
  sudo rm -fr work/init
fi

# TODO Add docker run for mysql image here

sleep 9

# TODO Add docker run for todonodejs image here

sleep 9
