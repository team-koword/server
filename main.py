## for test
# start server
print("SERVER STARTED")

# test run-time
import time

## words data
# get json file function
def get_json(fileName: str) -> dict:
    import os
    import json
    dirPath = os.path.dirname(os.path.realpath(__file__)) + "/"
    with open(dirPath + fileName, "r", encoding="utf8") as file:
        json_file = json.load(file)
    return json_file


# get json data
print("STARTING SERVER: start to get json data")
start = time.time()

try:
    ToPut = get_json("to_put.json")
    ToFind = get_json("to_find.json")
    print("SUCCESS TO LOAD JSON DATA")
except Exception as err:
    print(f"FAIL TO LOAD JSON DATA: {err}")

end = time.time()
print(f"STARTING SERVER: got json data in {end - start} secs")


# get vector similarity model
print("STARTING SERVER: start to load fasttext model")
start = time.time()

import fasttext
try:
    simModel = fasttext.load_model('./model.bin')
    print("SUCCESS TO LOAD FASTTEXT MODEL")
except Exception as err:
    print(f"FAIL TO LOAD FASTTEXT MODEL: {err}")

end = time.time()
print(f"STARTING SERVER: fasttext model loaded in {end - start} secs")
print("SERVER IS READY TO RUN GAMES")


# modeling functions module
from modeling import *




## game data
from collections import defaultdict
# each room data
class RoomData:
    def __init__(self) -> None:
        self.roomId: str = ""
        self.wordTable = defaultdict(lambda: "  ") # {loc: char, ...}
        self.wordMap = defaultdict(list)   # {word: [loc, ...], ...}
        self.height: int = 0
        self.width: int = 0
        self.users = defaultdict(int)     # {user: score, ...}
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
            # DIGIT = len(str(height * width))
            # cell = str(loc).zfill(DIGIT) + cell
            print(cell, end=" ")
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
    print("GAME START: game initializing")
    start = time.time()

    # get room data and initialize
    global Rooms, ToPut, ToFind
    Room = Rooms[Init.roomId]
    Room.roundCnt = 0
    Room.height, Room.width = Init.size, Init.size
    START = 0

    # initialize wordTable
    Room.wordTable = initWordTable(Room.wordTable, Room.height, Room.width)

    # initialize userData with score 0
    for user in Init.users:
        Room.users[user] = START

    # get word table and word map
    Room.wordTable = getWordTable(ToPut, Room.wordTable, 
                                  Room.height, Room.width)
    Room.wordMap = getWordMap(ToFind, Room.wordTable, Room.wordMap, 
                              Room.height, Room.width)

    # put word table in response body
    Init.wordTable = Room.wordTable

    # # print at terminal(for test)
    # printWordTable(Room.wordTable, Room.height, Room.width)

    end = time.time()
    print(f"GAME START: game initialized in {end - start} secs")
    print(f"GAME START: round start: {Room.roundCnt}")
    print(f"GAME START: words in table: {len(list(Room.wordMap.keys()))}")

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
    print("GAME RUNNING: start to check answer")
    start = time.time()

    # get room data
    global Rooms, ToPut, ToFind
    Room = Rooms[Check.roomId]
    Room.roundCnt += 1

    # get data to check
    answer = Check.answer
    wordList = list(Room.wordMap.keys())

    # if the answer in word table, remove only the word(includes duplicated)
    if answer in wordList:
        Check.removeWords = [answer]
        Check.mostSim = 100
    # get similar words in word table
    else:
        Check.removeWords, Check.mostSim \
            = getSimWords(simModel, wordList, answer)
    
    # update room data
    Room.wordTable, Room.wordMap, Check.moveInfo \
        = updateWordTable(ToPut, ToFind, Room.wordTable, Room.wordMap, 
                          Check.removeWords, Room.height, Room.width)

    # update score
    increment = len(Check.removeWords)
    Room.users[Check.user] += increment
    Check.increment = increment

    # renew word table if words in table less than standard count
    MIN = 30
    # set moveInfo for all cells -> empty
    if len(list(Room.wordMap.keys())) < MIN:
        SIZE = Room.height * Room.width
        Check.moveInfo = list()
        for loc in range(SIZE - 1, -1, -1):
            Check.moveInfo.append([loc, SIZE, Room.wordTable[loc]])
        # initWordTable
        Room.wordTable = initWordTable(Room.wordTable, Room.height, Room.width)
        # get word table and word map
        Room.wordTable, Check.moveInfo = getWordTable(ToPut, Room.wordTable, 
                                                      Room.height, Room.width, 
                                                      Check.moveInfo)
        Room.wordMap = getWordMap(ToFind, Room.wordTable, Room.wordMap, 
                                  Room.height, Room.width)
        print("GAME REFRESHED: table renewed")

    # # print at terminal(for test)
    # printWordTable(Room.wordTable, Room.height, Room.width)

    end = time.time()
    print(f"GAME RUNNING: answer checked in {end - start} secs")
    print(f"GAME RUNNING: round now: {Room.roundCnt}")
    print(f"GAME RUNNING: user: {Check.user}, answer: {Check.answer}")
    print(f"GAME RUNNING: removed words: {len(Check.removeWords)}, mostSim: {Check.mostSim}")
    print(f"GAME RUNNING: words in table: {len(list(Room.wordMap.keys()))}")

    return Check
