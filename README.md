# DO180-apps
DO180 Repository for Sample Applications  

Dockerfile:  
```
# install JBoss EAP 6.4.0
ADD jboss-eap-6.4.0.zip /opt/jboss/jboss-eap-6.4.0.zip
RUN unzip /opt/jboss/jboss-eap-6.4.0.zip
# set environment
ENV JBOSS_HOME /opt/jboss/jboss-eap-6.4
# create JBoss console user
RUN $JBOSS_HOME/bin/add-user.sh admin admin@2016 --silent
# configure JBoss
RUN echo "JAVA_OPTS=\"\$JAVA_OPTS -Djboss.bind.address=0.0.0.0 -Djboss.bind.address.management=0.0.0.0\"" >> $JBOSS_HOME/bin/standalone.conf

# set permission folder
RUN chown -R jboss:jboss /opt/jboss

# JBoss ports
EXPOSE 8080 9990 9999
# start JBoss
ENTRYPOINT $JBOSS_HOME/bin/standalone.sh -c standalone-full-ha.xml
```

sudo podman build -t jboss-eap .  
sudo podman run -d --name jboss-eap-app -p 8080:8080 -p 9990:9990 -p 9999:9999 localhost/jboss-eap  
  
sudo podman logs --tail=10 jboss-eap-app  
sudo podman stop jboss-eap-app  
sudo podman ps -a  
sudo podman rm jboss-eap-app  
  
sudo podman tag localhost/jboss-eap localhost/jboss-eap:6.4.v1  
sudo podman save -o localhost/jboss-eap.6.4.v1.tar localhost/jboss-eap:6.4.v1  
sudo podman images  
sudo podman tag localhost/jboss-eap:6.4.v1 docker.io/haiduc2023/jboss-eap:6.4.v1  
sudo podman push docker.io/haiduc2023/jboss-eap:6.4.v1  
  
sudo podman run -d --name mydb -v /home/student/local/mysql:/var/lib/mysql/data -p 30306:3306 -e MYSQL_ROOT_PASSWORD=password -e MYSQL_USER=user1 -e MYSQL_PASSWORD=password -e MYSQL_DATABASE=books registry.access.redhat.com/rhscl/mysql-57-rhel7  
gedit mysql.sh  
```
#!/bin/bash

sudo podman run -d --pod mypod --name mydb2 -e MYSQL_ROOT_PASSWORD=password -e MYSQL_USER=user1 -e MYSQL_PASSWORD=password -e MYSQL_DATABASE=books registry.access.redhat.com/rhscl/mysql-57-rhel7
```

oc new-app --name=mysql-app --docker-image=registry.access.redhat.com/rhscl/mysql-57-rhel7 -e MYSQL_USER=user -e MYSQL_PASSWORD=password -e MYSQL_DATABASE=books -l app=mydbapp --as-deployment-config  

oc expose svc mysql-app --hostname=mysaltestapptesturl.com  
oc cp mytestfile.txt mysql-app-1-clcqx:/tmp/  
oc logs mysql-app-1-clcqx  
oc get all  
oc rsh mysql-app-1-clcqx  

oc process -f mysql.yaml -p MYSQL_USER=user1 -p MYSQL_PASSWORD=password -p MYSQL_DATABASE=books | oc create -f -  

oc create -f mysql.yaml  
oc process mysql-persistent -p MYSQL_USER=user1 -p MYSQL_PASSWORD=password -p MYSQL_DATABASE=books | oc create -f -  
oc new-app --template=mysql-persistent -p MYSQL_USER=user1 -p MYSQL_PASSWORD=mypa55 -p MYSQL_DATABASE=testdb -p MYSQL_ROOT_PASSWORD=r00tpa55 -p VOLUME_CAPACITY=10Gi  

oc delete pods --all  
oc delete pods mysql-1-xxxxx  
# Create a new project with a display name and description
oc new-project web-team-dev --display-name="Web Team Development" --description="Development project for the web team."
