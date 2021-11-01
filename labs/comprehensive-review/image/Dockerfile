FROM ubi7/ubi:7.7

MAINTAINER sandeepv <sandeev@sg.ibm.com>

ENV NEXUS_HOME="/opt/NEXUS" \
    NEXUS_VERSION="2.14.3-02"

ADD nexus-${NEXUS_VERSION}-bundle.tar.gz ${NEXUS_HOME}/  
COPY nexus-start.sh ${NEXUS_HOME}/

RUN yum install -y --setopt=tsflags=nodocs java-1.8.0-openjdk-devel && \
    yum clean all -y

RUN groupadd -r nexus -f -g 1001 && \
    useradd -u 1001 -r -g nexus -m -d ${NEXUS_HOME} \
        -s /sbin/nologin \
        -c "Nexus User" nexus

WORKDIR ${NEXUS_HOME}

RUN ln -s ${NEXUS_HOME}/nexus-${NEXUS_VERSION} ${NEXUS_HOME}/nexus2 && \
    chown -R nexus:nexus ${NEXUS_HOME} && \
    chmod -R 755 ${NEXUS_HOME}

USER nexus

VOLUME /opt/nexus/sonatype-work

CMD ["sh","-c","${NEXUS_HOME}/nexus-start.sh"]

