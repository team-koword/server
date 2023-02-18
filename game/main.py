## for test
# print colored in terminal
class Colors:
    # type
    HEADER = "\033[95m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"

    # color
    Black = "\033[30m"
    Red	= "\033[31m"
    Green = "\033[32m"
    Yellow = "\033[33m"
    Blue = "\033[34m"
    Magenta = "\033[35m"
    Cyan = "\033[36m"
    White = "\033[37m"

    # bright color
    black = "\033[90m"
    red = "\033[91m"
    green = "\033[92m"
    yellow = "\033[93m"
    blue = "\033[94m"
    magenta = "\033[95m"
    cyan = "\033[96m"
    white = "\033[97m"

    # background_color
    B_Black = "\033[40m"
    B_Red = "\033[41m"
    B_Green = "\033[42m"
    B_Yellow = "\033[43m"
    B_Blue = "\033[44m"
    B_Magenta = "\033[45m"
    B_Cyan = "\033[46m"
    B_White = "\033[47m"

    # bright background_color
    B_black = "\033[100m"
    B_red = "\033[101m"
    B_green = "\033[102m"
    B_yellow = "\033[103m"
    B_blue = "\033[104m"
    B_magenta = "\033[105m"
    B_cyan = "\033[106m"
    B_white = "\033[107m"

    # RGB color \033[38;2;r;g;bm
    # RGB background \033[48;2;r;g;bm

    # reset
    End = "\033[0m"

# start server
print(f"\n\n{Colors.white}{Colors.B_blue}GAME SERVER STARTED{Colors.End}")

# test run-time
import time
START = time.time()

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
print(f"LOADING DATA: {Colors.Cyan}dictionary{Colors.End}")
start = time.time()

try:
    ToPut = get_json("to_put.json")
    ToFind = get_json("to_find.json")
    end = time.time()
    print(f"{Colors.Green}SUCCESS{Colors.End} to load dictionary in {Colors.Cyan}{end - start}{Colors.End} secs")
except Exception as err:
    print(f"{Colors.red}FAIL{Colors.End} to load dictionary: {err}")

# get vector similarity model
print(f"LOADING DATA: {Colors.Cyan}fast-text model{Colors.End}")
start = time.time()

import fasttext
try:
    simModel = fasttext.load_model('./model.bin')
    end = time.time()
    print(f"{Colors.Green}SUCCESS{Colors.End} to load fast-text model in {Colors.Cyan}{end - start}{Colors.End} secs")
except Exception as err:
    print(f"{Colors.red}FAIL{Colors.End} to load fast-text model: {err}")

print(f"{Colors.white}{Colors.B_blue}GAME SERVER IS READY{Colors.End}\n\n")


# modeling functions module
from modeling import *




## game data
from collections import defaultdict
# each room data
class RoomData:
    def __init__(self) -> None:
        self.roomId: str = ""
        self.wordTable = defaultdict(lambda: "  ")  # {loc: char, ...}
        self.wordMap = defaultdict(list)            # {word: [loc, ...], ...}
        self.height: int = 0
        self.width: int = 0
        self.users = defaultdict(int)               # {user: score, ...}
        self.roundCnt: int = -1                     # will be 0 when game initialized
        self.answerLog: list = list()               # [[answer, [removed words]], ...]


# rooms data
Rooms = defaultdict(RoomData)


# game functions module
from gameFunctions import *


# print wordTable in Terminal(for test)
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


# request and response
from typing import Optional, List
from pydantic import BaseModel


# request and response body
class InitBody(BaseModel):
    type: str
    roomId: str
    size: int
    users: list
    wordTable: Optional[dict] = None    # {loc: char, ...}
    possLocs: Optional[set] = None      # {loc, ...}
# initialize game with new word table in size(height * width)
@app.post("/init")
def init(Init: InitBody) -> InitBody:
    print(f"\n\n{Colors.Blue}NEW GAME STARTED{Colors.End}")
    print(f"room {Colors.Cyan}{Init.roomId}{Colors.End}")
    start = time.time()

    # get room data and initialize
    global Rooms, ToPut, ToFind
    Room = Rooms[Init.roomId]
    Room.roomId = Init.roomId
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
    Room.wordMap, Init.possLocs = getWordMap(ToFind, Room.wordTable, Room.wordMap, 
                                             Room.height, Room.width)

    # put word table in response body
    # # print at terminal(for test)
    # printWordTable(Room.wordTable, Room.height, Room.width)
    # print(f"wordList: {list(Room.wordMap.keys())}")

    end = time.time()
    print(f"game initialized in {Colors.Cyan}{end - start}{Colors.End} secs")
    print(f"{Colors.Cyan}{len(list(Room.wordMap.keys()))}{Colors.End} words in table\n\n")

    return Init


# request and response body
class CheckBody(BaseModel):
    type: str
    roomId: str
    user: str
    answer: str
    removeWords: Optional[list] = None  # [word, ...]
    mostSim: Optional[int] = None
    moveInfo: Optional[list] = None     # [[from, to, char], ...]
    increment: Optional[int] = None
    possLocs: Optional[set] = None      # {loc, ...}
# check if answer word or similar words in word table
# if answer in word table, remove only the answer(includes duplicated)
@app.post("/check")
def check(Check: CheckBody) -> CheckBody:
    print(f"\n\n{Colors.Blue}CHECKING ANSWER{Colors.End}")
    print(f"room {Colors.Cyan}{Check.roomId}{Colors.End}")
    start = time.time()

    # get room data
    global Rooms, ToPut, ToFind
    Room = Rooms[Check.roomId]
    Room.roundCnt += 1

    # get word list to check the answer
    wordList = list(Room.wordMap.keys())
    # if the answer in word table, remove only the word(includes duplicated)
    if Check.answer in wordList:
        Check.removeWords = [Check.answer]
        Check.mostSim = 100
    # get similar words in word table
    else:
        Check.removeWords, Check.mostSim \
            = getSimWords(simModel, wordList, Check.answer)
    
    # update room data
    Room.wordTable, Room.wordMap, Check.possLocs, Check.moveInfo \
        = updateWordTable(ToPut, ToFind, Room.wordTable, Room.wordMap, 
                          Check.removeWords, Room.height, Room.width)
    
    # log removed words
    Room.answerLog.append([Room.roundCnt, Check.answer, Check.removeWords])

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
        Room.wordMap, Check.possLocs = getWordMap(ToFind, 
                                                 Room.wordTable, Room.wordMap, 
                                                 Room.height, Room.width)
        print(f"too little words in table, {Colors.Green}TABLE REFRESHED{Colors.End}")

    # # print at terminal(for test)
    # printWordTable(Room.wordTable, Room.height, Room.width)
    # print(f"wordList: {list(Room.wordMap.keys())}")
    # print(f"moveinfo: {Check.moveInfo}")

    end = time.time()
    print(f"answer checked in {Colors.Cyan}{end - start}{Colors.End} secs")
    print(f"round {Colors.Cyan}{Room.roundCnt}{Colors.End}, user: {Colors.Cyan}{Check.user}{Colors.End}, answer: {Colors.Cyan}{Check.answer}{Colors.End}")
    print(f"removed words: {Colors.Cyan}{len(Check.removeWords)}{Colors.End}, mostSim: {Colors.Cyan}{Check.mostSim}{Colors.End}")
    print(f"{Colors.Cyan}{len(list(Room.wordMap.keys()))}{Colors.End} words in table\n\n")

    return Check

# request and response body
class FinishBody(BaseModel):
    type: str
    roomId: str
    scores: Optional[list] = None       # [[rand, user, score], ...]
    answerLog: Optional[list] = None    # [[round, answer, [removeWord, ...]], ...]
# show each user's score from first to last
# and what words removed with each answer
@app.post("/finish")
def finish(Finish: FinishBody) -> FinishBody:
    print(f"\n\n{Colors.Magenta}FINISHING GAME{Colors.End}")
    print(f"room {Colors.Cyan}{Finish.roomId}{Colors.End}")
    start = time.time()

    # get room data
    global Rooms
    Room = Rooms[Finish.roomId]

    # user's score
    scores = list()
    for user, score in Room.users.items():
        scores.append([user, score])
    # sort from first to last
    scores.sort(key = lambda x: -x[1])
    for i in range(len(scores)):
        scores[i].insert(0, i + 1)
    Finish.scores = scores

    # answer log
    Finish.answerLog = Room.answerLog
    
    # total count for removed words
    TOTAL = sum(score[2] for score in Finish.scores)
    
    end = time.time()
    # print(f"game data analyzed in {Colors.Cyan}{end - start}{Colors.End} secs")
    print(f"played {Colors.Cyan}{start - START}{Colors.End} secs, {Colors.Cyan}{Room.roundCnt}{Colors.End} rounds")
    print(f"total {Colors.Cyan}{TOTAL}{Colors.End} words removed")
    for rank, user, score in Finish.scores:
        print(f"rank {Colors.Cyan}{rank}{Colors.End}: {Colors.Cyan}{user}{Colors.End}, score: {Colors.Cyan}{score}{Colors.End}")
    print(f"{Colors.Magenta}GAME FINISHED{Colors.End}\n\n")
    
    return Finish
