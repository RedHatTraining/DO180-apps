# DO180 MySQL 5.6 Docker Image

This image customizes the supported Red Hat SCL MySQL image.

The customization is mechanism that load every script file that is on the /var/lib/mysql/init folder to the database.

To build this image, use the following command:

sudo podman build -t do180/mysql-56-rhel7 .
