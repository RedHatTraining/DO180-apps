#!/bin/bash

echo "Stopping and removing containers"
podman stop todo
podman stop mysql
podman rm todo
podman rm mysql

# if there was a problem with run.sh delete data dir so the database cab be re-initialized:
echo "Removing work directory"
sudo rm -rf work
