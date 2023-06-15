#!/bin/bash

# Stops and deletes all containers

docker stop $(docker ps -qa) ; docker rm $(docker ps -qa)

