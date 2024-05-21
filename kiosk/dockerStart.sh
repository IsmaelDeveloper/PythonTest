#!/bin/bash

read -p "사용자 이름을 입력하세요: " USERNAME

xhost +local:docker

sudo docker run --privileged -it \
    -e DISPLAY=$DISPLAY -e USERNAME=$USERNAME \
    -v /tmp/.X11-unix:/tmp/.X11-unix \
    ismaelhadj/kiosk_docker
