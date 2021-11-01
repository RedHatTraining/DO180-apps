#!/bin/bash

docker stop test-mysql
docker rm test-mysql
sleep 9
sudo rm -rf work
