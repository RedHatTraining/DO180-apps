#!/bin/bash

sudo podman stop test-mysql
sudo podman rm test-mysql
sleep 9
sudo rm -rf work
