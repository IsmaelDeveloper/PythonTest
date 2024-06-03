#!/bin/bash

read -p "사용자 이름을 입력하세요: " USERNAME

# Créer les scripts de redémarrage et d'arrêt dans /etc sans sudo
echo -e '#!/bin/sh\nCONTAINER_ID=$(docker ps -q --filter ancestor=ismaelhadj/kiosk_docker:polling)\nsudo docker stop $CONTAINER_ID' | sudo tee /etc/shutdown.sh > /dev/null
echo -e '#!/bin/sh\nCONTAINER_ID=$(docker ps -q --filter ancestor=ismaelhadj/kiosk_docker:polling)\nsudo docker restart $CONTAINER_ID' | sudo tee /etc/reboot.sh > /dev/null


# Rendre les scripts exécutables
sudo chmod +x /etc/shutdown.sh
sudo chmod +x /etc/reboot.sh

# Vérifier que les scripts ont été créés et sont exécutables
ls -l /etc/shutdown.sh /etc/reboot.sh

# Autoriser l'accès au serveur X pour les applications Docker
xhost +local:docker

# Lancer le conteneur Docker avec les volumes montés pour les scripts
sudo docker run --privileged -it \
    -e DISPLAY=$DISPLAY \
    -e USERNAME=$USERNAME \
    -v /tmp/.X11-unix:/tmp/.X11-unix \
    -v /etc/machine-id:/etc/machine-id \
    -v /run/user/$(id -u)/pulse:/run/user/$(id -u)/pulse \
    -e PULSE_SERVER=unix:/run/user/$(id -u)/pulse/native \
    -v /etc/shutdown.sh:/scripts/shutdown.sh \
    -v /etc/reboot.sh:/scripts/reboot.sh \
    -v /var/run/docker.sock:/var/run/docker.sock \
    --device /dev/snd \
    ismaelhadj/kiosk_docker:polling
