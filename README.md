# DO180-apps
DO180 Repository for Sample Applications  

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
sudo podman run -d --name mydb -p 30306:3306 -e MYSQL_ROOT_PASSWORD=password -e MYSQL_USER=user1 -e MYSQL_PASSWORD=password -e MYSQL_DATABASE=books registry.access.redhat.com/rhscl/mysql-57-rhel7  
gedit mysql.sh  
sudo podman run -d --pod mypod --name mydb -p 30306:3306 -e MYSQL_ROOT_PASSWORD=password -e MYSQL_USER=user1 -e MYSQL_PASSWORD=password -e MYSQL_DATABASE=books registry.access.redhat.com/rhscl/mysql-57-rhel7  
