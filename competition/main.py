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
# get directory real path
import os
dirPath = os.path.dirname(os.path.realpath(__file__)) + "/"

# get json file function
def get_json(fileName: str) -> dict:
    import json
    with open(dirPath + fileName, "r", encoding="utf8") as file:
        json_file = json.load(file)
    return json_file


# get json data
print(f"LOADING DATA: {C.Cyan}dictionary{C.End}")
start = time.time()

try:
    FirstDict = get_json("chars.json")  # {first: {len: [words], ...}, ...}
    LastDict = get_json("lasts.json")   # {last: {first: {len: [words], ...}, ...}, ...}
    WordDict = get_json("words.json")   # {len: [words], ...}
    FindDict = get_json("finds.json")   # {len: {char: [words], ...}, ...}
    end = time.time()
    print(f"{C.Green}SUCCESS{C.End} to load dictionary in {C.Cyan}{end - start}{C.End} secs")
except Exception as err:
    print(f"{C.red}FAIL{C.End} to load dictionary: {err}")


# get vector similarity model
print(f"LOADING DATA: {C.Cyan}fast-text model{C.End}")
start = time.time()

import fasttext
try:
    simModel = fasttext.load_model(dirPath + "model.bin")
    end = time.time()
    print(f"{C.Green}SUCCESS{C.End} to load fast-text model in {C.Cyan}{end - start}{C.End} secs")
except Exception as err:
    print(f"{C.red}FAIL{C.End} to load fast-text model: {err}")

print(f"{C.Magenta}GAME SERVER IS READY{C.End}\n\n")


# modeling functions module
from comp_mode_modeling import *




## game data
from typing import Optional
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
from comp_mode_functions import *




## response and request
# FastAPI
from fastapi import FastAPI
app = FastAPI()


# sentry
import sentry_sdk

sentry_sdk.init(
    dsn="https://0b799141cf7c40b18cce3f9d165da751@o4504772214325248.ingest.sentry.io/4504778998218752",
    environment="production",

    # Set traces_sample_rate to 1.0 to capture 100%
    # of transactions for performance monitoring.
    # We recommend adjusting this value in production,
    traces_sample_rate=1.0,
)


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
    print(f"{C.Cyan}{time.strftime('%Y-%m-%d %H:%M:%S')}{C.End}")
    print(f"room {C.Cyan}{Init.roomId}{C.End}")
    start = time.time()

    # get room data and initialize
    global Rooms, FirstDict, LastDict, WordDict
    # initialize room data
    Rooms[Init.roomId].__init__()
    Room = Rooms[Init.roomId]
    Room.roomId = Init.roomId
    Room.turns = 0
    Room.height, Room.width = Init.size, Init.size
    INIT = 0
    for user in Init.users:
        Room.users[user] = INIT

    # initialize table
    Room.gameTable, Room.wordMap \
        = initGameData(Room.gameTable, Room.wordMap, Room.height, Room.width)

    # get game data
    Init.moves = list()
    adds = list()
    Room.gameTable, Room.wordMap, adds = \
        getGameData(FirstDict, LastDict, WordDict, 
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
    print(f"{C.Cyan}{time.strftime('%Y-%m-%d %H:%M:%S')}{C.End}")
    print(f"room {C.Cyan}{Check.roomId}{C.End}")
    start = time.time()

    # get room data and dictionary
    global Rooms, FirstDict, LastDict, WordDict, FindDict
    Room = Rooms[Check.roomId]
    Room.turns += 1

    # get words in game table
    wordList = list(Room.wordMap.keys())
    # if the answer not in dictionary
    if str(len(Check.answer)) not in FindDict \
        or Check.answer[0] not in FindDict[str(len(Check.answer))] \
        or Check.answer not in FindDict[str(len(Check.answer))][Check.answer[0]]:
        Check.remWords = []
        print(f"answer {C.Cyan}{Check.answer}{C.End} not in dictionary")
    # if the answer in gameTable, remove only the word(includes duplicated)
    elif Check.answer in wordList:
        Check.remWords = [Check.answer]
        print(f"answer {C.Cyan}{Check.answer}{C.End} in game table")
    # get similar words in gameTable
    else:
        Check.remWords = getSimWords(simModel, wordList, Check.answer)
        print(f"words similar with answer {C.Cyan}{Check.answer}{C.End} will be removed")

    # update room data
    Check.moves = list()
    Room.gameTable, Room.wordMap, Check.moves \
        = updateGameData(FirstDict, LastDict, WordDict,
                         Room.gameTable, Room.wordMap, Check.moves, 
                         Check.remWords, Room.height, Room.width)

    # update user score and answer log
    increase = len(Check.remWords)
    Room.users[Check.user] += increase
    Check.increase = increase
    if Check.remWords:
        Room.answerLog.append([Room.turns, Check.answer, Check.remWords])

    # reset table if words in table less than standard count
    MIN = 40
    SIZE = Room.height * Room.width
    if len(list(Room.wordMap.keys())) < MIN:
        # set move information for all cells -> empty
        removes = [[i, SIZE, Room.gameTable[i][CHAR]] for i in range(SIZE - 1, -1, -1)]
        Check.moves.append(removes)
        # initialize gameTable and wordMap
        Room.gameTable, Room.wordMap \
            = initGameData(Room.gameTable, Room.wordMap, Room.height, Room.width)
        adds = list()
        # get game data again
        Room.gameTable, Room.wordMap, adds \
            = getGameData(FirstDict, LastDict, WordDict, 
                          Room.gameTable, Room.wordMap, adds, 
                          Room.height, Room.width)
        Check.moves.append(adds)
        print(f"{C.Cyan}{len(list(Room.wordMap.keys()))}{C.End} words were in table, {C.Green}TABLE REFRESHED{C.End}")

    Check.table = Room.gameTable

    # print at terminal(for test)
    for i, move in enumerate(Check.moves):
        if i == 0:
            print(f"removes: {C.Cyan}{len(move)} {move}{C.End}")
        elif i == 1:
            print(f"falls: {C.Cyan}{len(move)} {move}{C.End}")
        elif i == 2:
            print(f"adds: {C.Cyan}{len(move)} {move}{C.End}")
        elif i == 3:
            print(f"(reset)removes: {C.Cyan}{len(move)} {move}{C.End}")
        elif i == 4:
            print(f"(reset)adds: {C.Cyan}{len(move)} {move}{C.End}")
    printGameTable(Room.gameTable, Room.height, Room.width)

    def _error(FirstDict: dict, LastDict: dict, WordDict: dict, 
               gameTable: dict, wordMap: dict, 
               table: dict, moves: list, height: int, width: int) \
        -> Tuple[dict, dict, dict, list]:
        moves = list()
        removes = [[i, SIZE, gameTable[i][CHAR]] for i in range(SIZE - 1, -1, -1)]
        falls = list()
        adds = list()
        moves.append(removes)
        moves.append(falls)
        moves.append(adds)
        gameTable, wordMap \
            = initGameData(gameTable, wordMap, height, width)
        gameTable, wordMap, adds \
            = getGameData(FirstDict, LastDict, WordDict, 
                          gameTable, wordMap, adds, 
                          height, width)
        table = gameTable
        for i, move in enumerate(moves):
            if i == 0:
                print(f"removes: {C.Cyan}{len(move)} {move}{C.End}")
            elif i == 1:
                print(f"falls: {C.Cyan}{len(move)} {move}{C.End}")
            elif i == 2:
                print(f"adds: {C.Cyan}{len(move)} {move}{C.End}")
        printGameTable(gameTable, height, width)
        return gameTable, wordMap, table, moves

    # initialize gameTable if removed and added chars counts different
    if len(Check.moves[0]) != len(Check.moves[2]):
        print(f"{C.red}ERROR{C.End} removes counts {C.Cyan}{Check.moves[0]}{C.End} and adds counts {C.Cyan}{Check.moves[2]}{C.End} different")
        Room.gameTable, Room.wordMap, Check.table, Check.moves \
            = _error(FindDict, LastDict, WordDict, Room.gameTable, Room.wordMap, 
                     Check.table, Check.moves, Room.height, Room.width)

    # check error if gameTable and wordMap unmatched
    flag = False
    wordList = list(Room.wordMap.keys())
    for word in wordList:
        temp = ""
        for loc in Room.wordMap[word]:
            temp += Room.gameTable[loc][CHAR]
        if word != temp:
            print(f"{C.Red}ERROR{C.End} gameTable and wordMap different, word: {C.Cyan}{word}{C.End}, locs: {C.Cyan}{Room.wordMap[word]}{C.End}")
            Room.gameTable, Room.wordMap, Check.table, Check.moves \
                = _error(FindDict, LastDict, WordDict, Room.gameTable, Room.wordMap, 
                        Check.table, Check.moves, Room.height, Room.width)
            flag = True
            break
        if flag == True:
            break

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
    print(f"{C.Cyan}{time.strftime('%Y-%m-%d %H:%M:%S')}{C.End}")
    print(f"room {C.Cyan}{Finish.roomId}{C.End}")
    start = time.time()

    # get room data and dictionary
    global Rooms
    Room = Rooms[Finish.roomId]

    # user's score in score descending order
    scores = sorted([[user, score] for user, score \
        in Room.users.items()], key=lambda x: -x[1])
    # put rank at first
    TOTAL = sum(score[1] for score in scores)
    Finish.scores = [[rank, user, score] for rank, (user, score) \
        in enumerate(scores, start=1)]

    # answer log
    Finish.answerLog = Room.answerLog
    
    end = time.time()
    print(f"game data analyzed in {C.Cyan}{end - start}{C.End} secs")
    print(f"played {C.Cyan}{start - START}{C.End} secs, {C.Cyan}{Room.turns}{C.End} turns")
    print(f"total {C.Cyan}{TOTAL}{C.End} words removes")
    for rank, user, score in Finish.scores:
        print(f"rank {C.Cyan}{rank}{C.End}: {C.Cyan}{user}{C.End}, score: {C.Cyan}{score}{C.End}")
    print(f"{C.Magenta}GAME FINISHED{C.End}\n\n")
    
    # delete room data
    del(Rooms[Finish.roomId])
    
    return Finish


# sentry
@app.get("/sentry-debug")
async def trigger_error():
    division_by_zero = 1 / 0
