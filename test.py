import os
import json
from random import choice
from gameFunctions import *


## global variables
# get dataBase
def getDataBase(fileName: str) -> dict:
    import os
    import json
    dirPath = os.path.dirname(os.path.realpath(__file__)) + "/"
    with open(dirPath + fileName, "r", encoding="utf8") as file:
        dataBase = json.load(file)
    return dataBase


# print wordTable in Terminal
def printWordTable(wordTable: dict, height: int, width: int) -> None:
    for col in range(height):
        for row in range(width):
            loc = col * width + row
            cell = wordTable[loc]
            # print location
            cell = str(loc).zfill(2) + cell
            print(cell, end=" ")
        print()
    print()


# declare and initialize variables
height, width = 0, 0
wordData = dict()
wordTable = dict()
wordMap = dict()
# ML alternative
relData = dict()


height, width = 10, 10
SIZE = height * width
EMPTY = "  "
wordData = getDataBase("wordDB.json")

# initialize wordTable with empty cell
for i in range(SIZE):
    wordTable[i] = EMPTY


# ----------------------------------------


# 1. initialize word table with size(height * width)
# and also use to update word table
def init():
    global wordData, wordTable, height, width

    wordTable = getWordTable(wordData, wordTable, height, width)
    printWordTable(wordTable, height, width)
    print()
    
    return wordTable


# 2. find words in map
# rightCnt, downCnt for check
def mapping():
    global wordData, wordTable, wordMap, height, width

    wordTable = init()

    # wordMap, rightCnt, downCnt = getWordMap(wordData, wordTable, wordMap, height, width)
    # print(f"total: {rightCnt + downCnt}, diff: {rightCnt - downCnt}")
    wordMap = getWordMap(wordData, wordTable, wordMap, height, width)
    print(f"wordMap: {wordMap}")
    print()

    wordList = list(wordMap.keys())
    print(f"wordList: {len(wordList)} {wordList}")
    print()
    
    return wordTable, wordMap, wordList


# 3. check answer, update
def check():
    global wordData, wordTable, wordMap, height, width

    wordTable, wordMap, wordList = mapping()
    relData = getDataBase("ML.json")

    answer = choice(wordList)
    print("answer")
    print(answer)
    print()

    if answer in wordList:
        removeWords = [answer]
        print("answer in wordList!")
    else:
        if answer in relData:
            removeWords = relData[answer].split(",")
            if removeWords == [""]:
                removeWords = []
        else:
            removeWords = []
    print(f"removeWords: {removeWords}")
    for removeWord in removeWords:
        print(f"{removeWord}: {wordMap[removeWord]}")
    print()

    wordTable, wordMap, updateInfo \
        = updateWordTable(wordData, wordTable, wordMap, removeWords, height, width)
    print("wordTable")
    printWordTable(wordTable, height, width)
    print()

    print("updateInfo")
    print(updateInfo)
    print()

    print("wordMap")
    print(wordMap)
    print()

    wordList = list(wordMap.keys())
    print(f"wordList: {len(wordList)} {wordList}")
    print()


# 4. input
def play():
    global wordData, wordTable, wordMap, height, width

    wordTable, wordMap, wordList = mapping()
    relData = getDataBase("ML.json")

    while True:
        answer = input()
        print(f"answer: {answer}")
        print()

        if answer in wordList:
            removeWords = [answer]
            print("answer in wordList!")
        else:
            if answer in relData:
                removeWords = relData[answer].split(",")
                if removeWords == [""]:
                    removeWords = []
            else:
                removeWords = []
        print(f"removeWords: {removeWords}")
        for removeWord in removeWords:
            print(f"{removeWord}: {wordMap[removeWord]}")
        print()

        wordTable, wordMap, updateInfo \
            = updateWordTable(wordData, wordTable, wordMap, removeWords, height, width)
        print(f"updateInfo: {updateInfo}")
        print()
        printWordTable(wordTable, height, width)
        print(f"wordMap: {wordMap}")
        print()
        wordList = list(wordMap.keys())
        print(f"wordList: {len(wordList)} {wordList}")
        print()

init()