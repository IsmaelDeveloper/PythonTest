FROM ubuntu:20.04

# Éviter les messages de dialogue de front-end pendant les installations de paquets
ENV DEBIAN_FRONTEND=noninteractive

# Mise à jour des paquets et installation de Python 3.9 et des outils nécessaires
RUN apt-get update && apt-get install -y \
    python3.9 \
    python3-pip \
    python3.9-venv \
    unzip \
    libgl1-mesa-dri \
    libgl1-mesa-glx \
    libgstreamer1.0-0 \
    libgstreamer-plugins-base1.0-0 \
    gstreamer1.0-plugins-base \
    gstreamer1.0-plugins-good \
    gstreamer1.0-plugins-bad \
    gstreamer1.0-plugins-ugly \
    libxcomposite1 \
    libxi6 \
    libfontconfig1 \
    libasound2 \
    libxrender1 \
    libpulse0 \
    libxrandr2 \
    libxcursor1 \
    libxss1 \
    libnss3 \
    libx11-xcb1 \
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
