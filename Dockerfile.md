```
# dockerfile to build image for JBoss EAP 6.4

# start from rhel 7.2
FROM ubi8

# file author / maintainer
MAINTAINER "FirstName LastName" "emailaddress@gmail.com"

# update OS
RUN yum -y update && \
yum -y install sudo openssh-clients unzip java-1.8.0-openjdk-devel && \
yum clean all

# enabling sudo group
# enabling sudo over ssh
RUN echo '%wheel ALL=(ALL) NOPASSWD: ALL' >> /etc/sudoers && \
sed -i 's/.*requiretty$/Defaults !requiretty/' /etc/sudoers

# add a user for the application, with sudo permissions
RUN useradd -m jboss ; echo jboss: | chpasswd ; usermod -a -G wheel jboss

# create workdir
RUN mkdir -p /opt/jboss

WORKDIR /opt/jboss

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
ENTRYPOINT $JBOSS_HOME/bin/standalone.sh-c standalone-full-ha.xml
USER jboss

CMD /bin/bash

```
