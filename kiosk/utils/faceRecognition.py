from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout, QSizePolicy, QGraphicsView, QGraphicsScene, QGraphicsTextItem, QFrame
from PyQt5.QtGui import QImage, QPixmap, QFont
import cv2
import numpy as np
import torch
import os
import sys
import sqlite3
from ultralytics import YOLO
from facenet_pytorch import InceptionResnetV1
from PyQt5.QtCore import Qt, QTimer, QRectF
from PyQt5.QtGui import QColor
from PIL import Image, ImageDraw, ImageFont
import threading
import time
import logging

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

        self.base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        logging.getLogger('ultralytics').setLevel(logging.WARNING)
        weights_path = os.path.join(self.base_path, 'weights', 'best.pt')
        self.face_detection_model = YOLO(weights_path)
        self.face_similarity_model = InceptionResnetV1(pretrained='vggface2').eval()
        self.detect_and_print_available_cameras()

        self.embed_path = os.path.join(self.base_path, 'datasets', 'webcam_test', 'member')
        self.embed_dict = {}

        # Start the embedding update thread
        embedding_update_thread = threading.Thread(target=self.update_embeddings)
        embedding_update_thread.daemon = True
        embedding_update_thread.start()

        img = np.zeros((112, 112, 3))
        print('Weights loaded successfully')

        self.rmse_threshold = 1.05
        self.image_label = QLabel(self)
        self.image_label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.image_label.setScaledContents(True)
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.image_label)
        self.setLayout(layout)
        
        self.timer = QTimer(self)
        if hasattr(self, 'video_capture') and hasattr(self, 'thermal_cam'):
            self.timer.timeout.connect(lambda: self.process_frame(self.video_capture, self.thermal_cam, self.face_detection_model, self.embed_dict, self.rmse_threshold))
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
        font = QFont("Arial", 20, QFont.Bold)
        self.textItem.setFont(font)
        self.scene.addItem(self.textItem)
        self.scene.setBackgroundBrush(Qt.transparent)
        self.timer.timeout.connect(self.scroll_text)
        self.timer.start(1)

        self.text_position = 0

    def scroll_text(self):
        self.text_position -= 5
        if self.text_position < -self.textItem.boundingRect().width():
            self.text_position = self.width()
        self.textItem.setPos(self.text_position, 0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
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
                        if index == 0:
                            self.video_capture = cap
                            self.thermal_cam = cv2.VideoCapture(2)
                            self.thermal_cam.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter.fourcc('Y', '1', '6', ' '))
                            self.thermal_cam.set(cv2.CAP_PROP_CONVERT_RGB, 0)
                            break
                        else:
                            self.video_capture = cap
                            self.thermal_cam = cv2.VideoCapture(0)
                            self.thermal_cam.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter.fourcc('Y', '1', '6', ' '))
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
        face_img = cv2.resize(face_img, (112, 112))
        face_img = cv2.cvtColor(face_img, cv2.COLOR_BGR2RGB)
        return face_img

    def get_result(self, face_img):
        face_img = torch.from_numpy(face_img.transpose((2, 0, 1))).float() / 255.0
        with torch.no_grad():
            result = self.face_similarity_model(face_img.unsqueeze(0))
        return result.numpy()

    def get_rmse_value_person(self, face_embedding_result, embed_dict):
        lowest_rmse_value = float('inf')
        lowest_rmse_person_name = ''
        for registered_person, embeddings in embed_dict.items():
            rmses = np.sqrt(np.mean((embeddings - face_embedding_result)**2, axis=1) * 1000)
            min_rmse = np.min(rmses)
            if min_rmse < lowest_rmse_value:
                lowest_rmse_value = min_rmse
                lowest_rmse_person_name = registered_person
        return lowest_rmse_value, lowest_rmse_person_name
    
    def get_user_name(self, kiosk_seq):
        try:
            conn = sqlite3.connect('kioskdb.db')
            cursor = conn.cursor()
            cursor.execute("SELECT user_nm FROM users WHERE user_seq = ?", (kiosk_seq,))
            result = cursor.fetchone()
            conn.close()
            if result:
                return result[0]
            else:
                return kiosk_seq
        except Exception as e:
            print(f"Error accessing database: {e}")
            return kiosk_seq


    def process_frame(self, cap, thermal_cam, face_detection_model, embed_dict, rmse_threshold):
        ret, frame = cap.read()
        self.frame_count += 1
        result = face_detection_model.track(frame, persist=True, conf=0.6)
        annotated_frame = result[0].plot()
        result = result[0].cpu().numpy()
        for box in result.boxes:
            x1, y1, x2, y2 = box.xyxy[0].astype(int).tolist()
            face_img = self.preprocessing_image(frame[y1:y2, x1:x2])
            result = self.get_result(face_img)
            low_rmse_value, low_rmse_person_name = self.get_rmse_value_person(result, embed_dict)
            if low_rmse_value <= rmse_threshold:
                color = (0, 255, 0)
                name = self.get_user_name(low_rmse_person_name)
                label = f'Name: {name}, {low_rmse_value:.2f}'
            else:
                color = (0, 0, 255)
                label = f'Unknown, {low_rmse_value:.2f}'
            frame = self.draw_text(frame, label, (x1, y1 - 30))
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        image = QImage(frame, frame.shape[1], frame.shape[0], frame.strides[0], QImage.Format_RGB888).rgbSwapped()
        self.image_label.setPixmap(QPixmap.fromImage(image))

    def draw_text(self, img, text, position, font_path="ressources/NanumGothicBold.ttf", font_size=20):
        img_pil = Image.fromarray(img)
        draw = ImageDraw.Draw(img_pil)
        font = ImageFont.truetype(font_path, font_size)
        draw.text(position, text, font=font, fill=(0, 0, 255))
        img = np.array(img_pil)
        return img

    def update_embeddings(self):
        while True:
            print("test test")
            embed_dict_new = {}
            embed_lid = os.listdir(self.embed_path)
            for registered_person in embed_lid:
                embed_path2 = os.path.join(self.embed_path, registered_person, 'embeddings')
                embed_lid2 = os.listdir(embed_path2)
                tmp_list = []
                for npy_name in embed_lid2:
                    embeddings = np.load(os.path.join(embed_path2, npy_name))
                    tmp_list.append(embeddings)
                tmp = np.vstack(tmp_list)
                embed_dict_new[registered_person] = tmp
            self.embed_dict = embed_dict_new
            time.sleep(10)

    def releaseCamera(self):
        self.timer.stop()
        if hasattr(self, 'video_capture') and self.video_capture.isOpened():
            self.video_capture.release()
        if hasattr(self, 'thermal_cam') and self.thermal_cam.isOpened():
            self.thermal_cam.release()

    def reactivateCamera(self):
        self.detect_and_print_available_cameras()
        try:
            self.timer.timeout.disconnect()
        except TypeError:
            pass
        self.timer.timeout.connect(lambda: self.process_frame(self.video_capture, self.thermal_cam, self.face_detection_model, self.embed_dict, self.rmse_threshold))
        self.timer.timeout.connect(self.scroll_text)
        self.timer.start(100)
