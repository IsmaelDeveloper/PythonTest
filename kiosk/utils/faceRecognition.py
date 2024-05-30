from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout, QSizePolicy,  QGraphicsView, QGraphicsScene, QGraphicsTextItem, QFrame, QStackedWidget
from PyQt5.QtGui import QImage, QPixmap, QFont
import cv2
import numpy as np
import torch
import os
import sys 
from ultralytics import YOLO
from facenet_pytorch import InceptionResnetV1
from PyQt5.QtCore import Qt 
from PyQt5.QtCore import QTimer, QRectF
from PyQt5.QtGui import QColor

class WebcamWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.STR_SYMBOL_RAW = ""
        self.STR_SYMBOL_CELSIUS = "℃"
        self.STR_SYMBOL_FAHRENHEIT = "℉"
        self.STR_SYMBOL_KELVIN = "K"
        self.CONST_KELVIN2CELSIUS = 262.15
        self.CONST_KELVIN2FEHRENHEIT = 459.67
        self.frame_count = 0

        self.base_path = getattr(sys, '_MEIPASS', os.path.dirname(
            os.path.abspath(__file__)))
        weights_path = os.path.join(
            self.base_path, 'weights', 'yolov8n-face.pt')
        self.face_detection_model = YOLO(weights_path)
        self.face_similarity_model = InceptionResnetV1(
            pretrained='vggface2').eval()
        self.detect_and_print_available_cameras()

        self.embed_path =  os.path.join(
            self.base_path, 'datasets', 'webcam_test' , 'member') 
        embed_lid = os.listdir(self.embed_path)
        self.embed_dict = {}
        for registered_person in embed_lid:
            embed_path2 = self.embed_path + '/' + registered_person + '/embeddings/'
            embed_lid2 = os.listdir(embed_path2)
            tmp_list = []
            for npy_name in embed_lid2:
                embeddings = np.load(embed_path2 + npy_name)
                tmp_list.append(embeddings)
            tmp = np.vstack(tmp_list)
            self.embed_dict[f'{registered_person}'] = tmp
        
        img = np.zeros((160, 160, 3))
        self.face_detection_model.predict(source=img, conf=0.6)
        self.get_result(img)
        print('Weights loaded successfully')

        distance_threshold = 0.6 
        self.image_label = QLabel(self)
        self.image_label.setSizePolicy(
            QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.image_label.setScaledContents(True)
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.image_label) 
        self.setLayout(layout)
        
        self.timer = QTimer(self) 
        if  hasattr(self, 'video_capture') and  hasattr(self, 'thermal_cam') :
            self.timer.timeout.connect(lambda: self.process_frame(self.video_capture, self.thermal_cam, self.face_detection_model, self.embed_dict, distance_threshold))
            self.timer.start(100) 
        self.mse_choose = 0.9

        self.graphicsView = QGraphicsView(self)
        self.graphicsView.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.graphicsView.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.graphicsView.setFrameShape(QFrame.NoFrame)
        self.graphicsView.setStyleSheet("background-color: rgba(0, 0, 0, 150); border: none;")
        self.scene = QGraphicsScene()
        self.graphicsView.setScene(self.scene)
        self.current_marquee_msg = ""
        self.textItem = QGraphicsTextItem(self.current_marquee_msg)
        self.textItem.setDefaultTextColor(QColor("white"))
        font = QFont("Arial",  20, QFont.Bold)
        self.textItem.setFont(font)
        self.scene.addItem(self.textItem)
        self.scene.setBackgroundBrush(Qt.transparent)
        self.timer.timeout.connect(self.scroll_text)
        self.timer.start(1)

        self.text_position = 0

    def scroll_text(self):
        self.text_position -= 2  
        if self.text_position < -self.textItem.boundingRect().width():
            self.text_position = self.width()

        self.textItem.setPos(self.text_position, 0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Positionnez graphicsView sur l'image_label. Exemple : en bas de l'image_label.
        self.graphicsView.setGeometry(0, self.image_label.height() - 50, self.image_label.width(), 50)

    def checkAndUpdateMarqueeText(self, new_text):
        if new_text != self.current_marquee_msg:
            self.current_marquee_msg = new_text
            self.updateMarqueeText(new_text)

    def updateMarqueeText(self, text):
        self.textItem.setPlainText(text)

    def detect_and_print_available_cameras(self):
        max_test_cameras = 10 
        for index in range(max_test_cameras):
            cap = cv2.VideoCapture(index) 
            if cap.isOpened():
                ret, frame = cap.read()
                if ret:
                    if self.is_thermal_camera(frame) == False:
                        if index == 0 :
                            self.video_capture = cap
                            self.thermal_cam = cv2.VideoCapture(2)
                            self.thermal_cam.set(cv2.CAP_PROP_FOURCC,
                                                cv2.VideoWriter.fourcc('Y', '1', '6', ' '))
                            self.thermal_cam.set(cv2.CAP_PROP_CONVERT_RGB, 0)
                            break
                        else :
                            self.video_capture = cap
                            self.thermal_cam = cv2.VideoCapture(0) 
                            self.thermal_cam.set(cv2.CAP_PROP_FOURCC,
                                                cv2.VideoWriter.fourcc('Y', '1', '6', ' '))
                            self.thermal_cam.set(cv2.CAP_PROP_CONVERT_RGB, 0)
                            break 
                cap.release() 

    def is_thermal_camera(self, frame): 
        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        unique_colors = len(np.unique(gray_frame)) 
        return unique_colors < 50

    def compensateHumanTemperature(tempC):
        if 20.0 < tempC and tempC <= 37.5:
            compTempC = tempC - (0.9 * (tempC - 36.5) + 0.2)
        elif 37.5 < tempC and tempC <= 40.0:
            compTempC = tempC - (0.9 * (tempC - 37.3))
        elif tempC > 40.0:
            compTempC = tempC
        return compTempC

    def convert_raw_to_celsius(self, raw):

        temperature_celsius = raw / 100 - self.CONST_KELVIN2CELSIUS

        return temperature_celsius

    def preprocessing_image(self, face_img):
        # 이미지 크기를 160x160으로 조정
        face_img = cv2.resize(face_img, (160, 160))
        # 이미지 채널 순서 변경 (OpenCV는 BGR 순서, PyTorch는 RGB 순서)
        face_img = cv2.cvtColor(face_img, cv2.COLOR_BGR2RGB)
        return face_img

    def get_result(self, face_img):
        face_img = torch.from_numpy(face_img.transpose((2, 0, 1))).float() / 255.0
        with torch.no_grad():
            result = self.face_similarity_model(face_img.unsqueeze(0))
        return result.numpy()
    
    def get_euclidean_distance_person(self, face_embedding_result, embed_dict):
        low_distance = float('inf')
        low_distance_person_name = None
        for registered_person, embeddings in embed_dict.items():
            distances = np.linalg.norm(embeddings - face_embedding_result, axis=1)
            min_distance = np.min(distances)
            if min_distance < low_distance:
                low_distance = min_distance
                low_distance_person_name = registered_person
        return low_distance, low_distance_person_name
    


    def process_frame(self, cap, thermal_cam, face_detection_model, embed_dict, distance_threshold):
        PREVIOUS_LABELS = {} 
        ret, frame = cap.read()
        self.frame_count += 1
        result = face_detection_model.predict(source=frame, conf=0.7)
        result = result[0].cpu().numpy()
        for box in result.boxes:
            x1, y1, x2, y2 = box.xyxy[0].astype(int).tolist()
            face_img = self.preprocessing_image(frame[y1:y2, x1:x2])
            result = self.get_result(face_img)
            low_distance, low_distance_person_name = self.get_euclidean_distance_person(result, embed_dict)
            if low_distance <= distance_threshold:
                color = (0, 255, 0)  # Green for known faces
                PREVIOUS_LABELS[(x1, y1, x2, y2)] = low_distance_person_name
            else:
                color = (0, 0, 255)  # Red for unknown faces
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            text = f'{low_distance_person_name}, Dist: {low_distance:.2f}' if low_distance <= distance_threshold else f'Unknown, Dist: {low_distance:.2f}'
            cv2.putText(frame, text, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1, cv2.LINE_AA)
        image = QImage(frame, frame.shape[1], frame.shape[0],
        frame.strides[0], QImage.Format_RGB888).rgbSwapped()
        self.image_label.setPixmap(QPixmap.fromImage(image))

    def thermal_cam__frame(cam):
        while cam.isOpened():
            # Read frames from the thermal camera
            rval, frame = cam.read()
            if not rval:
                break

    # def update_frame(self):
    #     ret, frame = self.video_capture.read()
    #     # ret_thermal, frame_thermal = self.thermal_cam.read()
    #     # if ret and ret_thermal:
    #     if ret :
    #         result = self.face_detection_model.predict(source=frame, conf=0.6)
    #         result = result[0].cpu().numpy()
    #         for box in result.boxes:
    #             x1, y1, x2, y2 = box.xyxy[0].astype(int).tolist()
    #             face_img = self.preprocessing_image(frame[y1:y2, x1:x2])
    #             result = self.get_result(face_img)
    #             low_mse_value, low_mse_person_name = self.get_mse_value_person(
    #                 result, self.embed_dict)
    #             color = (0, 255, 0) if low_mse_value <= self.mse_choose else (
    #                 0, 0, 255)
    #             cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
    #             # temp_1 = self.ompensateHumanTemperature(self.convert_raw_to_celsius(
    #             #     frame_thermal[int((x1+x2)/2/10.7)][int((y1+y2)/2/8)]))
    #             temp_1 = 0
    #             text = f'Name: {low_mse_person_name}, temp: {temp_1:.2f}' if low_mse_value <= self.mse_choose else f'Unknown, temp: {temp_1:.2f}'
    #             cv2.putText(frame, text, (x1, y1 - 10),
    #                         cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1, cv2.LINE_AA)
    #         image = QImage(frame, frame.shape[1], frame.shape[0],
    #                        frame.strides[0], QImage.Format_RGB888).rgbSwapped()
    #         self.image_label.setPixmap(QPixmap.fromImage(image))

    def releaseCamera(self):
        self.timer.stop()
        if hasattr(self, 'video_capture') and self.video_capture.isOpened():
            self.video_capture.release()
        if hasattr(self, 'thermal_cam') and self.thermal_cam.isOpened():
            self.thermal_cam.release()


    def reactivateCamera(self):
        # # Libérer les caméras actuelles si elles sont ouvertes
        # if hasattr(self, 'video_capture') and self.video_capture.isOpened():
        #     self.video_capture.release()
        # if hasattr(self, 'thermal_cam') and self.thermal_cam.isOpened():
        #     self.thermal_cam.release()

        # Réinitialiser les caméras disponibles
        self.detect_and_print_available_cameras()

        try:
            self.timer.timeout.disconnect()
        except TypeError:
            pass 
        self.timer.timeout.connect(lambda: self.process_frame(
            self.video_capture, self.thermal_cam, self.face_detection_model, self.embed_dict, 0.6)) 
        self.timer.timeout.connect(self.scroll_text)
        self.timer.start(100)

