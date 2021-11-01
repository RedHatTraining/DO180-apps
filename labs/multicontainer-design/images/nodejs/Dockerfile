FROM    ubi7/ubi:7.7

MAINTAINER username <username@example.com>

ENV     NODEJS_VERSION=8.0 \
        HOME=/opt/app-root/src

# Setting tsflags=nodocs helps create a leaner container
# image, as documentation is not needed in the container.
RUN yum install -y --setopt=tsflags=nodocs rh-nodejs8 make && \
	yum clean all --noplugins -y && \
	mkdir -p /opt/app-root && \
  	groupadd -r appuser -f -g 1001 && \
  	useradd -u 1001 -r -g appuser -m -d ${HOME} -s /sbin/nologin \
            -c "Application User" appuser && \
  	chown -R appuser:appuser /opt/app-root && \
	chmod -R 755 /opt/app-root

ADD	./enable-rh-nodejs8.sh /etc/profile.d/

USER	appuser
WORKDIR	${HOME}

CMD	["echo", "You must create your own container from this one."]
