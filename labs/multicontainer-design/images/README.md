# DO180 Base images for the frameworks

The folders contain the Dockerfiles to create the base images for all
the language/frameworks used in the solution.

Each folder may contain a `build.sh` script to build the container image. Otherwise, instructions for building the image are present in the student guide.

Child images (application images) should copy their sources to a build folder at the same level as the child Dockerfile.
