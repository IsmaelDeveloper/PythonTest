from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout, QSizePolicy
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QImage, QPixmap
import cv2
import numpy as np
import torch
import os
from ultralytics import YOLO
from facenet_pytorch import InceptionResnetV1


class WebcamWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.CONST_KELVIN2CELSIUS = 262.15

        weights_path = './utils/weights/yolov8n-face.pt'
        self.face_detection_model = YOLO(weights_path)
        self.face_similarity_model = InceptionResnetV1(
            pretrained='vggface2').eval()

        self.thermal_cam = cv2.VideoCapture(2)
        self.thermal_cam.set(cv2.CAP_PROP_FOURCC,
                             cv2.VideoWriter.fourcc('Y', '1', '6', ' '))
        self.thermal_cam.set(cv2.CAP_PROP_CONVERT_RGB, 0)

        self.embed_path = './utils/datasets/webcam_test/member/'
        embed_lid = os.listdir(self.embed_path)
        self.embed_dict = {}
        for registered_person in embed_lid:
            embed_path2 = self.embed_path + registered_person + '/embeddings/'
            embed_lid2 = os.listdir(embed_path2)
            tmp_list = []
            for npy_name in embed_lid2:
                embeddings = np.load(embed_path2 + npy_name)
                tmp_list.append(embeddings)
            tmp = np.vstack(tmp_list)
            self.embed_dict[f'{registered_person}'] = tmp

        self.video_capture = cv2.VideoCapture(0)
        self.image_label = QLabel(self)
        self.image_label.setSizePolicy(
            QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.image_label.setScaledContents(True)
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.image_label)
        self.setLayout(layout)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(100)
        self.mse_choose = 0.9

    def convert_raw_to_celsius(self, raw):

        temperature_celsius = raw / 100 - self.CONST_KELVIN2CELSIUS

        return temperature_celsius

    def preprocessing_image(self, face_img):
        face_img = cv2.resize(face_img, (160, 160))
        face_img = cv2.cvtColor(face_img, cv2.COLOR_BGR2RGB)
        return face_img

    def get_result(self, face_img):
        face_img = torch.from_numpy(
            face_img.transpose((2, 0, 1))).float() / 255.0
        with torch.no_grad():
            result = self.face_similarity_model(face_img.unsqueeze(0))
        return result.numpy()

    def get_mse_value_person(self, face_embedding_result, embed_dict):
        low_mse_value = 1e+10
        for registered_person, _ in embed_dict.items():
            mse = min(np.mean(
                (embed_dict[registered_person] - face_embedding_result)**2, axis=1) * 1000)
            if mse < low_mse_value:
                low_mse_value = mse
                low_mse_person_name = registered_person
        return low_mse_value, low_mse_person_name

    def update_frame(self):
        ret, frame = self.video_capture.read()
        ret_thermal, frame_thermal = self.thermal_cam.read()
        if ret and ret_thermal:
            result = self.face_detection_model.predict(source=frame, conf=0.6)
            result = result[0].cpu().numpy()
            for box in result.boxes:
                x1, y1, x2, y2 = box.xyxy[0].astype(int).tolist()
                face_img = self.preprocessing_image(frame[y1:y2, x1:x2])
                result = self.get_result(face_img)
                low_mse_value, low_mse_person_name = self.get_mse_value_person(
                    result, self.embed_dict)
                if low_mse_value <= self.mse_choose:
                    color = (0, 255, 0)
                else:
                    color = (0, 0, 255)
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                temp_1 = self.convert_raw_to_celsius(
                    frame_thermal[int((x1+x2)/2/10.7)][int((y1+y2)/2/8)])
                text = f'Name: {low_mse_person_name}, temp: {temp_1:.2f}' if low_mse_value <= self.mse_choose else f'Unknown, temp: {temp_1:.2f}'
                cv2.putText(frame, text, (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1, cv2.LINE_AA)
            image = QImage(frame, frame.shape[1], frame.shape[0],
                           frame.strides[0], QImage.Format_RGB888).rgbSwapped()
            self.image_label.setPixmap(QPixmap.fromImage(image))

    def releaseCamera(self):
        self.timer.stop()
        self.video_capture.release()
        self.thermal_cam.release()

    def reactivateCamera(self):
        if not self.video_capture.isOpened():
            self.video_capture = cv2.VideoCapture(0)
        if (not self.thermal_cam.isOpened()):
            self.thermal_cam = cv2.VideoCapture(2)
            self.thermal_cam.set(cv2.CAP_PROP_FOURCC,
                                 cv2.VideoWriter.fourcc('Y', '1', '6', ' '))
            self.thermal_cam.set(cv2.CAP_PROP_CONVERT_RGB, 0)
