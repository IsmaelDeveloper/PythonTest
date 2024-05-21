#!/bin/bash

read -p "사용자 이름을 입력하세요: " USERNAME

xhost +local:docker

sudo docker run --privileged -it \
    -e DISPLAY=$DISPLAY \
    -e USERNAME=$USERNAME \
    -v /tmp/.X11-unix:/tmp/.X11-unix \
    -v /etc/machine-id:/etc/machine-id \
    -v /run/user/$(id -u)/pulse:/run/user/$(id -u)/pulse \
    -e PULSE_SERVER=unix:/run/user/$(id -u)/pulse/native \
    --device /dev/snd \
    ismaelhadj/kiosk_docker:nozip


