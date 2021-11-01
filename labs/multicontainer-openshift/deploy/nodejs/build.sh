#!/bin/bash

echo "Preparing build folder"
rm -fr build
mkdir -p build
cp -ap nodejs-source/* build
rm build/*.sh
cp -p db.js build/models
chmod -R a+rwX build

source /usr/local/etc/ocp4.config
sudo podman build --layers=false -t do180/todonodejs --build-arg NEXUS_BASE_URL=${RHT_OCP4_NEXUS_SERVER} .
