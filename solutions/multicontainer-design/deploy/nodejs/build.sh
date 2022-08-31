#!/bin/bash
echo "Preparing build folder"
rm -fr build
mkdir -p build
cp -ap nodejs-source/* build
rm build/*.sh

# image build complains if he cannot read the database folder even if not needed for building the image
sudo rm -rf {linked,kubernetes}/work

source /usr/local/etc/ocp4.config
podman build --layers=false -t do180/todonodejs --build-arg NEXUS_BASE_URL=${RHT_OCP4_NEXUS_SERVER} .