from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout, QSizePolicy
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QImage, QPixmap
import cv2
import numpy as np
import torch
from facenet_pytorch import InceptionResnetV1
from sklearn.metrics.pairwise import cosine_similarity
import os


class WebcamWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Initialisation du modèle de détection de visages et de similarité
        # DNN 얼굴 탐지 모델 가중치 파일 경로
        face_detection_model_path = "utils/resources/model/res10_300x300_ssd_iter_140000.caffemodel"
        model_proto_path = "utils/resources/model/deploy.prototxt"  # DNN 모델 프로토콜 파일 경로
        self.face_detection_model = cv2.dnn.readNetFromCaffe(
            model_proto_path, face_detection_model_path)
        self.face_similarity_model = InceptionResnetV1(
            pretrained='vggface2').eval()
        self.cosine_threshold = 0.75

        # Chargement des embeddings
        self.embed_path = 'utils/datasets/webcam_test/member/'
        self.embed_dict = self.load_embeddings(self.embed_path)

        # Configuration de la caméra
        self.video_capture = cv2.VideoCapture(0)

        # Configuration de l'interface utilisateur
        self.image_label = QLabel(self)
        self.image_label.setSizePolicy(
            QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.image_label.setScaledContents(True)
        layout = QVBoxLayout()
        layout.addWidget(self.image_label)
        self.setLayout(layout)

        # Timer pour la mise à jour de l'image
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(100)

    def load_embeddings(self, embed_path):
        embed_dict = {}
        for registered_person in os.listdir(embed_path):
            embed_lid2 = os.listdir(os.path.join(
                embed_path, registered_person, 'embeddings'))
            tmp_list = [np.load(os.path.join(
                embed_path, registered_person, 'embeddings', npy_name)) for npy_name in embed_lid2]
            embed_dict[registered_person] = np.vstack(tmp_list)
        return embed_dict

    def preprocessing_image(self, face_img):
        face_img = cv2.resize(face_img, (160, 160))
        face_img = cv2.cvtColor(face_img, cv2.COLOR_BGR2RGB)
        face_img = face_img.transpose((2, 0, 1))
        return face_img

    def get_result(self, face_img):
        face_img = torch.from_numpy(face_img).float() / 255.0
        face_img = torch.unsqueeze(face_img, 0)
        with torch.no_grad():
            result = self.face_similarity_model(face_img)
        return result.numpy()

    def get_cosine_similarity(self, face_embedding_result):
        max_cosine_similarity = -1
        most_similar_person_name = ''
        for registered_person, embeddings in self.embed_dict.items():
            cosine_similarities = cosine_similarity(
                embeddings, face_embedding_result)
            max_similarity = np.max(cosine_similarities)
            if max_similarity > max_cosine_similarity:
                max_cosine_similarity = max_similarity
                most_similar_person_name = registered_person
        return max_cosine_similarity, most_similar_person_name

    def update_frame(self):
        ret, frame = self.video_capture.read()
        if ret:
            frame = cv2.flip(frame, 1)
            (h, w) = frame.shape[:2]
            blob = cv2.dnn.blobFromImage(cv2.resize(
                frame, (300, 300)), 1.0, (300, 300), (104.0, 177.0, 123.0))
            self.face_detection_model.setInput(blob)
            detections = self.face_detection_model.forward()

            for i in range(0, detections.shape[2]):
                confidence = detections[0, 0, i, 2]
                if confidence > 0.3:
                    box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
                    (startX, startY, endX, endY) = box.astype("int")
                    face_img = frame[startY:endY, startX:endX]
                    if face_img.size == 0:
                        continue

                    face_img = self.preprocessing_image(face_img)
                    result = self.get_result(face_img)
                    max_cosine_similarity, most_similar_person_name = self.get_cosine_similarity(
                        result)
                    text = f'Name: {most_similar_person_name}, cos: {max_cosine_similarity:.2f}' if max_cosine_similarity >= self.cosine_threshold else 'Unknown'
                    cv2.putText(frame, text, (startX, startY - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
                    cv2.rectangle(frame, (startX, startY),
                                  (endX, endY), (0, 255, 0), 2)

            image = QImage(frame, frame.shape[1], frame.shape[0],
                           frame.strides[0], QImage.Format_RGB888).rgbSwapped()
            self.image_label.setPixmap(QPixmap.fromImage(image))

    def releaseCamera(self):
        self.timer.stop()
        self.video_capture.release()

    def reactivateCamera(self):
        if not self.video_capture.isOpened():
            self.video_capture = cv2.VideoCapture(0)
