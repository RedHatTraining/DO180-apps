#!/bin/bash

# if there was a problem with run.sh delete data dir so the database cab be re-initialized:
# rm -rf data

docker stop todo
docker stop mysql
docker rm todo
docker rm mysql
