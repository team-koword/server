## imports
# FastAPI
from fastapi import FastAPI
app = FastAPI()


# CORS
from fastapi.middleware.cors import CORSMiddleware
# origins = ["*"]
origins = [
    "http://localhost",
    "http://localhost:8080",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# game functions module
from gameFunctions import *
# getWordTable
# getWordMap
# updateWordTable




## global variables
# get dataBase
def getDataBase(fileName: str) -> dict:
    import os
    import json
    dirPath = os.path.dirname(os.path.realpath(__file__)) + "/"
    with open(dirPath + fileName, "r", encoding="utf8") as file:
        dataBase = json.load(file)
    return dataBase


# declare and initialize variables
height, width = 0, 0
wordData = dict()
wordTable = dict()
wordMap = dict()
# ML alternative
relData = dict()




## response for request
# initialize game with new word table in size(height * width)
@app.get("/init/{size}")
def init(size: int) -> dict:
    global wordData, wordTable, wordMap, height, width
    
    height, width = size, size
    wordData = getDataBase("wordDB.json")

    # initialize wordTable with blank(" ")
    for i in range(size):
        wordTable[i] = " "

    wordTable = getWordTable(wordData, wordTable, height, width)
    wordMap = getWordMap(wordData, wordTable, wordMap, height, width)

    return wordTable


# check if answer word or relative words in word table
# if answer in word table, remove only the answer(includes duplicated)
@app.get("/check/{answer}")
def check(answer: str) -> list:
    global wordData, wordTable, wordMap, updateInfo, height, width

    # if the answer in word table, remove only the word(includes duplicated)
    wordList = list(wordMap.keys())
    if answer in wordList:
        removeWords = [answer]
    # check if relative words in word table
    else:
        # get relative words
        # TODO: substitute to get from ML directly
        relData = getDataBase("ML.json")
        # relative words in word table
        if answer in relData:
            removeWords = relData[answer].split(",")
            # no relative word in word table, return directly
            if removeWords == [""]:
                return []
        # no relative word in word table, return directly
        else:
            return []

    wordTable, wordMap, updateInfo \
        = updateWordTable(wordData, wordTable, wordMap, removeWords, height, width)

    return updateInfo
