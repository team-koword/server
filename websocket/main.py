import json
from collections import defaultdict

from fastapi import FastAPI, WebSocket, BackgroundTasks
from starlette.websockets import WebSocketDisconnect
from starlette.middleware.cors import CORSMiddleware
import requests
import asyncio


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Notifier:
    """
        Manages chat room sessions and members along with message routing
    """

    def __init__(self):
        self.connections: dict = defaultdict(dict)          # 기본 연결 정보
        self.generator = self.get_notification_generator()
        self.user_access_info: dict = defaultdict(dict)     # 현재 접속중인 소켓 정보
        self.user_turn_count: dict = defaultdict(dict)      # user_access_info의 인덱스: 순서대로 접근하기 위해 선언한 변수
        self.room_game_start: dict = defaultdict(dict)      # 현재 방이 게임 진행중인지 여부 - [0: 대기중, 1: 진행중]
        self.recent_turn_user: dict = defaultdict(dict)     # 현재 턴인 유저의 정보
        self.board_size = 11                                # game_board size
        self.turn_timer_task: dict = defaultdict(dict)      # 비동기로 실행할 매 턴 타이머
        self.limit_timer_task: dict = defaultdict(dict)     # 비동기로 실행할 게임 제한 시간 타이머
        self.game_time = 60                                 # 게임 제한 시간(초)
        self.turn_time = 7                                  # 유저 별 턴 시간(초)

    async def get_notification_generator(self):
        while True:
            message = yield
            msg = message["message"]
            room_name = message["room_name"]
            await self._notify(msg, room_name)

    def get_members(self, room_name):
        """해당 room에 있는 소켓 구하기"""
        # living_conn = []
        # for i in self.connections[room_name]:
        #     print(i)
        #     #i = json.loads(i)
        #     print(i.client_state.name)
        #     print("--21312312312312")
        #     if i.client_state.name == "CONNECTED":
        #         living_conn.append(i)
        #         print("asdasdasd")
        # print(living_conn)
        try:
            #living_conn = []
            # for i in self.connections[room_name]:
            #     i = json.dumps(i)
            #     print(i.client_state.name)
            #     print("--21312312312312")
            #     if i.client_state.name == "CONNECTED":
            #         living_conn.append(i)
            #return self.connections[room_name]
            # living_conn = []
            # for i in self.connections[room_name]:
            #     #print(i)
            #     if i.client_state.name == "CONNECTED":
            #         living_conn.append(i)
            # #print(living_conn)
            return self.connections[room_name]
        except Exception:
            return None

    async def push(self, msg: str, room_name: str = None):
        message_body = {"message": msg, "room_name": room_name}
        await self.generator.asend(message_body)

    async def send_to_room(self, room_name, send_info):
        """같은 방에 있는 사람에게 뿌려주기"""
        try:
            living_connections = []
            while len(self.connections[room_name]) > 0:
                websocket = self.connections[room_name].pop()
                if websocket.client_state.name == "CONNECTED":
                    await websocket.send_text(send_info)
                    living_connections.append(websocket)
                else:
                    print(websocket)
            self.connections[room_name] = living_connections
        except Exception as exception:
            print("예외는 ", exception)
        

    async def connect(self, websocket: WebSocket, room_name: str):
        """웹소켓 연결 설정"""

        await websocket.accept()
        if self.connections[room_name] == {} or len(self.connections[room_name]) == 0:
            self.connections[room_name] = []
        self.connections[room_name].append(websocket)

        print(f"CONNECTIONS : {self.connections[room_name]}")

   
    def remove(self, websocket: WebSocket, room_name: str, limit_timer_task, turn_timer_task):
        """방에서 퇴장한 user 정보 설정"""
        try:
            # 기존 딕셔너리에서 user_name 가져오고 해당 키 삭제. 이후 클라이언트로 user_name 전달
            # 이것은 턴을 위한 유저 정보
            send_userid = self.user_access_info[room_name].pop(websocket, None)

            # user가 나갔으면 해당 room에서 socket 지워주기
            if websocket in self.connections[room_name]:
                self.connections[room_name].remove(websocket)

            print("이건 뭐야 정말로 ", self.connections[room_name])
            if len(self.connections[room_name]) == 0:
                print("이 방은 지웁니다.", room_name)
                del self.user_access_info[room_name]
                del self.user_turn_count[room_name]
                del self.recent_turn_user[room_name]
                del self.room_game_start[room_name]
                if limit_timer_task != {}:
                    print("전체타이머 지운다~~~~~~")
                    limit_timer_task.cancel()
                print("여기서는 뭐야대체", turn_timer_task)
                if turn_timer_task != {}:
                    print("유저 턴 타이머 지운다~~~~~~")
                    turn_timer_task.cancel()

            print(send_userid)

            print(
                f"CONNECTION REMOVED\nREMAINING CONNECTIONS : {self.connections[room_name]}"
            )

            return send_userid
        except Exception as exception:
            print(exception) 

    async def _notify(self, message: str, room_name: str):
        """자신의 채팅 다른사람에게 전달"""

         # 같은 방에 있는 사람에게 뿌려주기
        await self.send_to_room(room_name, message)


    async def _notCam(self, bytesimage: str, room_name: str):
        """자신의 캠 다른사람에게 전달"""

        # 같은 방에 있는 사람에게 뿌려주기
        await self.send_to_room(room_name, bytesimage)

    async def insert_user_access_info(self, info, room_name, userid, websocket):
        print(userid)
        # 들어왔으니 그려라
        print("들어와라", websocket)
        print(info)

        # 같은 방에 있는 사람에게 뿌려주기
        await self.send_to_room(room_name, info)

    async def delete_frame(self, room_name, send_userid):
        """유저가 나갔을 때 자기 캠 지우기"""
        self.update_user_access_info(room_name)
        print("캠 지워주세요", send_userid)

        json_object = {
            "type": "delete_frame",
            "userid": send_userid, 
        }
        json_object = json.dumps(json_object)

        # 같은 방에 있는 사람에게 뿌려주기
        await self.send_to_room(room_name, json_object)

    def update_user_access_info(self, room_name):
        # 이번 턴 유저 아이디 설정
        get_conn_list = self.get_members(room_name)
        for i in get_conn_list:
            if i.client_state.name != "CONNECTED":
                self.connections[room_name].remove(i)
                self.user_access_info[room_name].pop(i, None)
        print("업데이트 후 남아있는건", self.user_access_info[room_name])

    def get_user_turn(self, user_turn: json, room_name: str):
        """유저의 턴 정보 전달"""

        print(self.user_access_info[room_name])
        self.update_user_access_info(room_name)
        user_lists = list(self.user_access_info[room_name].values())
        if(len(user_lists) <= 0):
            return ""

        if self.user_turn_count[room_name] >= len(user_lists):
            self.user_turn_count[room_name] = 0

        print("이번 유저는 ", self.user_turn_count[room_name], user_lists)

        user_turn["userid"] = user_lists[self.user_turn_count[room_name]]
        user_turn["type"] = "send_user_turn"
        self.recent_turn_user[room_name] = user_turn["userid"]
        print("유저 턴 줍니다~~~~~~~.", user_lists[self.user_turn_count[room_name]])
        

        # # 다음 턴 유저 아이디 설정
        # self.user_turn_count[room_name] += 1
        # if self.user_turn_count[room_name] >= len(user_lists):
        #     self.user_turn_count[room_name] = 0

        # client에 보내기 위해 json으로 변환
        user_turn = str(json.dumps(user_turn))
        return user_turn
    
    async def check_users(self, room_name):
        for i in self.connections[room_name]:
            if i.client_state.name != "CONNECTED":
                self.connections[room_name].remove(i)
                send_userid = self.user_access_info[room_name].pop(i, None)
                print("지워라", send_userid)
                await notifier.delete_frame(room_name, send_userid)


    async def game_server_request(self, room_name, path, method, params):
        """게임서버 호출하여 데이터를 받아옴"""
        print(room_name, path, method)

        api_host = "http://localhost:7777/"                                                  # 서버 주소
        headers = {'Content-Type': 'application/json', 'charset': 'UTF-8', 'Accept': '*/*'}  # http 헤더
        url = api_host + path                                                                # 상세 경로
        body = params                                                                        # http body
        response = ""                                                                        # http response
        user_lists = []                                                                      # 해당 room에 있는 user list
        send_data = ""                                                                       # 보낼 데이터
        
        body["roomId"] = room_name
        # 경로에 따른 전달 값 설정
        if path == "check":
            send_data = json.dumps(body, ensure_ascii=False, indent="\t").encode('utf-8')
        elif path == "init":
            #self.update_user_access_info(room_name)
            user_lists = list(self.user_access_info[room_name].values())
            body["users"] = user_lists
            body["size"] = self.board_size
            send_data = json.dumps(body, ensure_ascii=False, indent="\t")

        print(url)
        print(send_data)
        print("구분선====================")

        # http method에 따른 처리
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, data = send_data)
            elif method == 'POST':
                response = requests.post(url, headers=headers, data = send_data)
            
            print(response.text)
            
            # 같은 방에 있는 사람에게 뿌려주기
            await self.send_to_room(room_name, response.text)

        except Exception as exception:
            print(exception)

    async def game_timer(self, room_name, userid):
        """게임 전체 1분 타이머"""

        count = self.game_time
        while count >= 0:
            json_object = {
                "type": "limit_time_start",
                "remain_time": count,
                "first_turn": userid, 
            }
            json_object = json.dumps(json_object)

            print(f"{room_name} - Game_timer count: {count}")

            # 같은 방에 있는 사람에게 뿌려주기
            await self.send_to_room(room_name, json_object)

            count -= 1
            await asyncio.sleep(1)

    async def turn_timer(self, room_name, userid):
        """유저 전체 7초 타이머"""

        count = self.turn_time
        while count >= 0:
            json_object = {
                "type": "turn_timer",
                "userid": userid,
                "remain_time": count, 
            }
            json_object = json.dumps(json_object)

            print(f"{room_name} -> {userid} - User_timer count: {count}")

            # 같은 방에 있는 사람에게 뿌려주기
            await self.send_to_room(room_name, json_object)

            if count == 0:
                # 다음 턴 유저 아이디 설정
                self.update_user_access_info(room_name)
                user_lists = list(self.user_access_info[room_name].values())
                self.user_turn_count[room_name] += 1
                if self.user_turn_count[room_name] >= len(user_lists):
                    self.user_turn_count[room_name] = 0

            count -= 1
            await asyncio.sleep(1)

notifier = Notifier()
@app.websocket("/ws/{room_name}")
async def websocket_endpoint(
    websocket: WebSocket, room_name, background_tasks: BackgroundTasks
):
    
    print()
    print()
    print()
    print("in websocket")
    #print(websocket.client_state.name)
    await notifier.connect(websocket, room_name)
    if notifier.room_game_start[room_name] == 1:
        print("진행중인 방은 접근 불가. 방이름은 = ", room_name)
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
            room_members = (notifier.get_members(room_name) if notifier.get_members(room_name) is not None else [])

            # if websocket not in room_members:
            #     print("USER NOT IN ROOM MEMBERS: RECONNECTING")
            #     print("업슨ㄴ 웹소켓은  ",websocket)
            #     print("룸멤버는  ",room_members)
            #     await notifier.connect(websocket, room_name)
            #     notifier.user_access_info[room_name][websocket] = d["userid"]
            #     await notifier.insert_user_access_info(f"{data}", room_name, d["userid"], websocket)
            #     # 게임보드 보내고
            #     # 게임 시작 버튼 제거하고
            #     await notifier.send_to_room(room_name, f"{data}")

            if d["type"] == 'video':
                await notifier._notCam(f"{data}", room_name)
            elif d["type"] == 'message':
                await notifier._notify(f"{data}", room_name)
            elif d["type"] == 'info':
                notifier.user_access_info[room_name][websocket] = d["userid"]
                print(notifier.user_access_info[room_name])
                await notifier.insert_user_access_info(f"{data}", room_name, d["userid"], websocket)
            elif d["type"] == 'send_user_turn':
                get_user_turn = notifier.get_user_turn(d, room_name)
                if get_user_turn != "":
                    await notifier.send_to_room(room_name, get_user_turn)
            elif d["type"] == 'game_server':
                print("게임서버 호출하러 갑니다.")
                path = d["path"]
                method = d["method"]
                params = d["params"]
                get_user_turn = notifier.get_user_turn(d, room_name)
                if get_user_turn != "":
                    if notifier.turn_timer_task[room_name] != {}:
                        print("game_server에서 notifier.turn_timer_task[room_name] 삭제")
                        notifier.turn_timer_task[room_name].cancel()
                await notifier.game_server_request(room_name, path, method, params)
            elif d["type"] == "game_start":
                print("게임시작하니 버튼 지워주세요.")
                notifier.user_turn_count[room_name] = 0
                notifier.room_game_start[room_name] = 1
                await notifier.send_to_room(room_name, f"{data}")
            elif d["type"] == "limit_time_start":
                print("전체타이머")
                # 전체 타이머 설정
                get_user_turn = notifier.get_user_turn(d, room_name)
                if get_user_turn != "":
                    if notifier.turn_timer_task[room_name] != {}:
                        print("limit_time_start notifier.turn_timer_task[room_name] 삭제")
                        notifier.turn_timer_task[room_name].cancel()

                    notifier.update_user_access_info(room_name)
                    user_lists = list(notifier.user_access_info[room_name].values())

                    notifier.limit_timer_task[room_name] = asyncio.create_task(notifier.game_timer(room_name, user_lists[notifier.user_turn_count[room_name]]))
            elif d["type"] == "get_timer":
                get_user_turn = notifier.get_user_turn(d, room_name)
                if get_user_turn != "":
                    if notifier.turn_timer_task[room_name] != {}:
                        print(notifier.turn_timer_task[room_name])
                        print("get_timer에서 notifier.turn_timer_task[room_name] 삭제")
                        notifier.turn_timer_task[room_name].cancel()
                    
                    notifier.update_user_access_info(room_name)
                    user_lists = list(notifier.user_access_info[room_name].values())

                    if d["next_user"] == "true":
                        notifier.user_turn_count[room_name] += 1
                        if notifier.user_turn_count[room_name] >= len(user_lists):
                            notifier.user_turn_count[room_name] = 0

                    recent_turn_user = user_lists[notifier.user_turn_count[room_name]]
                    notifier.recent_turn_user[room_name] = recent_turn_user
                    notifier.turn_timer_task[room_name] = asyncio.create_task(notifier.turn_timer(room_name, recent_turn_user))     


    except WebSocketDisconnect:
        """소켓 연결이 끊어졌을 시"""
        print("WebSocketDisconnect~~~~~~~~~~~~~~~~~~~~~~~~")
        # 연결정보 삭제
        get_user_id = notifier.remove(websocket, room_name, notifier.limit_timer_task[room_name], notifier.turn_timer_task[room_name])

        # 게임이 진행중이고 내 턴이 진행중일 때 연결이 끊어졌다면 남은 사람들에게 턴을 넘겨야 한다.
        notifier.update_user_access_info(room_name)
        user_lists = list(notifier.user_access_info[room_name].values())
        if notifier.room_game_start[room_name] == 1 and get_user_id == notifier.recent_turn_user[room_name] :
            print("여기부터11111111")
            get_user_turn = notifier.get_user_turn(d, room_name)
            print("여기부터22222222")
            if get_user_turn != "":
                print("여기부터333333")
                if notifier.turn_timer_task[room_name] != {}:
                    print("여기부터444444")
                    print(notifier.turn_timer_task[room_name])
                    print("WebSocketDisconnect에서 notifier.turn_timer_task[room_name] 삭제")
                    notifier.turn_timer_task[room_name].cancel()

                
                notifier.turn_timer_task[room_name] = asyncio.create_task(notifier.turn_timer(room_name, user_lists[notifier.user_turn_count[room_name]]))   
        # 다시 참여 하러면 게임보드 보내줘야함
        # 또한 게임시작 버튼 지워야 한다.

        # 연결이 끊어졌으니 내 비디오를 지우라고 전송
        await notifier.delete_frame(room_name, get_user_id)
        #await websocket.close()
