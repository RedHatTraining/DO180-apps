#!/bin/sh

DOCROOT=/opt/rh/httpd24/root/var/www/html/

sudo rm -rf $DOCROOT/todo
sudo cp -r src/ $DOCROOT/todo
sudo chmod -R a+rX $DOCROOT/todo

