#!/bin/bash
if curl -L --progress-bar -O https://download.sonatype.com/nexus/oss/nexus-2.14.3-02-bundle.tar.gz
then
  echo "Nexus bundle download successful"
else
  echo "Download failed"
fi
