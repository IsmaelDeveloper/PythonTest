from gtts import gTTS
import pygame
import os

# audio file generation
text = "안녕하세요 . 키오스크 음성비서입니다, 현재 날씨는 맑은 상태이며, 바람은 조금 불고 있습니다.  현재 기온은 어제보다 1 도 가 높은 19 도 입니다 감사합니다"
tts = gTTS(text=text, lang='ko')
file_path = "helloKO.mp3"
tts.save(file_path)

# pygame initialisation
pygame.mixer.init()

# play audio file
pygame.mixer.music.load(file_path)
pygame.mixer.music.play()

# wait until audio is done playing
while pygame.mixer.music.get_busy():
    pygame.time.Clock().tick(10)

# delete audio file
os.remove(file_path)
