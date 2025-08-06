import socket  #현재 컴퓨터의 이름을 얻기 위한 표준 모듈
from flask import Flask, render_template
                         # HTML템플릿 연결하는 도구
app = Flask(__name__)
print("✅ Flask 앱 생성 완료")

@app.route('/')
def home():
    print("🚀 '/' 경로에 접속함") 

    if app.debug:   # 개발 모드(debug=True)일 때만 실행
        print("🛠 디버그 모드 ON")  
        hostname = '컴퓨터(인스턴스) : ' + socket.gethostname()
        print(f"📡 hostname 설정됨 → {hostname}")

    else:
        print("🔒 운영모드 (디버그 아님)")
        hostname = ' '      # 디버그 모드가 아닐 때 아래처럼 실행
    
    print("📄 index.html 렌더링 시작")
    return render_template('index.html', computername=hostname)


                     # socket.gethostname()
                     # 현재 컴퓨터의 이름을 가져옴
                     # hostname 변수에 그 이름을 붙여 문자열로 저장

                     # render_template('index.html', computername=hostname)
                     # templates 폴더에 있는 index.html 파일을 불러오고
                     # 거기에 computername 이라는 값으로 hostname을 넘겨줌

if __name__ == '__main__':
    print("🚦 서버 실행 준비 완료")
    app.run(debug=True)
