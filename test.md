1

Edit the Docker file in path /home/openshift ex180 practice/EX180 as instructed below and build an image with name iboss-eap  
Copy the file /home/openshift_ex180 _ practice/jboss-eap-6.4.0 .zip from host to container image path /opt/jboss/. Unzip the copied file.  

﻿﻿Set ENV for BOSS HOME to /opt/jboss/jboss-eap-6.4  
﻿﻿Create EAP user using $JBOSS_HOME/bin/add-user.sh admin admin@2016 --silent  
﻿﻿Expose ports 8080,9990 and 9999  
﻿﻿Start JBOSS using $JBOSS_HOME/bin/standalone.sh-c standalone-full-ha.xml  



2

RUN container and use the image jboss-eap build in previous section.  
Expose ports 8080 ,9990 and 9999 of containers to local host ports 8080,9990 and 9999 respectively.  
Set name of the container as "jboss-eap-app"  
  


3

Get last 10 lines of logs for container jboss-eap-app  
Stop the container boss-eap-app  
Remove the container jboss-eap-app  



4

Add a tag "6.4.v1" to the image jboss-eap (Build in Test 1)  
Save the image with new tag to tar file jboss-eap.6.4.v1.tar  
Push the image with new tag "6.4.v1 to docker registry  


5


Run myg| container using Podman and image registry.access.redhat.com/rhscl/mysql-57-rhel7  
Name of the container mydb  
Expose container port 3306 to port 30306 on local h  
Pass the container parameter values  
MYSQL_ROOT_PASSWORD=password  
MYSQL_USER=user1  
MYSQL_PASSWORD=password  
MYSQL_DATABASE=books  

6

Create an mysql application as instructed below  
Name of the app is mysql-app  

Use image registry.access.redhat.com/rhscl/mysql-57-rhel7  

Parameters to be  
used MYSQL_USER=user MYSQL_PASSWORD=password MYSQL_DATABASE=books  
All resources should have label "app=mydbapp"  

7

Expose the service to url "mysaltestapptesturl.com"  
Copy file mytestfile. txt from host to the mysql application path /tmp/  
Check pod logs  
Login into application and check the version of mysq|  

8

Create mysql application as instructed below  
Use mysql.son or mysql.yaml for application creation　　  
Variable to be set　　  
MYSQL_USER=user1 MYSQL_PASSWORD=password MYSQL_DATABASE=books　　  

9

Create Template from mysql. json or mysql. yaml file　　  
Create mysql application as instructed below　　  
	• ﻿Use the template created　　  
	• ﻿Variable to be set　　  
MYSQL_USER=user1 MYSQL_PASSWORD=password MYSQL_DATABASE=books　　  

