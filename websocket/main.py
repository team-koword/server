import json
from collections import defaultdict

from fastapi import FastAPI, WebSocket, BackgroundTasks
from starlette.websockets import WebSocketDisconnect
from starlette.middleware.cors import CORSMiddleware
import requests
import asyncio
import aiohttp
import time
import sentry_sdk
import uvloop
import sys
import logging

asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())


sentry_sdk.init(
    dsn="https://421b5d7b3f4a4bb8a64c60cbb9de622d@o4504772214325248.ingest.sentry.io/4504774549241856",
    environment="production",

    # Set traces_sample_rate to 1.0 to capture 100%
    # of transactions for performance monitoring.
    # We recommend adjusting this value in production,
    traces_sample_rate=1.0,
)




app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(format='\n%(levelname)s:    %(asctime)s\n%(message)s\n', level=logging.INFO)


class Notifier:
    """
        Manages chat room sessions and members along with message routing
    """

    def __init__(self):
        self.generator = self.get_notification_generator()
        self.user_access_info: dict = defaultdict(lambda: defaultdict(dict))     # 현재 접속중인 소켓 정보
        self.user_turn_count: dict = defaultdict(dict)                           # user_access_info의 인덱스: 순서대로 접근하기 위해 선언한 변수
        self.room_info: dict = defaultdict(lambda: defaultdict(dict))            # 현재 방이 정보 ->게임 진행중인지 여부 - [0: 대기중, 1: 진행중], 게임모드  - ["", "WordCard", "CoOpGame"]
        self.recent_turn_user: dict = defaultdict(dict)                          # 현재 턴인 유저의 정보
        self.board_size = 11                                                     # game_board size
        self.turn_timer_task: dict = defaultdict(dict)                           # 비동기로 실행할 매 턴 타이머
        self.limit_timer_task: dict = defaultdict(dict)                          # 비동기로 실행할 게임 제한 시간 타이머
        self.game_time = 60                                                      # 게임 제한 시간(초)
        self.turn_time = 12                                                      # 유저 별 턴 시간(초)
        self.game_timer_stop: dict = defaultdict(dict)                           # 1이면 게임타이머 3초간 멈춤.
        self.new_game_tick = 0.5                                                 # new_game_time_tick
        self.ready_time = 3                                                      # 게임 시작 시 대기 시간
        self.ready_timer_task: dict = defaultdict(dict)                          # 시작 시 대기 시간 타이머
        self.survival_timer_task: dict = defaultdict(dict)                       # 생존 시간 타이머

    async def get_notification_generator(self):
        while True:
            message = yield
            msg = message["message"]
            room_name = message["room_name"]
            await self._notify(msg, room_name)

    async def push(self, msg: str, room_name: str = None):
        message_body = {"message": msg, "room_name": room_name}
        await self.generator.asend(message_body)

    async def send_to_room(self, room_name, send_info):
        """같은 방에 있는 사람에게 뿌려주기"""
        try:
            wesocket_list = self.get_websocket_lists_from_dict(room_name)
            while len(wesocket_list) > 0:
                websocket = wesocket_list.pop()
                if websocket.client_state.name == "CONNECTED":
                    await websocket.send_text(send_info)
        except Exception as exception:
            logging.exception(exception)

    async def send_video_to_room(self, room_name, send_info):
        """같은 방에 있는 사람에게 비디오 보내기. 보낼 때 마다 조건을 체크해야 하니 일반 알림을 보내는 것과 분리함"""
        try:
            wesocket_list = self.get_websocket_lists_from_dict(room_name)
            while len(wesocket_list) > 0:
                websocket = wesocket_list.pop()
                if websocket.client_state.name == "CONNECTED":
                    if self.user_access_info[room_name][websocket]["video_status"] == True:
                        await websocket.send_text(send_info)
        except Exception as exception:
            logging.exception(exception)
        

    async def connect(self, websocket: WebSocket, room_name: str):
        """웹소켓 연결 설정"""
        await websocket.accept()
   
    def remove(self, websocket: WebSocket, room_name: str, limit_timer_task, turn_timer_task):
        """방에서 퇴장한 user 정보 설정"""
        try:
            # 기존 딕셔너리에서 user_name 가져오고 해당 키 삭제. 이후 클라이언트로 user_name 전달
            # 이것은 턴을 위한 유저 정보
            logging.info(self.user_access_info[room_name])

            send_userid = self.user_access_info[room_name].pop(websocket, None)["userid"]

            # user가 나갔으면 해당 room에서 socket 지워주기
            wesocket_list = self.get_websocket_lists_from_dict(room_name)
            if websocket in wesocket_list:
                self.user_access_info[room_name].pop(websocket, None)

            if len(self.get_websocket_lists_from_dict(room_name)) == 0:
                logging.info(f"delete room - {room_name}")
                if self.user_access_info[room_name] != {}:
                    del self.user_access_info[room_name]
                if self.user_turn_count[room_name] != {}:
                    del self.user_turn_count[room_name]
                if self.recent_turn_user[room_name] != {}:
                    del self.recent_turn_user[room_name]
                if self.room_info[room_name] != {}:
                    del self.room_info[room_name]
                if limit_timer_task != {}:
                    logging.info(f"delete limit_timer - {limit_timer_task}")
                    limit_timer_task.cancel()
                    del self.limit_timer_task[room_name]
                if turn_timer_task != {}:
                    logging.info(f"delete turn_timer_task - {turn_timer_task}")
                    turn_timer_task.cancel()
                    del self.turn_timer_task[room_name]
                if self.ready_timer_task[room_name] != {}:
                    logging.info(f"delete ready_timer_task - {self.ready_timer_task[room_name]}")
                    self.ready_timer_task[room_name].cancel()
                    del self.ready_timer_task[room_name]
                if self.survival_timer_task[room_name] != {}:
                    logging.info(f"delete survival_timer_task - {self.survival_timer_task[room_name]}")
                    self.survival_timer_task[room_name].cancel()
                    del self.survival_timer_task[room_name]

            logging.info(f"CONNECTION REMOVED. REMAINING CONNECTIONS\n {self.get_websocket_lists_from_dict(room_name)}")

            return send_userid
        except Exception as exception:
            logging.exception(exception) 

    async def _notify(self, message: str, room_name: str):
        """자신의 채팅 다른사람에게 전달"""

         # 같은 방에 있는 사람에게 뿌려주기
        await self.send_to_room(room_name, message)


    async def _notCam(self, bytesimage: str, room_name: str):
        """자신의 캠 다른사람에게 전달"""

        # 같은 방에 있는 사람에게 뿌려주기
        await self.send_to_room(room_name, bytesimage)

    async def notify_user_info(self, info, room_name, userid, websocket):
        logging.info(f"{userid} join room {room_name}\n{info}")

        # 같은 방에 있는 사람에게 뿌려주기
        await self.send_to_room(room_name, info)

    async def delete_frame(self, room_name, send_userid):
        """유저가 나갔을 때 자기 캠 지우기"""
        self.update_user_access_info(room_name)

        json_object = {
            "type": "delete_frame",
            "userid": send_userid, 
        }
        json_object = json.dumps(json_object)

        # 같은 방에 있는 사람에게 뿌려주기
        await self.send_to_room(room_name, json_object)

    def update_user_access_info(self, room_name):
        """유저 정보 업데이트"""

        get_conn_list = self.get_websocket_lists_from_dict(room_name)
        for i in get_conn_list:
            if i.client_state.name != "CONNECTED":
                self.user_access_info[room_name].pop(i, None)
        logging.info(f"after update_user_access_info\n{ self.user_access_info[room_name] }")

    def get_user_turn(self, user_turn: json, room_name: str):
        """유저의 턴 정보 전달"""

        self.update_user_access_info(room_name)
        user_lists = self.get_userid_lists_from_dict(room_name)
        if(len(user_lists) <= 0):
            return ""

        if self.user_turn_count[room_name] >= len(user_lists):
            self.user_turn_count[room_name] = 0

        user_turn["userid"] = user_lists[self.user_turn_count[room_name]]
        user_turn["type"] = "send_user_turn"
        self.recent_turn_user[room_name] = user_turn["userid"]

        logging.info(f"this_turn - [{ room_name }] { user_lists[self.user_turn_count[room_name]] }")

        # client에 보내기 위해 json으로 변환
        user_turn = str(json.dumps(user_turn))
        return user_turn
    
    async def check_users(self, room_name):
        logging.info("checking users")
        for i in self.get_websocket_lists_from_dict(room_name):
            if i.client_state.name != "CONNECTED":
                send_userid = self.user_access_info[room_name].pop(i, None)
                await notifier.delete_frame(room_name, send_userid)


    async def game_server_request(self, room_name, path, method, params, websocket, game_mode=""):
        """게임서버 호출하여 데이터를 받아옴"""

        api_host = ""                                                                        # 서버 주소
        headers = {'Content-Type': 'application/json', 'charset': 'UTF-8', 'Accept': '*/*'}  # http 헤더
        url = ""                                                                             # 상세 경로
        body = params                                                                        # http body
        response = ""                                                                        # http response
        send_data = ""                                                                       # 보낼 데이터
        
        body["roomId"] = room_name

        # game_mode에 따른 url 설정
        if game_mode == "WordCard":
            api_host = "http://gameserver:7777/"
        else:
            api_host = "http://new_game:7778/"

        url = api_host + path

        # 경로에 따른 전달 값 설정
        send_data = self.set_game_server_send_data(game_mode, path, body, room_name)

        logging.info(f"url = { url }\ndata = { send_data }")

        # http method에 따른 처리
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, data = send_data)
            elif method == 'POST':
                #response = requests.post(url, headers=headers, data = send_data)
                response = await self.make_post_request(url, headers, send_data)

                if path == "check":
                    d = json.loads(response)
                    d["color_code"] = notifier.user_access_info[room_name][websocket]["color_code"]
                    response = json.dumps(d)

            logging.info(f"response - { response }")

            # 같은 방에 있는 사람에게 뿌려주기
            await self.send_to_room(room_name, response)

            # 새로운 게임은 init시 클라이언트에서는 할일이 없어서 init완료 시 바로 next요청
            if path == "init" and game_mode == "CoOpGame":
                self.turn_timer_task[room_name] = asyncio.create_task(self.send_next_word("POST", game_mode, body, headers, room_name, api_host, "next", websocket))

        except Exception as exception:
            await send_msg(exception)
            logging.exception(exception)

    async def make_post_request(self, url, headers, data):
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, data=data) as response:
                return await response.text()

    async def send_next_word(self, method, game_mode, body, headers, room_name, api_host, path, websocket):
        """서버에 뿌려줄 단어 매 틱 마다 요청 후 클라이언트에 전달"""
        response = ""
        url = api_host + path
        body["type"] = "next"
        send_data = self.set_game_server_send_data(game_mode, "next", body, room_name)
        status = "continue"
        start_time = time.time()

        tick_start = 1.7

        self.survival_timer_task[room_name] = asyncio.create_task(self.survival_timer(room_name))

        while status != "gameover" and self.room_info[room_name]["is_start"] == 1:
            # http method에 따른 처리
            try:
                if method == 'GET':
                    response = requests.get(url, headers=headers, data = send_data)
                elif method == 'POST':
                    response = requests.post(url, headers=headers, data = send_data)

                # next를 받아서 해당 틱마다 단어를 클라이언트에게 전달
                await self.send_to_room(room_name, response.text)
                logging.info(response.text)
                status = response.json()["status"]

                await asyncio.sleep(tick_start)

                tick_start = tick_start - 0.02 if tick_start > 0.5 else 0.5

            except Exception as exception:
                await send_msg(exception)
                logging.exception(exception)
        
        # 게임 끝났을 때 로직
        end_time = time.time()
        survival_time = int(end_time - start_time)
        params = { "type": "finish", "times": survival_time}
        await self.game_server_request(room_name, "finish", "POST", params, websocket, game_mode)
        self.delete_resource(room_name)

    def set_game_server_send_data(self, game_mode, path, body, room_name):
        """게임서버에 보낼 데이터 리턴"""

        send_data = ""
        if path == "init":
            user_lists = self.get_userid_lists_from_dict(room_name)
            body["users"] = user_lists
            body["size"] = self.board_size
            if game_mode == "CoOpGame":
                body["tick"] = self.new_game_tick
            send_data = json.dumps(body, ensure_ascii=False, indent="\t")
        elif path == "next":
            send_data = json.dumps(body, ensure_ascii=False, indent="\t")
        elif path == "check":
            if game_mode == "CoOpGame":
                send_data = json.dumps(body, ensure_ascii=False, indent="\t")
            elif game_mode == "WordCard":
                send_data = json.dumps(body, ensure_ascii=False, indent="\t").encode('utf-8')
        elif path == "finish":
            send_data = json.dumps(body, ensure_ascii=False, indent="\t")

        return send_data

    async def game_timer(self, room_name, userid, websocket):
        """게임 전체 1분 타이머"""

        count = self.game_time
        while count >= 0:
            if self.game_timer_stop[room_name] > 0:
                await asyncio.sleep(3)
                self.game_timer_stop[room_name] = 0

            json_object = {
                "type": "limit_time_start",
                "remain_time": count,
                "first_turn": userid, 
            }
            json_object = json.dumps(json_object)

            logging.info(f"{room_name} - Game_timer count: {count}")

            # 같은 방에 있는 사람에게 뿌려주기
            await self.send_to_room(room_name, json_object)

            count -= 1
            await asyncio.sleep(1)

        
        params = { "type": "finish", }
        await self.game_server_request(room_name, "finish", "POST", params, websocket, "WordCard")
        self.delete_resource(room_name)

    async def turn_timer(self, room_name, userid, remove_count = 0):
        """유저 전체 12초 타이머"""

        if self.limit_timer_task[room_name] == {}:
            self.turn_timer_task[room_name].cancel()

        # 단어를 1개 이상 지웠다면
        if remove_count > 0:
            self.game_timer_stop[room_name] = 1
            await asyncio.sleep(3)
            self.game_timer_stop[room_name] = 0

        count = self.turn_time
        while count >= 0:
            json_object = {
                "type": "turn_timer",
                "userid": userid,
                "remain_time": count, 
            }
            json_object = json.dumps(json_object)

            logging.info(f"{room_name} -> {userid} - User_timer count: {count}")

            # 같은 방에 있는 사람에게 뿌려주기
            await self.send_to_room(room_name, json_object)

            if count == 0:
                # 다음 턴 유저 아이디 설정
                self.update_user_access_info(room_name)
                user_lists = self.get_userid_lists_from_dict(room_name)
                self.user_turn_count[room_name] += 1
                if self.user_turn_count[room_name] >= len(user_lists):
                    self.user_turn_count[room_name] = 0

            count -= 1
            await asyncio.sleep(1)

    async def ready_timer(self, room_name, path, method, params, game_mode, websocket):
        count = self.ready_time

        while count >= 0:
            json_object = {
                "type": "ready_time",
                "ready_time": count, 
            }
            json_object = json.dumps(json_object)

            logging.info(f"{room_name} -> Ready_timer count: {count}")

            # 같은 방에 있는 사람에게 뿌려주기
            await self.send_to_room(room_name, json_object)

            count -= 1
            await asyncio.sleep(1)

        await self.game_server_request(room_name, path, method, params, websocket, game_mode)
        self.ready_timer_task[room_name].cancel()

    async def survival_timer(self, room_name):
        """협동게임 생존 시간 타이머"""

        count = 0

        while self.room_info[room_name]["is_start"] == 1:
            json_object = {
                "type": "survival_time",
                "survival_time": count, 
            }
            json_object = json.dumps(json_object)

            logging.info(f"{room_name} -> Survival_timer count: {count}")

            # 같은 방에 있는 사람에게 뿌려주기
            await self.send_to_room(room_name, json_object)

            count += 1
            await asyncio.sleep(1)

        self.survival_timer_task[room_name].cancel()

    def delete_resource(self, room_name):
        """게임 종료 시 필요없는 방 정보 삭제"""

        if self.limit_timer_task[room_name] != {}:
            self.limit_timer_task[room_name].cancel()
        if self.turn_timer_task[room_name] != {}:
            self.turn_timer_task[room_name].cancel()
        if self.ready_timer_task[room_name] != {}:
            self.ready_timer_task[room_name].cancel()
        if self.survival_timer_task[room_name] != {}:
            self.survival_timer_task[room_name].cancel()
        #self.room_info[room_name] = {}
        self.room_info[room_name]["is_start"] = 0
        #self.room_info[room_name]["game_mode"] = 0
        self.recent_turn_user[room_name] = {}
        self.turn_timer_task[room_name] = {}
        self.limit_timer_task[room_name] = {}
        self.game_timer_stop[room_name] = {}

    async def send_msg(self, msg):
        """슬랙으로 메시지 보내기"""

        url = "https://hooks.slack.com/services/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"
        message = (str(msg)) 
        title = (f"Error 발생 :zap:") # 타이틀 입력
        slack_data = {
            "username": "websockerServer", # 보내는 사람 이름
            "icon_emoji": ":satellite:",
            #"channel" : "#somerandomcahnnel",
            "attachments": [
                {
                    "color": "#9733EE",
                    "fields": [
                        {
                            "title": title,
                            "value": message,
                            "short": "false",
                        }
                    ]
                }
            ]
        }
        byte_length = str(sys.getsizeof(slack_data))
        headers = {'Content-Type': "application/json", 'Content-Length': byte_length}
        try:
            response = await self.make_post_request(url, headers, json.dumps(slack_data))
        except Exception as exception:
            logging.exception(exception)

    def get_websocket_lists_from_dict(self, room_name):
        """websocket 정보 가져오기"""

        user_ids = []
        inner_dict = self.user_access_info[room_name]
        for ws, info in inner_dict.items():
            user_ids.append(ws)
        return user_ids

    def get_userid_lists_from_dict(self, room_name):
        """유저 아이디 리스트 가져오기"""

        user_ids = []
        inner_dict = self.user_access_info[room_name]
        for ws, info in inner_dict.items():
            user_ids.append(info['userid'])
        return user_ids

def image_server_request(data):
        """이미지서버 호출하여 데이터를 받아옴"""
        url = "http://localhost:9999/"                                                  # 서버 주소
        headers = {'Content-Type': 'application/json', 'charset': 'UTF-8', 'Accept': '*/*'}  # http 헤더
        try:
            return requests.post(url, headers=headers, data=data)
        except Exception as exception:
            logging.exception(exception)

def get_color() -> str:
    from random import randint
    r, g, b = 0, 0, 0
    # get rgb code
    while True:
        r, g, b = (randint(45, 255) for _ in range(3))
        if r + g + b > 200:
            break
    # rgb to hex
    hex = "#{:02x}{:02x}{:02x}".format(r, g, b)
    return hex


notifier = Notifier()
@app.websocket("/ws/{room_name}")
async def websocket_endpoint(
    websocket: WebSocket, room_name, background_tasks: BackgroundTasks
):

    await notifier.connect(websocket, room_name)
    if notifier.room_info[room_name]["is_start"] == 1:
        logging.info(f"can't access in progress = {room_name}")
        go_back_data = {"type":"game_ing"} 
        go_back_data = json.dumps(go_back_data)
        await websocket.send_text(go_back_data)
    try:
        timer = ""
        await notifier.check_users(room_name)
        while True:
            data = await websocket.receive_text()
            d = json.loads(data)
            d["room_name"] = room_name

            if d["type"] == 'video':
                #data = image_server_request(data).text
                await notifier.send_video_to_room(room_name, f"{data}")
            elif d["type"] == "video_off":
                await notifier._notCam(f"{data}", room_name)
            elif d["type"] == "video_on":
                await notifier._notCam(f"{data}", room_name)
            elif d["type"] == "video_status":
                notifier.user_access_info[room_name][websocket]["video_status"] = d["video_status"]
            elif d["type"] == 'message':
                d["color_code"] = notifier.user_access_info[room_name][websocket]["color_code"]
                await notifier._notify(json.dumps(d), room_name)
            elif d["type"] == 'info':
                if notifier.room_info[room_name]["is_start"] == 1:
                    logging.info(f"can't access in progress = {room_name}")
                    go_back_data = {"type":"game_ing"} 
                    go_back_data = json.dumps(go_back_data)
                    await websocket.send_text(go_back_data)
                else:
                    # 유저 정보 설정
                    notifier.user_access_info[room_name][websocket]["userid"] = d["userid"]
                    notifier.user_access_info[room_name][websocket]["video_status"] = d["video_status"]
                    notifier.user_access_info[room_name][websocket]["color_code"] = get_color()

                    d["color_code"] = notifier.user_access_info[room_name][websocket]["color_code"]

                    if notifier.room_info[room_name]["game_mode"]:
                        d["game_mode"] = notifier.room_info[room_name]["game_mode"]
                    else:
                        d["game_mode"] = ""

                    await notifier.notify_user_info(json.dumps(d), room_name, d["userid"], websocket)
            elif d["type"] == 'send_user_turn':
                get_user_turn = notifier.get_user_turn(d, room_name)
                # 해당 room에 유저 턴 정보가 있다면
                if get_user_turn != "":
                    await notifier.send_to_room(room_name, get_user_turn)
            elif d["type"] == 'game_server':
                logging.info("go to call game_server")

                path = d["path"]
                method = d["method"]
                params = d["params"]
                game_mode = d["game_mode"]

                get_user_turn = notifier.get_user_turn(d, room_name)
                if get_user_turn != "":
                    if notifier.turn_timer_task[room_name] != {}:
                        if d["game_mode"] == "WordCard":
                            logging.info(f"delete {notifier.turn_timer_task[room_name]} in while game_server")
                            notifier.turn_timer_task[room_name].cancel()

                if path == "init":
                    # 처음 게임 시작 시 3초간 대기함
                    notifier.ready_timer_task[room_name] = asyncio.create_task(notifier.ready_timer(room_name, path, method, params, game_mode, websocket))
                else:
                    await notifier.game_server_request(room_name, path, method, params, websocket, game_mode)
            elif d["type"] == "game_start":
                notifier.user_turn_count[room_name] = 0
                notifier.room_info[room_name]["is_start"] = 1
                await notifier.send_to_room(room_name, f"{data}")
            elif d["type"] == "limit_time_start":
                # 전체 타이머 설정
                get_user_turn = notifier.get_user_turn(d, room_name)
                if get_user_turn != "":
                    if notifier.turn_timer_task[room_name] != {}:
                        logging.info(f"delete {notifier.turn_timer_task[room_name]} in while limit_time_start")
                        notifier.turn_timer_task[room_name].cancel()

                    notifier.update_user_access_info(room_name)
                    user_lists = notifier.get_userid_lists_from_dict(room_name)

                    notifier.game_timer_stop[room_name] = 0
                    notifier.limit_timer_task[room_name] = asyncio.create_task(notifier.game_timer(room_name, user_lists[notifier.user_turn_count[room_name]], websocket))
            elif d["type"] == "get_timer":
                get_user_turn = notifier.get_user_turn(d, room_name)
                if get_user_turn != "":
                    if notifier.turn_timer_task[room_name] != {}:
                        logging.info(f"delete {notifier.turn_timer_task[room_name]} in while get_timer")
                        notifier.turn_timer_task[room_name].cancel()
                    
                    notifier.update_user_access_info(room_name)
                    user_lists = notifier.get_userid_lists_from_dict(room_name)

                    # 다음 사람으로 유저 턴 변경
                    if d["next_user"] == "true":
                        notifier.user_turn_count[room_name] += 1
                        if notifier.user_turn_count[room_name] >= len(user_lists):
                            notifier.user_turn_count[room_name] = 0

                    # 턴을 가진 유저에게 턴 정보 전달
                    recent_turn_user = user_lists[notifier.user_turn_count[room_name]]
                    notifier.recent_turn_user[room_name] = recent_turn_user
                    if notifier.limit_timer_task[room_name] != {}:
                        notifier.turn_timer_task[room_name] = asyncio.create_task(notifier.turn_timer(room_name, recent_turn_user, d["remove_count"]))
            elif d["type"] == "change_game":
                notifier.room_info[room_name]["game_mode"] = d["game_mode"]
                await notifier.send_to_room(room_name, f"{data}")


    except WebSocketDisconnect:
        """소켓 연결이 끊어졌을 시"""
        logging.info(f"WebSocketDisconnect - {websocket}")
        # 연결정보 삭제
        get_user_id = notifier.remove(websocket, room_name, notifier.limit_timer_task[room_name], notifier.turn_timer_task[room_name])

        # 게임이 진행중이고 내 턴이 진행중일 때 연결이 끊어졌다면 남은 사람들에게 턴을 넘겨야 한다.
        notifier.update_user_access_info(room_name)
        user_lists = notifier.get_userid_lists_from_dict(room_name)

        if notifier.room_info[room_name]["is_start"] == 1 and get_user_id == notifier.recent_turn_user[room_name] :
            get_user_turn = notifier.get_user_turn(d, room_name)
            if get_user_turn != "":
                if notifier.turn_timer_task[room_name] != {}:
                    if notifier.room_info[room_name]["game_mode"] == "WordCard":
                        logging.info(f"delete {notifier.turn_timer_task[room_name]} in WebSocketDisconnect")
                        notifier.turn_timer_task[room_name].cancel()

                notifier.turn_timer_task[room_name] = asyncio.create_task(notifier.turn_timer(room_name, user_lists[notifier.user_turn_count[room_name]]))  

        # 연결이 끊어졌으니 내 비디오를 지우라고 전송
        await notifier.delete_frame(room_name, get_user_id)

@app.get("/sentry-debug")
async def trigger_error():
    division_by_zero = 1 / 0
