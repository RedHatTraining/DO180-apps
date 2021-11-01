PHP Docker images
=================

This repository contains the source for building various versions of
the PHP application as a reproducible Docker image using
[source-to-image](https://github.com/openshift/source-to-image).
Users can choose between RHEL and CentOS based builder images.
The resulting image can be run using [Docker](http://docker.io).

For more information about using these images with OpenShift, please see the
official [OpenShift Documentation](https://docs.openshift.org/latest/using_images/s2i_images/php.html).

Versions
---------------
PHP versions currently supported are:
* php-5.6
* php-7.0

RHEL versions currently supported are:
* RHEL7

CentOS versions currently supported are:
* CentOS7


Installation
---------------
To build a PHP image, choose either the CentOS or RHEL based image:
*  **RHEL based image**

    To build a RHEL based PHP image, you need to run the build on a properly
    subscribed RHEL machine.

    ```
    $ git clone https://github.com/sclorg/s2i-php-container.git
    $ cd s2i-php-container
    $ make build TARGET=rhel7 VERSION=7.0
    ```

*  **CentOS based image**
    ```
    $ git clone https://github.com/sclorg/s2i-php-container.git
    $ cd s2i-php-container
    $ make build TARGET=centos7 VERSION=7.0
    ```

Alternatively, you can pull the CentOS image from Docker Hub via:

    $ docker pull centos/php-70-centos7

**Notice: By omitting the `VERSION` parameter, the build/test action will be performed
on all the supported versions of PHP.**


Usage
---------------------------------

For information about usage of Dockerfile for PHP 7.0,
see [usage documentation](7.0/README.md).

For information about usage of Dockerfile for PHP 5.6,
see [usage documentation](5.6/README.md).

Test
---------------------
This repository also provides a [S2I](https://github.com/openshift/source-to-image) test framework,
which launches tests to check functionality of a simple PHP application built on top of the s2i-php image.

Users can choose between testing a PHP test application based on a RHEL or CentOS image.

*  **RHEL based image**

    This image is not available as a trusted build in [Docker Index](https://index.docker.io).

    To test a RHEL7 based PHP-5.5 image, you need to run the test on a properly
    subscribed RHEL machine.

    ```
    $ cd s2i-php-container
    $ make test TARGET=rhel7 VERSION=7.0
    ```

*  **CentOS based image**

    ```
    $ cd s2i-php-container
    $ make test TARGET=centos7 VERSION=7.0
    ```

**Notice: By omitting the `VERSION` parameter, the build/test action will be performed
on all the supported versions of PHP.**


Repository organization
------------------------
* **`<php-version>`**

    Dockerfile and scripts to build container images from.

* **`hack/`**

    Folder containing scripts which are responsible for the build and test actions performed by the `Makefile`.

Image name structure
------------------------

1. Platform name (lowercase) - php
2. Platform version(without dots) - 70
3. Base builder image - centos7/rhel7

Examples: `php-70-centos7`, `php-70-rhel7`

