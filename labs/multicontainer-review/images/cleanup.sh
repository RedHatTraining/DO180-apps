#!/bin/bash

# Stops and deletes all containers

sudo podman stop $(sudo podman ps -qa) ; sudo podman rm $(sudo podman ps -qa)

