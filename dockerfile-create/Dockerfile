FROM ubi7/ubi:7.7
MAINTAINER jim j_lee@gmx.co.uk
LABEL description="a custom apache container bsaed on UBI 7"
RUN yum install -y httpd && \
    yum clean all
RUN echo "Hello from Dockerfile" > /var/www/html/index.html
EXPOSE 80
CMD ["httpd", "-D", "FOREGROUND"]

