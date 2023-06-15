#!/bin/bash

rm -fr build
mkdir -p build
cp -ap /home/student/DO180/labs/appendix-microservices/apps/nodejs/* build
rm build/*.sh

cp run.sh build
chmod a+x build/run.sh
chmod -R a+rwX build

# podman build complains if he cannot read the database folder even if not needed for building the image
sudo rm -rf {linked,kubernetes}/work

source /usr/local/etc/ocp4.config
podman build -t do180/todonodejs .