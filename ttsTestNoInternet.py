import pyttsx3

engine = pyttsx3.init()
engine.setProperty('voice', 'ko-KR')
engine.say( "안녕하세요 . 키오스크 음성비서입니다, 현재 날씨는 맑은 상태이며, 바람은 조금 불고 있습니다.  현재 기온은 어제보다 1 도 가 높은 19 도 입니다 감사합니다")
engine.runAndWait()
