DOCKERFILE = Dockerfile
DOCKER_TAG = latest

# Avoid modifying the _PATH variables
BASE_OUTPUT_PATH=/mnt/output
BASE_INPUT_PATH=/mnt/input
BASE_SMARTGALLERY_PATH=/mnt/SmartGallery

# Adapt _REAL_PATH variables to match the locations on your systems
BASE_OUTPUT_PATH_REAL=/comfyui-nvidia/basedir/output
BASE_INPUT_PATH_REAL=/comfyui-nvidia/basedir/input
BASE_SMARTGALLERY_PATH_REAL=/comfyui-nvidia/SmartGallery_Temp

# Modify the alternate options as needed
EXPOSED_PORT=8189
THUMBNAIL_WIDTH=300
WEBP_ANIMATED_FPS=16.0
PAGE_SIZE=100
BATCH_SIZE=500
# see MAX_PARALLEL_WORKERS in smartgallery.py, if not set, will use "None" (ie use all available CPU cores)

all: build

build:
	docker build -t smartgallery:$(DOCKER_TAG) -f $(DOCKERFILE) .

run:
	docker run --name smartgallery -v $(BASE_OUTPUT_PATH_REAL):$(BASE_OUTPUT_PATH) -v $(BASE_INPUT_PATH_REAL):$(BASE_INPUT_PATH) -v $(BASE_SMARTGALLERY_PATH_REAL):$(BASE_SMARTGALLERY_PATH) -e BASE_OUTPUT_PATH=$(BASE_OUTPUT_PATH) -e BASE_INPUT_PATH=$(BASE_INPUT_PATH) -e BASE_SMARTGALLERY_PATH=$(BASE_SMARTGALLERY_PATH) -p $(EXPOSED_PORT):8189 smartgallery:$(DOCKER_TAG)

kill:
	(docker kill smartgallery && docker rm smartgallery) || docker rm smartgallery
