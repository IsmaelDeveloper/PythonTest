FROM ubuntu:20.04

# Éviter les messages de dialogue de front-end pendant les installations de paquets
ENV DEBIAN_FRONTEND=noninteractive

# Mise à jour des paquets et installation de Python 3.9 et des outils nécessaires
RUN apt-get update && apt-get install -y \
    python3.9 \
    python3-pip \
    python3.9-venv \
    unzip \
    fonts-dejavu-core \
    ttf-bitstream-vera \
    fonts-noto-cjk \
    libgl1-mesa-dri \
    libgl1-mesa-glx \
    libgstreamer1.0-dev \
    libgstreamer-plugins-base1.0-dev \
    libgstreamer-plugins-bad1.0-dev \
    gstreamer1.0-plugins-base \
    gstreamer1.0-plugins-good \
    gstreamer1.0-plugins-bad \
    gstreamer1.0-plugins-ugly \
    gstreamer1.0-libav \
    gstreamer1.0-tools \
    gstreamer1.0-x \
    gstreamer1.0-alsa \
    gstreamer1.0-gl \
    gstreamer1.0-gtk3 \
    gstreamer1.0-qt5 \
    gstreamer1.0-pulseaudio \
    && rm -rf /var/lib/apt/lists/*

# Mettre à jour pip et installer les packages Python nécessaires
RUN python3.9 -m pip install --upgrade pip && \
    pip install PyQt5 PyQtWebEngine

# Copier et extraire l'application
COPY ./build_ultralytics.zip ./
RUN unzip ./build_ultralytics.zip -d ./ && \
    rm ./build_ultralytics.zip

WORKDIR /build_ultralytics/main

# Rendre le fichier principal exécutable
RUN chmod +x ./main

# Configurer l'intégration GLX pour Qt et désactiver le sandbox pour QtWebEngine
ENV QT_XCB_GL_INTEGRATION=xcb_glx
ENV QTWEBENGINE_DISABLE_SANDBOX=1

CMD ["./main"]
