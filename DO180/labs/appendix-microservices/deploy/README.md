Each subfolder contains scripts and Dockerfiles to build the To Do List applicaiton containter image.

For each runtime, there are folders for the "combo" version of the application (no suffix), where the HTML5 front end is serverd by the same web server as the HTTP API back end, and "api" versions of the application (`_api` suffix) where the front end is served by an Apache httpd server running in a different container.

Each folder in turn contains linked and kuberntes subfolders. The first one contains scripts to start and stop all required containers, and connected them using the linked containers docker feature. The second one contains kubernetes resource definition files (`*.yaml`) and scripts to start all required pods and connect them using kubernetes services.

Also notice that, in the "api" versions of the application, the front end will connect to the back end using the FQDN `api.lab.example.com` so this host name should be defined in the developer workstation /etc/hosts pointing to 127.0.0.1. All containers/pods redirect the required ports from the container host and the vagrant box also redirects the same ports from the VM host but the developer has to edit its /etc/hosts file.

