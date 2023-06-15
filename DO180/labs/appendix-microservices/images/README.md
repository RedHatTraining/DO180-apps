# DO180 Base images for the frameworks

The folders contain the Dockerfiles to create the base images for all
the language/frameworks used in the solution.

Each folder contains a `build.sh` script to build the container image and a `test.sh` script to test the image, sometimes by creating a derived image.

Child images (application images) should copy their sources to a build folder at the same level as the child Dockerfile.

