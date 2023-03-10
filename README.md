# Backend(Server)
총 3개의 서버 존재<br/>
- websocket -> 웹소켓 서버<br/>
- competition -> 경쟁모드 게임 서버<br/>
- cooperation -> 협동 모드 게임 서버<br/>

기능 별로 서버를 분리하여 로직 간 간섭을 최소화 하였습니다.<br/>
또한 비동기 처리를 위해 FastAPI 프레임워크를 사용하였습니다.

## APM & Monitoring
![sentry (1)](https://user-images.githubusercontent.com/115965829/224282827-9c8d987e-7299-4022-a261-b61adc98dccb.png)
![Prometheus_software_logo svg (1)](https://user-images.githubusercontent.com/115965829/224283616-f37c1fdc-ab74-47e4-88ed-7c182d152052.png)
![내 프로젝트 (1)](https://user-images.githubusercontent.com/115965829/224284029-834aa269-954b-4871-8684-334ab8335a64.png)


## Project Setup
```sh
git clone https://github.com/team-koword/server.git
cd server
```

### websocket

```sh
cd websocket

#we use docker, so you have to change below code
if game_mode == "WordCard":
    api_host = "http://gameserver:7777/" -> "http://localhost:{port_number}/"
else:
    api_host = "http://new_game:7778/" -> "http://localhost:{port_number}/"

#if you want, you can use venv
pip install -r requirements.txt
uvicorn main:app --port {port_number} --reload
```

### competition

```sh
cd competition
#if you want, you can use venv
pip install -r requirements.txt
uvicorn main:app --port {port_number} --reload
```

### cooperation

```sh
cd cooperation
#if you want, you can use venv
pip install -r requirements.txt
uvicorn main:app --port {port_number} --reload
```
