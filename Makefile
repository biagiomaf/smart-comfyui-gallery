ifneq (,$(wildcard .env))
	include .env
	export $(shell sed -n 's/^\([A-Za-z_][A-Za-z0-9_]*\)=.*/\1/p' .env)
endif

.PHONY: all build_main build_exp build_core run kill buildx_rm docker_tag docker_push

SMARTGALLERY_VERSION = 1.55

DOCKERFILE = Dockerfile
DOCKER_TAG_PRE = smartgallery
DOCKER_TAG_POST_EXP = exp

DOCKER_TAG = ${SMARTGALLERY_VERSION}
DOCKER_LATEST_TAG = latest

SMARTGALLERY_CONTAINER_NAME = ${DOCKER_TAG_PRE}:${DOCKER_TAG}
SMARTGALLERY_CONTAINER_NAME_EXP = ${DOCKER_TAG_PRE}:${DOCKER_TAG_POST_EXP}

# used for builfx
SMARTGALLERY_NAME = ${DOCKER_TAG_PRE}

TEMPLATE_FILE=templates/index.html
SMARTGALLERY_FILE=smartgallery.py

# Try to optimize caching for development
RELEASE_BUILD=true
# apt-cacher-ng proxy
# APT Cache: HTTP only, most content from Ubuntu will work, limit download of common packages between images/builds
BUILD_APT_PROXY ?=

EXP_FOLDER=experiments
# if EXP_FOLDER/templates/index.html exists, set EXP_TEMPLATE_FILE to it
ifneq (,$(wildcard ${EXP_FOLDER}/templates/index.html))
	EXP_TEMPLATE_FILE=${EXP_FOLDER}/templates/index.html
else
	EXP_TEMPLATE_FILE=${TEMPLATE_FILE}
endif
# Same with smartgallery.py
ifneq (,$(wildcard ${EXP_FOLDER}/smartgallery.py))
	EXP_SMARTGALLERY_FILE=${EXP_FOLDER}/smartgallery.py
else
	EXP_SMARTGALLERY_FILE=${SMARTGALLERY_FILE}
endif

DOCKER_CMD=docker
DOCKER_PRE="NVIDIA_VISIBLE_DEVICES=void"
DOCKER_BUILD_ARGS=

# Avoid modifying the _PATH variables
BASE_OUTPUT_PATH=/mnt/output
BASE_INPUT_PATH=/mnt/input
BASE_SMARTGALLERY_PATH=/mnt/SmartGallery

# Adapt _REAL_PATH variables to match the locations on your systems (those are passed as environment variables to the container)
BASE_OUTPUT_PATH_REAL=/comfyui-nvidia/basedir/output
BASE_INPUT_PATH_REAL=/comfyui-nvidia/basedir/input
BASE_SMARTGALLERY_PATH_REAL=/comfyui-nvidia/SmartGallery_Temp

# set WANTED_UID and WANTED_GID
WANTED_UID=1000
WANTED_GID=1000

# Modify the alternate options as needed
EXPOSED_PORT=8189
THUMBNAIL_WIDTH=300
WEBP_ANIMATED_FPS=16.0
PAGE_SIZE=100
BATCH_SIZE=500
# see MAX_PARALLEL_WORKERS in smartgallery.py, if not set, will use "None" (ie use all available CPU cores)

all: 
	@echo "Available targets: build build_exp run kill buildx_rm"

build:
	CHOOSEN_NAME=${SMARTGALLERY_NAME} CHOOSEN_CONTAINER_NAME=${SMARTGALLERY_CONTAINER_NAME} CHOOSEN_TEMPLATE_FILE=${TEMPLATE_FILE} CHOOSEN_SMARTGALLERY_FILE=${SMARTGALLERY_FILE} make build_core

build_exp:
	CHOOSEN_NAME=${SMARTGALLERY_NAME_EXP} CHOOSEN_CONTAINER_NAME=${SMARTGALLERY_CONTAINER_NAME_EXP} CHOOSEN_TEMPLATE_FILE=${EXP_TEMPLATE_FILE} CHOOSEN_SMARTGALLERY_FILE=${EXP_SMARTGALLERY_FILE} make build_core

build_core:
	@echo ""; echo ""; echo "===== Building ${CHOOSEN_CONTAINER_NAME}"
	@$(eval VAR_NT="${CHOOSEN_NAME}")
	@echo "-- Docker command to be run:"
	@if [ "A${RELEASE_BUILD}" = "Atrue" ]; then \
		if [ -f buildkitd.toml ]; then \
			BUILDX_ADD="--driver docker-container --config ./buildkitd.toml"; \
		else \
			BUILDX_ADD=""; \
		fi; \
		echo "docker buildx ls | grep -q ${SMARTGALLERY_NAME} && echo \"builder already exists -- to delete it, use: docker buildx rm ${SMARTGALLERY_NAME}\" || docker buildx create --name ${SMARTGALLERY_NAME} $${BUILDX_ADD}"  > ${VAR_NT}.cmd; \
		echo "docker buildx use ${SMARTGALLERY_NAME} || exit 1" >> ${VAR_NT}.cmd; \
	else \
		echo "docker buildx use default || exit 1" > ${VAR_NT}.cmd; \
	fi
	@echo "BUILDX_EXPERIMENTAL=1 ${DOCKER_PRE} docker buildx debug --on=error build --progress plain ${DOCKER_BUILD_ARGS} \\" >> ${VAR_NT}.cmd
	@echo "  --build-arg CHOOSEN_TEMPLATE_FILE=\"${CHOOSEN_TEMPLATE_FILE}\" \\" >> ${VAR_NT}.cmd
	@echo "  --build-arg CHOOSEN_SMARTGALLERY_FILE=\"${CHOOSEN_SMARTGALLERY_FILE}\" \\" >> ${VAR_NT}.cmd
	@echo "  --build-arg BUILD_APT_PROXY=\"${BUILD_APT_PROXY}\" \\" >> ${VAR_NT}.cmd
	@echo "  --tag=\"${CHOOSEN_CONTAINER_NAME}\" \\" >> ${VAR_NT}.cmd
	@echo "  -f ${DOCKERFILE} \\" >> ${VAR_NT}.cmd
	@echo "  --load \\" >> ${VAR_NT}.cmd
	@echo "  ." >> ${VAR_NT}.cmd
	@echo "docker buildx use default" >> ${VAR_NT}.cmd
	@cat ${VAR_NT}.cmd | tee ${VAR_NT}.log.temp
	@echo "" | tee -a ${VAR_NT}.log.temp
	@echo "Press Ctl+c within 5 seconds to cancel"
	@for i in 5 4 3 2 1; do echo -n "$$i "; sleep 1; done; echo ""
# Actual build
	@chmod +x ./${VAR_NT}.cmd
	@script -a -e -c ./${VAR_NT}.cmd ${VAR_NT}.log.temp
	@mv ${VAR_NT}.log.temp ${VAR_NT}.log
	@rm -f ./${VAR_NT}.cmd

run:
	docker run --name ${SMARTGALLERY_NAME} -v $(BASE_OUTPUT_PATH_REAL):$(BASE_OUTPUT_PATH) -v $(BASE_INPUT_PATH_REAL):$(BASE_INPUT_PATH) -v $(BASE_SMARTGALLERY_PATH_REAL):$(BASE_SMARTGALLERY_PATH) -e BASE_OUTPUT_PATH=$(BASE_OUTPUT_PATH) -e BASE_INPUT_PATH=$(BASE_INPUT_PATH) -e BASE_SMARTGALLERY_PATH=$(BASE_SMARTGALLERY_PATH) -p $(EXPOSED_PORT):8189 -e WANTED_UID=${WANTED_UID} -e WANTED_GID=${WANTED_GID} ${SMARTGALLERY_CONTAINER_NAME}

kill:
	(docker kill ${SMARTGALLERY_NAME} && docker rm ${SMARTGALLERY_NAME}) || docker rm ${SMARTGALLERY_NAME}

buildx_rm:
	@docker buildx rm ${SMARTGALLERY_NAME}


##### Docker Container registry (maintainers only)
DOCKERHUB_REPO="mmartial/smart-comfyui-gallery"
DOCKER_PRESENT=$(shell image="${SMARTGALLERY_CONTAINER_NAME}"; if docker images --format "{{.Repository}}:{{.Tag}}" | grep -v ${DOCKERHUB_REPO} | grep -q $$image; then echo $$image; fi)

docker_tag:
	@if [ `echo ${DOCKER_PRESENT} | wc -w` -eq 0 ]; then echo "No images to tag"; exit 1; fi
	@echo "== About to tag ${SMARTGALLERY_CONTAINER_NAME} as:"
	@echo "${DOCKER_TAG_PRE}:${DOCKER_LATEST_TAG}"
	@echo "${DOCKERHUB_REPO}:${DOCKER_TAG}"
	@echo "${DOCKERHUB_REPO}:${DOCKER_LATEST_TAG}"
	@echo ""
	@echo "Press Ctl+c within 5 seconds to cancel"
	@for i in 5 4 3 2 1; do echo -n "$$i "; sleep 1; done; echo ""
	@docker tag ${SMARTGALLERY_CONTAINER_NAME} ${DOCKER_TAG_PRE}:${DOCKER_LATEST_TAG}
	@docker tag ${SMARTGALLERY_CONTAINER_NAME} ${DOCKERHUB_REPO}:${DOCKER_TAG}
	@docker tag ${SMARTGALLERY_CONTAINER_NAME} ${DOCKERHUB_REPO}:${DOCKER_LATEST_TAG}

docker_push:
	@echo "== Pushing ${DOCKERHUB_REPO}:${DOCKER_TAG} and ${DOCKERHUB_REPO}:${DOCKER_LATEST_TAG}"
	@echo ""
	@echo "Press Ctl+c within 5 seconds to cancel"
	@for i in 5 4 3 2 1; do echo -n "$$i "; sleep 1; done; echo ""
	@docker push ${DOCKERHUB_REPO}:${DOCKER_TAG}
	@docker push ${DOCKERHUB_REPO}:${DOCKER_LATEST_TAG}

# This will replace docker_tag and docker_push in the future
multiarch_buildx_push:
	docker buildx ls | grep -q multiarch || docker buildx create --name multiarch --driver docker-container
	docker buildx use multiarch
	docker buildx inspect --bootstrap
	docker run --privileged --rm tonistiigi/binfmt --install all
	docker buildx build \
		--platform linux/amd64,linux/arm64 \
		-t ${DOCKERHUB_REPO}:${DOCKER_TAG} \
		-t ${DOCKERHUB_REPO}:${DOCKER_LATEST_TAG} \
		--build-arg CHOOSEN_TEMPLATE_FILE=${TEMPLATE_FILE} \
		--build-arg CHOOSEN_SMARTGALLERY_FILE=${SMARTGALLERY_FILE} \
		-f ${DOCKERFILE} \
		--push \
		.
	docker buildx use default
	docker buildx rm multiarch

##### Maintainer
# Docker images (mmartial/smart-comfyui-gallery):
# - Build the images:
#   % make build
# - Confirm tags are correct, esp. latest (be ready to Ctrl+C before re-running)
#   % make docker_tag
# - Push the images (here too be ready to Ctrl+C before re-running)
#   % make docker_push
#
# GitHub release:
# - on the build system, checkout main and pull the changes
#   % git checkout main
#   % git pull
# - if needed: delete the development branch
#   % git branch -d dev_branch_name
# - Tag the release on GitHub
#   % git tag 1.41
#   % git push origin 1.41
# - Create a release on GitHub using the 1.41 tag, add the release notes, and publish
#
# Cleanup:
# - Erase build logs
#   % rm *.log
# - Erase the buildx builder
#   % make buildx_rm
#
# Icon conversion:
# magick assets/logo.png -define icon:auto-resize=256,128,64,48,32,16 static/galleryout/favicon.ico
