## imports
# request
from typing import Optional, List
from pydantic import BaseModel
# FastAPI
from fastapi import FastAPI, Query
app = FastAPI()
# game functions module
from gameFunctions import *


## origins
#allow
origins = [
    "*",
    # "http://localhost",
    # "http://localhost:8080",
]

# CORS
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


## main functions
# get dataBase
def getDataBase(fileName: str) -> dict:
    import os
    import json
    dirPath = os.path.dirname(os.path.realpath(__file__)) + "/"
    with open(dirPath + fileName, "r", encoding="utf8") as file:
        dataBase = json.load(file)
    return dataBase


## global variables
# declare and initialize variables
roomId:int = 0
wordData = dict()
wordTable = dict()
wordMap = dict()
height:int = 0
width:int = 0
# ML alternative
relData = dict()
# user data {user: score}
users = dict()


## response and request
# get room number
@app.get("/ws/{room_name}")
def create(room_name: int) -> None:
    global roomId

    roomId = room_name
    return


# request body: get method cannot have body
class RoomData(BaseModel):
    size: int
    users: list

# initialize game with new word table in size(height * width)
# TODO: modify url or to websocket
@app.post("/init")
def init(init: RoomData) -> dict:
    global wordData, wordTable, wordMap, height, width, users
    height, width = init.size, init.size
    SIZE = height * width
    EMPTY, START = "  ", 0
    wordData = getDataBase("wordDB.json")

    # initialize wordTable with empty cell
    for i in range(SIZE):
        wordTable[i] = EMPTY

    # initialize userData with score 0
    for user in init.users:
        users[user] = START

    wordTable = getWordTable(wordData, wordTable, height, width)
    wordMap = getWordMap(wordData, wordTable, wordMap, height, width)

    return wordTable

# # initialize game with new word table in size(height * width)
# # TODO: modify url or to websocket
# @app.get("/{roomId}/{size}")
# def init(size: int, userList: list = Query(...)) -> dict:
#     global wordData, wordTable, wordMap, height, width, users
#     height, width = size, size
#     SIZE = height * width
#     EMPTY, START = "  ", 0
#     wordData = getDataBase("wordDB.json")

#     # initialize wordTable with empty cell
#     for i in range(SIZE):
#         wordTable[i] = EMPTY

#     # initialize userData with score 0
#     for user in userList:
#         users[user] = START

#     wordTable = getWordTable(wordData, wordTable, height, width)
#     wordMap = getWordMap(wordData, wordTable, wordMap, height, width)

#     return wordTable


# check if answer word or relative words in word table
# request and response body
class Check(BaseModel):
    user: int
    answer: str
    removeWords: Optional[list] = None
    moveInfo: Optional[list] = None
    increment: Optional[int] = None

# if answer in word table, remove only the answer(includes duplicated)
# TODO: modify url or to websocket
@app.post("/"+str(roomId))
def check(checkInfo: Check) -> Check:
    global wordData, wordTable, wordMap, moveInfo, height, width, users

    # if the answer in word table, remove only the word(includes duplicated)
    answer = checkInfo.answer
    wordList = list(wordMap.keys())
    if answer in wordList:
        checkInfo.removeWords = list(answer)
    # check if relative words in word table
    else:
        # get relative words
        # TODO: substitute to get from ML directly
        relData = getDataBase("ML.json")
        # relative words in word table
        relWords = relData.get(answer, "").split(",")
        checkInfo.removeWords = list(word for word in relWords if word in wordList and word)
    # update
    wordTable, wordMap, checkInfo.moveInfo \
        = updateWordTable(wordData, wordTable, wordMap, checkInfo.removeWords, height, width)
    checkInfo.increment = len(checkInfo.removeWords)

    return checkInfo
