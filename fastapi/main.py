from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import Union, List
import numpy as np
from fastapi import (
    Cookie,
    Depends,
    FastAPI,
    Query,
    WebSocket,
    WebSocketException,
    status,
)
from fastapi.responses import StreamingResponse
import base64
import io
import cv2
from imageio.v2 import imread
from PIL import Image

image_dict = {}


def readb64(uri, w, h):
    nparr = np.fromstring(base64.b64decode(uri), np.uint8)
    img = cv2.resize(cv2.imdecode(nparr, cv2.IMREAD_COLOR), (w, h))
    return img


html = """
<!DOCTYPE html>
<html lang="ko">
<html>
    <head>
        <title>Chat</title>

    </head>
    <body>
        <h1>WebSocket Chat</h1>
        <h2>Your ID: <span id="ws-id"></span></h2>
        <form action="" onsubmit="sendMessage(event)">
            <input type="text" id="messageText" autocomplete="off"/>
            <button>Send</button>
        </form>
        <ul id='messages'>
        </ul>
        <script>
            var client_id = Date.now()
            document.querySelector("#ws-id").textContent = client_id;
            var ws = new WebSocket(`wss://webdev-test.site/api/ws/${client_id}`);
            ws.onmessage = function(event) {
                var messages = document.getElementById('messages')
                var message = document.createElement('li')
                var content = document.createTextNode(event.data)
                message.appendChild(content)
                messages.appendChild(message)
            };
            function sendMessage(event) {
                var input = document.getElementById("messageText")
                ws.send(input.value)
                input.value = ''
                event.preventDefault()
            }
        </script>
    </body>
</html>
"""


def streamCamera():
    cam = cv2.VideoCapture(0)
    while True:
        retVal, mat = cam.read()
        if not retVal:
            break

        retVal, jpgImg = cv2.imencode(".jpg", mat)
        jpgBin = bytearray(jpgImg.tobytes())

        yield (b"--PNPframe\r\n" b"Content-Type: image/jpeg\r\n\r\n" + jpgBin + b"\r\n")


app = FastAPI()


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)


manager = ConnectionManager()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def get():
    return {"message": "Here is test"}


@app.get("/api/index")
async def get():
    return HTMLResponse(html)


@app.get("/api/message")
async def root():
    return {"message": "응 너무 쉽구요 "}


@app.get("/api/video")
async def video():
    return StreamingResponse(streamCamera(), media_type="multipart/x-mixed-replace; boundary=PNPframe")


async def get_cookie_or_token(
    websocket: WebSocket,
    session: Union[str, None] = Cookie(default=None),
    token: Union[str, None] = Query(default=None),
):
    if session is None and token is None:
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)
    return session or token


def dataToArray(data):
    head, file = data.split(",")
    img = imread(io.BytesIO(base64.b64decode(file)))
    img = cv2.resize(img, (200, 200))
    img = np.array(img, dtype="uint8")
    return img, head


@app.websocket("/api/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: int):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            image_dict[client_id] = data

            keys = sorted(image_dict.keys())
            L = len(keys)
            bg = np.zeros((200 * L, 200, 3), dtype="uint8")

            for idx in range(L):
                data = image_dict[keys[idx]]
                img, head = dataToArray(data)
                for c in range(3):
                    bg[200 * idx : 200 * (idx + 1), 0:200, c] = img[0:200, 0:200, c]

            pil_img = Image.fromarray(bg)
            buff = io.BytesIO()
            pil_img.save(buff, format="JPEG")
            new_image_string = base64.b64encode(buff.getvalue()).decode("utf-8")
            cast = head + "," + new_image_string
            await manager.broadcast(f"{cast}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        try:
            del image_dict[client_id]
            await manager.broadcast(f"Client #{client_id} left the chat")
        except:
            pass
