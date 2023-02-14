## words data
# dataBase
import os
import json
dirPath = os.path.dirname(os.path.realpath(__file__)) + "/"
fileName = './wordDB.json'
with open(dirPath + fileName, "r", encoding="utf8") as file:
    dataBase = json.load(file)


# vector similarity model
import fasttext
simModel = fasttext.load_model('./model.bin')


# modeling functions module
from modeling import *




## game data
# game variables
wordData = dict()   # {char: {len: "word1,word2,...", ...}, ...}
wordTable = dict()  # {loc: char, ...}
wordMap = dict()    # {word: [loc, ...], ...}
height:int = 0
width:int = 0
roomId:int = 0
users = dict()      # {user: score, ...}


# game functions module
from gameFunctions import *


# print wordTable in Terminal
def printWordTable(wordTable: dict, height: int, width: int) -> None:
    for col in range(height):
        for row in range(width):
            loc = col * width + row
            cell = wordTable[loc]
            # print location
            cell = str(loc).zfill(3) + cell
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


# get room number
@app.get("/ws/{room}")
def create(room: int) -> None:
    global roomId

    roomId = room
    return


# request body: get method cannot have body
class RoomData(BaseModel):
    size: int
    users: list
# initialize game with new word table in size(height * width)
# TODO: modify url
@app.post("/init")
def init(init: RoomData) -> dict:
    global wordData, wordTable, wordMap, height, width, users
    height, width = init.size, init.size
    SIZE = height * width
    EMPTY, START = "  ", 0
    wordData = dataBase

    # initialize wordTable with empty cell
    for i in range(SIZE):
        wordTable[i] = EMPTY

    # initialize userData with score 0
    for user in init.users:
        users[user] = START

    wordTable = getWordTable(wordData, wordTable, height, width)
    wordMap = getWordMap(wordData, wordTable, wordMap, height, width)
    
    printWordTable(wordTable, height, width)
    print(len(list(wordMap.keys())))

    return wordTable


# check if answer word or similar words in word table
# request and response body
class Check(BaseModel):
    user: str
    answer: str
    removeWords: Optional[list] = None
    mostSim: Optional[int] = None
    moveInfo: Optional[list] = None
    increment: Optional[int] = None
# if answer in word table, remove only the answer(includes duplicated)
# TODO: modify url
@app.post("/check")
def check(checkInfo: Check) -> Check:
    global wordData, wordTable, wordMap, moveInfo, height, width, users

    answer = checkInfo.answer
    wordList = list(wordMap.keys())
    # if the answer in word table, remove only the word(includes duplicated)
    if answer in wordList:
        checkInfo.removeWords = [answer]
        checkInfo.mostSim = 1
    # get similar words in word table
    else:
        checkInfo.removeWords, checkInfo.mostSim \
            = getSimWords(simModel, wordList, answer)
    # update
    wordTable, wordMap, checkInfo.moveInfo \
        = updateWordTable(wordData, wordTable, wordMap, 
                          checkInfo.removeWords, height, width)
    checkInfo.increment = len(checkInfo.removeWords)

    print(len(checkInfo.removeWords), checkInfo.mostSim)
    printWordTable(wordTable, height, width)
    print(len(list(wordMap.keys())))

    return checkInfo
