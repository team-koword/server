# print colored in terminal
# from .colored_terminal import C
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
    CharDict = get_json("chars.json")
    WordDict = get_json("words.json")
    FindDict = get_json("finds.json")
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
# from .comp_mode_modeling import *
from comp_mode_modeling import *




## game data
from typing import Optional, TypeVar
from collections import defaultdict
EMPTY, DISCNT = "  ", "X"
CHAR, CONN = 0, 1


# each room data
class RoomData:
    def __init__(self) -> None:
        self.roomId: str = ""
        self.gameTable: dict[int, list] = defaultdict(list) # {loc: [char, connections], ...}
        self.wordMap: dict[str, list] = defaultdict(list)   # {word: [loc, ...], ...}
        self.height: int = 0
        self.width: int = 0
        self.users: dict[str, int] = defaultdict(int)       # {user: score, ...}
        self.turns: int = -1                                # will be 0 when game initialized
        self.answerLog: list = list()                       # [[answer, [removed words]], ...]


# rooms data
Rooms = defaultdict(RoomData)


# game functions module
# from .comp_mode_functions import *
from comp_mode_functions import *




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
from pydantic import BaseModel


# request and response body
class InitBody(BaseModel):
    type: str
    roomId: str
    size: int
    users: list
    table: Optional[dict] = None    # {loc: [char, conn], ...}
    moves: Optional[list] = None    # [[adds]], adds = [[dep, arr, char], ...]
# initialize game with new table in size(height * width)
@app.post("/init")
def init(Init: InitBody) -> InitBody:
    print(f"\n\n{C.Magenta}NEW GAME STARTED{C.End}")
    print(f"room {C.Cyan}{Init.roomId}{C.End}")
    start = time.time()

    # get room data and initialize
    global Rooms, CharDict, WordDict, FindDict
    Room = Rooms[Init.roomId]
    Room.roomId = Init.roomId
    Room.turns = 0
    Room.height, Room.width = Init.size, Init.size
    Room.gameTable = defaultdict(list)
    INIT = 0
    for user in Init.users:
        Room.users[user] = INIT

    # initialize table
    initGameTable(Room.gameTable, Room.height, Room.width)

    # get game data
    Init.moves = list()
    adds = list()
    getGameData(CharDict, WordDict, FindDict, 
                Room.gameTable, Room.wordMap, adds, 
                Room.height, Room.width)
    Init.table = Room.gameTable
    Init.moves.append(adds)

    # print at terminal(for test)
    printGameTable(Room.gameTable, Room.height, Room.width)

    end = time.time()
    print(f"game initialized in {C.Cyan}{end - start}{C.End} secs")
    wordList = list(Room.wordMap.keys())
    print(f"{C.Cyan}{len(wordList)}{C.End} words in table: {C.Cyan}{wordList}{C.End}")
    print(f"{C.Magenta}GAME START{C.End}\n\n")

    return Init


# request and response body
class CheckBody(BaseModel):
    type: str
    roomId: str
    user: str
    answer: str
    table: Optional[dict] = None        # {loc: [char, conn], ...}
    moves: Optional[list] = None        # [[removes], [falls], [adds]]
    remWords: Optional[list] = None     # [word, ...]
    increase: Optional[int] = None
# check if answer word or similar words in table
# if the answer in table, remove only the answer(includes duplicated)
@app.post("/check")
def check(Check: CheckBody) -> CheckBody:
    print(f"\n\n{C.Magenta}CHECKING ANSWER{C.End}")
    print(f"room {C.Cyan}{Check.roomId}{C.End}")
    start = time.time()

    # get room data and dictionary
    global Rooms, CharDict, FindDict
    Room = Rooms[Check.roomId]
    Room.turns += 1

    # get words in game table
    wordList = list(Room.wordMap.keys())
    # if the answer not in dictionary
    if Check.answer not in FindDict[Check.answer[0]][str(len(Check.answer))]:
        Check.remWords = []
    # if the answer in word table, remove only the word(includes duplicated)
    elif Check.answer in wordList:
        Check.remWords = [Check.answer]
    # get similar words in word table
    else:
        Check.remWords = getSimWords(simModel, wordList, Check.answer)
        for word in Check.remWords:
            if word not in wordList:
                Check.remWords.remove(word)

    # update room data
    Check.moves = list()
    updateGameData(CharDict, WordDict, FindDict, Room.gameTable, Room.wordMap, 
                   Check.remWords, Check.moves, Room.height, Room.width)
    print(f"{C.Cyan}{len(list(Room.wordMap.keys()))}{C.End} words in table")

    # update user score and answer log
    increase = len(Check.remWords)
    Room.users[Check.user] += increase
    Check.increase = increase
    Room.answerLog.append([Room.turns, Check.answer, Check.remWords])

    # reset table if words in table less than standard count
    MIN = 20
    if len(list(Room.wordMap.keys())) < MIN:
        # set move information for all cells -> empty
        SIZE = Room.height * Room.width
        removes = [[i, SIZE, Room.gameTable[i]] for i in range(SIZE - 1, -1, -1)]
        Check.moves.append(removes)
        # reset gameTable
        Room.gameTable = defaultdict(list)
        initGameTable(Room.gameTable, Room.height, Room.width)
        adds = list()
        getGameData(CharDict, WordDict, FindDict, 
                    Room.gameTable, Room.wordMap, adds, 
                    Room.height, Room.width)
        Check.moves.append(adds)
        print(f"too little words in table, {C.Green}TABLE REFRESHED{C.End}")

    Check.table = Room.gameTable

    # print at terminal(for test)
    printGameTable(Room.gameTable, Room.height, Room.width)

    end = time.time()
    print(f"answer checked in {C.Cyan}{end - start}{C.End} secs")
    print(f"turn {C.Cyan}{Room.turns}{C.End}, user: {C.Cyan}{Check.user}{C.End}, answer: {C.Cyan}{Check.answer}{C.End}")
    print(f"{C.Cyan}{len(Check.remWords)}{C.End} words removed: {C.Cyan}{Check.remWords}{C.End}")
    wordList = list(Room.wordMap.keys())
    print(f"{C.Cyan}{len(wordList)}{C.End} words in table: {C.Cyan}{wordList}{C.End}")
    print(f"{C.Magenta}ANSWER CHECKED{C.End}\n\n")

    return Check

# request and response body
class FinishBody(BaseModel):
    type: str
    roomId: str
    scores: Optional[list] = None       # [[rank, user, score], ...]
    answerLog: Optional[list] = None    # [[turn, answer, [removesWord, ...]], ...]
# show each user's score from first to last
# and what words removes with each answer
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
    
    # total count for removes words
    TOTAL = sum(score[2] for score in Finish.scores)
    
    end = time.time()
    print(f"game data analyzed in {C.Cyan}{end - start}{C.End} secs")
    print(f"played {C.Cyan}{start - START}{C.End} secs, {C.Cyan}{Room.turns}{C.End} turns")
    print(f"total {C.Cyan}{TOTAL}{C.End} words removes")
    for rank, user, score in Finish.scores:
        print(f"rank {C.Cyan}{rank}{C.End}: {C.Cyan}{user}{C.End}, score: {C.Cyan}{score}{C.End}")
    print(f"{C.Magenta}GAME FINISHED{C.End}\n\n")
    
    return Finish
