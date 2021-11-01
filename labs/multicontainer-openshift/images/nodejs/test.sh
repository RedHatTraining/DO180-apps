#!/bin/bash -x

cd test
docker build -t do180/test-nodejs .
docker run -d --name test-nodejs -p 30080:3000 do180/test-nodejs
sleep 3
# Expected result is "Hello there" no HTML formatting
curl http://127.0.0.1:30080/hi
echo
docker stop test-nodejs
docker rm test-nodejs
