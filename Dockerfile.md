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

# set environment

# create JBoss console user

# configure JBoss
RUN echo "JAVA_OPTS=\"\$JAVA_OPTS -Djboss.bind.address=0.0.0.0 -Djboss.bind.address.management=0.0.0.0\"" >> $JBOSS_HOME/bin/standalone.conf

# set permission folder
RUN chown -R jboss:jboss /opt/jboss

# JBoss ports

# start JBoss
USER jboss

CMD /bin/bash
                                                                                                                                            45,1         底
```
