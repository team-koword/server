# Server
We have three server. websocket, competition, cooperation.

pixel is option.


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
