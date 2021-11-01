#!/bin/bash

echo "Stopping and removing containers"
sudo podman stop todo
sudo podman stop mysql
sudo podman rm todo
sudo podman rm mysql

# if there was a problem with run.sh delete data dir so the database cab be re-initialized:
echo "Removing work directory"
sudo rm -rf work
