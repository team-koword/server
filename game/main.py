# print colored in terminal
from colored_terminal import C


##### COMPETETION MODE SERVER #####
print(f"\n\n{C.white}{C.B_magenta}COMPETETION MODE{C.End}")


# start server
print(f"\n\n{C.Magenta}GAME SERVER STARTED{C.End}")

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
print(f"LOADING DATA: {C.Cyan}dictionary{C.End}")
start = time.time()

try:
    ToPut = get_json("to_put.json")
    ToFind = get_json("to_find.json")
    end = time.time()
    print(f"{C.Green}SUCCESS{C.End} to load dictionary in {C.Cyan}{end - start}{C.End} secs")
except Exception as err:
    print(f"{C.red}FAIL{C.End} to load dictionary: {err}")

# get vector similarity model
print(f"LOADING DATA: {C.Cyan}fast-text model{C.End}")
start = time.time()

import fasttext
try:
    simModel = fasttext.load_model("./model.bin")
    end = time.time()
    print(f"{C.Green}SUCCESS{C.End} to load fast-text model in {C.Cyan}{end - start}{C.End} secs")
except Exception as err:
    print(f"{C.red}FAIL{C.End} to load fast-text model: {err}")

print(f"{C.Magenta}GAME SERVER IS READY{C.End}\n\n")


# modeling functions module
from modeling import *




## game data
from collections import defaultdict
EMPTY = "  "


# each room data
class RoomData:
    def __init__(self) -> None:
        self.roomId: str = ""
        self.wordTable = defaultdict(lambda: EMPTY) # {loc: char, ...}
        self.wordMap = defaultdict(list)            # {word: [loc, ...], ...}
        self.height: int = 0
        self.width: int = 0
        self.users = defaultdict(int)               # {user: score, ...}
        self.turns: int = -1                        # will be 0 when game initialized
        self.answerLog: list = list()               # [[answer, [removed words]], ...]


# rooms data
Rooms = defaultdict(RoomData)


# game functions module
from game_functions import *




## response and request
# FastAPI
from fastapi import FastAPI
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
from typing import Optional
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
    print(f"\n\n{C.Magenta}NEW GAME STARTED{C.End}")
    print(f"room {C.Cyan}{Init.roomId}{C.End}")
    start = time.time()

    # get room data and initialize
    global Rooms, ToPut, ToFind
    Room = Rooms[Init.roomId]
    Room.roomId = Init.roomId
    Room.turns = 0
    Room.height, Room.width = Init.size, Init.size
    START = 0
    for user in Init.users:
        Room.users[user] = START

    # initialize word table
    Room.wordTable = initWordTable(Room.wordTable, Room.height, Room.width)

    # get word table and word map
    Room.wordTable = getWordTable(ToPut, Room.wordTable, 
                                  Room.height, Room.width)
    Room.wordMap = getWordMap(ToFind, Room.wordTable, Room.wordMap, 
                              Room.height, Room.width)

    # put word table and possible locations in response body
    Init.wordTable = Room.wordTable
    Init.possLocs = getPossLocs(Room.wordMap)
    
    # # print at terminal(for test)
    # printWordTable(Room.wordTable, Room.height, Room.width)

    end = time.time()
    print(f"game initialized in {C.Cyan}{end - start}{C.End} secs")
    print(f"{C.Cyan}{len(list(Room.wordMap.keys()))}{C.End} words in table")
    print(f"{C.Magenta}GAME START{C.End}\n\n")

    return Init


# request and response body
class CheckBody(BaseModel):
    type: str
    roomId: str
    user: str
    answer: str
    removedWords: Optional[list] = None  # [word, ...]
    mostSim: Optional[int] = None
    moveInfo: Optional[list] = None     # [[from, to, char], ...]
    increment: Optional[int] = None
    possLocs: Optional[set] = None      # {loc, ...}
# check if answer word or similar words in word table
# if the answer in word table, remove only the answer(includes duplicated)
@app.post("/check")
def check(Check: CheckBody) -> CheckBody:
    print(f"\n\n{C.Magenta}CHECKING ANSWER{C.End}")
    print(f"room {C.Cyan}{Check.roomId}{C.End}")
    start = time.time()

    # get room data and dictionary
    global Rooms, ToPut, ToFind
    Room = Rooms[Check.roomId]
    Room.turns += 1

    # get word list to check the answer
    wordList = list(Room.wordMap.keys())
    # if the answer in word table, remove only the word(includes duplicated)
    if Check.answer in wordList:
        Check.removedWords = [Check.answer]
        Check.mostSim = 100
    # get similar words in word table
    else:
        Check.removedWords, Check.mostSim = getSimWords(simModel, wordList, 
                                                        Check.answer)
    
    # update room data
    Room.wordTable, Room.wordMap, Check.moveInfo \
        = updateWordTable(ToPut, ToFind, Room.wordTable, Room.wordMap, 
                          Check.removedWords, Room.height, Room.width)
    
    # log removed words
    Room.answerLog.append([Room.turns, Check.answer, Check.removedWords])

    # update score
    increment = len(Check.removedWords)
    Room.users[Check.user] += increment
    Check.increment = increment

    # renew word table if words in table less than standard count
    MIN = 30
    # set move information for all cells -> empty
    if len(list(Room.wordMap.keys())) < MIN:
        SIZE = Room.height * Room.width
        Check.moveInfo = [[loc, SIZE, Room.wordTable[loc]] \
            for loc in range(SIZE - 1, -1, -1)]
        # initWordTable
        Room.wordTable = initWordTable(Room.wordTable, Room.height, Room.width)
        # get word table and word map
        Room.wordTable, Check.moveInfo = getWordTable(ToPut, Room.wordTable, 
                                                      Room.height, Room.width, 
                                                      Check.moveInfo)
        Room.wordMap = getWordMap(ToFind, Room.wordTable, Room.wordMap, 
                                  Room.height, Room.width)
        print(f"too little words in table, {C.Green}TABLE REFRESHED{C.End}")

    # put possible locations in response body
    Check.possLocs = getPossLocs(Room.wordMap)

    # # print at terminal(for test)
    # printWordTable(Room.wordTable, Room.height, Room.width)

    end = time.time()
    print(f"answer checked in {C.Cyan}{end - start}{C.End} secs")
    print(f"turn {C.Cyan}{Room.turns}{C.End}, user: {C.Cyan}{Check.user}{C.End}, answer: {C.Cyan}{Check.answer}{C.End}")
    print(f"{C.Cyan}{len(Check.removedWords)}{C.End} words removed: {C.Cyan}{Check.removedWords}{C.End}")
    print(f"{C.Cyan}{len(list(Room.wordMap.keys()))}{C.End} words in table")
    print(f"{C.Magenta}ANSWER CHECKED{C.End}\n\n")

    return Check

# request and response body
class FinishBody(BaseModel):
    type: str
    roomId: str
    scores: Optional[list] = None       # [[rank, user, score], ...]
    answerLog: Optional[list] = None    # [[turn, answer, [removedWord, ...]], ...]
# show each user's score from first to last
# and what words removed with each answer
@app.post("/finish")
def finish(Finish: FinishBody) -> FinishBody:
    print(f"\n\n{C.Magenta}FINISHING GAME{C.End}")
    print(f"room {C.Cyan}{Finish.roomId}{C.End}")
    start = time.time()

    # get room data and dictionary
    global Rooms
    Room = Rooms[Finish.roomId]

    # user's score in score descending order
    scores = sorted([[user, score] for user, score \
        in Room.users.items()], key=lambda x: -x[1])
    # put rank at first
    Finish.scores = [[rank, user, score] for rank, (user, score) \
        in enumerate(scores, start=1)]

    # answer log
    Finish.answerLog = Room.answerLog
    
    # total count for removed words
    TOTAL = sum(score[2] for score in Finish.scores)
    
    end = time.time()
    print(f"game data analyzed in {C.Cyan}{end - start}{C.End} secs")
    print(f"played {C.Cyan}{start - START}{C.End} secs, {C.Cyan}{Room.turns}{C.End} turns")
    print(f"total {C.Cyan}{TOTAL}{C.End} words removed")
    for rank, user, score in Finish.scores:
        print(f"rank {C.Cyan}{rank}{C.End}: {C.Cyan}{user}{C.End}, score: {C.Cyan}{score}{C.End}")
    print(f"{C.Magenta}GAME FINISHED{C.End}\n\n")
    
    return Finish
