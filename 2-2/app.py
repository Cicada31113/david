print(f"DEBUG 상태: __debug__ == {__debug__}")


import socket  #현재 컴퓨터의 이름을 얻기 위한 표준 모듈
from flask import Flask, render_template
                         # HTML템플릿 연결하는 도구
app = Flask(__name__)
print("✅ Flask 앱 생성 완료")



if __name__ == '__main__':
    print("🚦 서버 실행 준비 완료")
    app.run(debug=True)


# 문제에서 "Python 실행 시 __debug__ 플래그 활성화를 위한 인자를 포함해 실행한다."
# 라고 하였는데, 이를 위해 print(f"DEBUG 상태: __debug__ == {__debug__}") 를 추가했고,
# 실행시 python -O app.py 하여 디버깅 끄고 실행했음 (O는 대문자 O)

