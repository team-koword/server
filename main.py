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
print("start to load model")
start = time.time()

import fasttext
try:
    simModel = fasttext.load_model('./model.bin')
    print("load model success")
except:
    print("load model failed")

end = time.time()
print(f"model loaded in {end - start} secs")


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


# request and response body
class InitBody(BaseModel):
    type: str
    roomId: str
    size: int
    users: list
    wordTable: Optional[dict] = None
# initialize game with new word table in size(height * width)
@app.post("/init")
def init(Init: InitBody) -> dict:
    print("start to initialize game")
    start = time.time()

    # get room data and initialize
    global Rooms
    Room = Rooms[Init.roomId]
    Room.roundCnt = 0
    Room.height, Room.width = Init.size, Init.size
    SIZE = Room.height * Room.width
    EMPTY, START = "  ", 0
    Room.wordData = dataBase

    # initialize wordTable with empty cell
    for i in range(SIZE):
        Room.wordTable[i] = EMPTY

    # initialize userData with score 0
    for user in Init.users:
        Room.users[user] = START

    # get word table and word map
    Room.wordTable = getWordTable(Room.wordData, Room.wordTable, 
                                  Room.height, Room.width)
    Room.wordMap = getWordMap(Room.wordData, Room.wordTable, Room.wordMap, 
                              Room.height, Room.width)

    # put word table in response body
    Init.wordTable = Room.wordTable

    # print at terminal(for test)
    print(f"round start: {Room.roundCnt}")
    printWordTable(Room.wordTable, Room.height, Room.width)
    print(f"words: {len(list(Room.wordMap.keys()))}")

    end = time.time()
    print(f"game initialized in {end - start} secs")

    return Init


# check if answer word or similar words in word table
# request and response body
class CheckBody(BaseModel):
    type: str
    roomId: str
    user: str
    answer: str
    removeWords: Optional[list] = None
    mostSim: Optional[int] = None
    moveInfo: Optional[list] = None
    increment: Optional[int] = None
# if answer in word table, remove only the answer(includes duplicated)
@app.post("/check")
def check(Check: CheckBody) -> CheckBody:
    print("start to check answer")
    start = time.time()

    # get room data
    global Rooms
    Room = Rooms[Check.roomId]
    Room.roundCnt += 1

    # get data to check
    answer = Check.answer
    wordList = list(Room.wordMap.keys())

    # if the answer in word table, remove only the word(includes duplicated)
    if answer in wordList:
        Check.removeWords = [answer]
        Check.mostSim = 1
    # get similar words in word table
    else:
        Check.removeWords, Check.mostSim \
            = getSimWords(simModel, wordList, answer)

    # update room data
    Room.wordTable, Room.wordMap, Check.moveInfo \
        = updateWordTable(Room.wordData, Room.wordTable, Room.wordMap, 
                          Check.removeWords, Room.height, Room.width)

    # update score
    increment = len(Check.removeWords)
    Room.users[Check.user] += increment
    Check.increment = increment

    # print at terminal(for test)
    print(f"roundCnt: {Room.roundCnt}")
    print(f"user: {Check.user}, answer: {Check.answer}")
    print(f"removeNums: {len(Check.removeWords)}, mostSim: {Check.mostSim}")
    printWordTable(Room.wordTable, Room.height, Room.width)
    print(f"remain words: {len(list(Room.wordMap.keys()))}")

    end = time.time()
    print(f"answer checked in {end - start} secs")

    return Check
