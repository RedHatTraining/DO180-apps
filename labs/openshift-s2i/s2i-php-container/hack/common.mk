SKIP_SQUASH?=0

build = hack/build.sh

ifeq ($(TARGET),rhel7)
	OS := rhel7
else
	OS := centos7
endif

script_env = \
	SKIP_SQUASH=$(SKIP_SQUASH)                      \
	UPDATE_BASE=$(UPDATE_BASE)                      \
	VERSIONS="$(VERSIONS)"                          \
	OS=$(OS)                                        \
	VERSION="$(VERSION)"                            \
	BASE_IMAGE_NAME=$(BASE_IMAGE_NAME)              \
	OPENSHIFT_NAMESPACES="$(OPENSHIFT_NAMESPACES)"

.PHONY: build
build:
	$(script_env) $(build)

.PHONY: test
test:
	$(script_env) TAG_ON_SUCCESS=$(TAG_ON_SUCCESS) TEST_MODE=true $(build)
