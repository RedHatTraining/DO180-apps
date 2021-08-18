#!/bin/sh

if [ -d "work" ]; then
  sudo rm -fr work
fi

echo "Create database volume..."
mkdir -p work/data
sudo chcon -Rt container_file_t work
podman unshare chown -R 27:27 work



# TODO Add podman run for mysql image here

sleep 9

# TODO Add podman run for todonodejs image here

