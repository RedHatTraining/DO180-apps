FROM	do180/nodejs
ARG NEXUS_BASE_URL
MAINTAINER username <username@example.com>

COPY run.sh build ${HOME}/
RUN scl enable rh-nodejs8 'npm install --registry=http://$NEXUS_BASE_URL/repository/nodejs/'
EXPOSE	30080

CMD	["scl","enable","rh-nodejs8","./run.sh"]
