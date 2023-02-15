## words data
# dataBase
import os
import json
dirPath = os.path.dirname(os.path.realpath(__file__)) + "/"
fileName = './wordDB.json'
with open(dirPath + fileName, "r", encoding="utf8") as file:
    dataBase = json.load(file)


# vector similarity model
import time
print("start to get model")
start = time.time()

import fasttext
simModel = fasttext.load_model('./model.bin')

end = time.time()
print(f"got model in {end - start} secs")


# modeling functions module
from modeling import *




## game data
# each room data
from collections import defaultdict
class RoomData:
    def __init__(self) -> None:
        self.roomId: str = ""
        self.wordData = dict()   # {char: {len: "word1,word2,...", ...}, ...}
        self.wordTable = dict()  # {loc: char, ...}
        self.wordMap = dict()    # {word: [loc, ...], ...}
        self.height: int = 0
        self.width: int = 0
        self.users = dict()      # {user: score, ...}
        self.roundCnt: int = -1


# rooms data
Rooms = defaultdict(RoomData)


# game functions module
from gameFunctions import *


# print wordTable in Terminal
def printWordTable(wordTable: dict, height: int, width: int) -> None:
    for col in range(height):
        for row in range(width):
            loc = col * width + row
            cell = wordTable[loc]
            # # print location
            # cell = str(loc).zfill(3) + cell
            print(cell, end=" ")
        print()
    print()




## response and request
# FastAPI
from fastapi import FastAPI, Query
app = FastAPI()


# CORS
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# origins
origins = [
    "*",
    # "http://localhost",
    # "http://localhost:8080",
]


# request
from typing import Optional, List
from pydantic import BaseModel


# request body
class InitReq(BaseModel):
    roomId: str
    size: int
    users: list
# initialize game with new word table in size(height * width)
# TODO: modify url
@app.post("/init")
def init(Init: InitReq) -> dict:
    print("start to init game")
    start = time.time()

    global Rooms
    room = Rooms[Init.roomId]
    room.height, room.width = Init.size, Init.size
    SIZE = room.height * room.width
    EMPTY, START = "  ", 0
    room.wordData = dataBase
    room.roundCnt = 0

    # initialize wordTable with empty cell
    for i in range(SIZE):
        room.wordTable[i] = EMPTY

    # initialize userData with score 0
    for user in Init.users:
        room.users[user] = START

    room.wordTable = getWordTable(room.wordData, room.wordTable, 
                                  room.height, room.width)
    room.wordMap = getWordMap(room.wordData, room.wordTable, room.wordMap, 
                              room.height, room.width)

    print(f"round start: {room.roundCnt}")
    printWordTable(room.wordTable, room.height, room.width)
    print(f"words: {len(list(room.wordMap.keys()))}")

    end = time.time()
    print(f"game started in {end - start} secs")

    return room.wordTable


# check if answer word or similar words in word table
# request and response body
class CheckReq(BaseModel):
    roomId: str
    user: str
    answer: str
    removeWords: Optional[list] = None
    mostSim: Optional[float] = None
    moveInfo: Optional[list] = None
    increment: Optional[int] = None
# if answer in word table, remove only the answer(includes duplicated)
# TODO: modify url
@app.post("/check")
def check(Check: CheckReq) -> CheckReq:
    print("start to check")
    start = time.time()

    global Rooms
    room = Rooms[Check.roomId]

    answer = Check.answer
    wordList = list(room.wordMap.keys())
    # if the answer in word table, remove only the word(includes duplicated)
    if answer in wordList:
        Check.removeWords = [answer]
        Check.mostSim = 1
    # get similar words in word table
    else:
        Check.removeWords, Check.mostSim \
            = getSimWords(simModel, wordList, answer)
    # update
    room.wordTable, room.wordMap, Check.moveInfo \
        = updateWordTable(room.wordData, room.wordTable, room.wordMap, 
                          Check.removeWords, room.height, room.width)
    Check.increment = len(Check.removeWords)

    room.roundCnt += 1
    print(f"roundCnt: {room.roundCnt}")
    print(f"removeNums: {len(Check.removeWords)}, mostSim: {Check.mostSim}")
    printWordTable(room.wordTable, room.height, room.width)
    print(f"remain words: {len(list(room.wordMap.keys()))}")

    end = time.time()
    print(f"answer checked in {end - start} secs")

    return Check
