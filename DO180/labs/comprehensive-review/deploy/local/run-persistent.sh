#!/bin/bash
if [ ! -d /tmp/docker/work ]; then
  mkdir -p /tmp/docker/work
  chcon -Rt container_file_t /tmp/docker/work
  podman unshare chown 1001:1001 /tmp/docker/work
fi

podman run -d -v /tmp/docker/work:/opt/nexus/sonatype-work -p 127.0.0.1:18081:8081 nexus