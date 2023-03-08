# print colored in terminal
from colored_terminal import C


##### COOPERATION MODE SERVER #####
print(f"\n\n{C.white}{C.B_blue}COOPERATION MODE{C.End}")


# start server
print(f"\n\n{C.Blue}GAME SERVER STARTED{C.End}")


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

import json
try:
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

print(f"{C.Blue}GAME SERVER IS READY{C.End}\n\n")


# modeling functions module
from coop_mode_modeling import *




## game data
from typing import Optional
from collections import defaultdict
# each room data
class RoomData:
    def __init__(self) -> None:
        self.roomId: str = ""
        self.gameTable: dict[int, str] = defaultdict(str)   # {loc: char, ...}
        self.wordMap: dict[str, int] = defaultdict(int)     # {word: loc, ...}
        self.rowMap: dict[int, list] = defaultdict(list)    # {row: [words], ...}
        self.height: int = 0
        self.width: int = 0
        self.times: float = 0
        self.users: dict[str, int] = defaultdict(int)       # {user: score, ...}
        self.tries: int = -1                                # will be 0 when game initialized
        self.answerLog: list = list()                       # [[answer, [removed words]], ...]


# rooms data
Rooms = defaultdict(RoomData)


# game functions module
from coop_mode_functions import *




## response and request
# FastAPI
from fastapi import FastAPI
app = FastAPI()


# sentry
import sentry_sdk
sentry_sdk.init(
    dsn="https://1ae39f0f338248a8abbe893a34f8ee13@o4504772214325248.ingest.sentry.io/4504779026137088",
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
# initialize new game in size(height * width)
@app.post("/init")
def init(Init: InitBody) -> InitBody:
    print(f"\n\n{C.Blue}NEW GAME STARTED{C.End}")
    print(f"{C.Cyan}{time.strftime('%Y-%m-%d %H:%M:%S')}{C.End}")
    print(f"room {C.Cyan}{Init.roomId}{C.End}")
    start = time.time()

    # get room data and initialize
    global Rooms
    # initialize room data
    Rooms[Init.roomId].__init__()
    Room = Rooms[Init.roomId]
    Room.roomId = Init.roomId
    Room.tries = 0
    Room.height, Room.width = Init.size, Init.size
    for user in Init.users:
        Room.users[user] = 0

    # initialize word table
    initWordTable(Room.gameTable, Room.height, Room.width)

    # print at terminal(for test)
    printWordTable(Room.gameTable, Room.height, Room.width)

    end = time.time()
    print(f"game initialized in {C.Cyan}{end - start}{C.End} secs")
    print(f"{C.Blue}GAME START{C.End}\n\n")
    
    return Init


# request and response body
class NextBody(BaseModel):
    type: str
    roomId: str
    status: Optional[str] = None	# "continue" | "gameover"
    word: Optional[str] = None
    left: Optional[int] = None
    length: Optional[int] = None
    fall: Optional[int] = None
# put next new word
# if the new word reach to top, game over
@app.post("/next")
def next(Next: NextBody) -> NextBody:
    print(f"\n\n{C.Blue}NEW WORD FALLING{C.End}")
    print(f"{C.Cyan}{time.strftime('%Y-%m-%d %H:%M:%S')}{C.End}")
    print(f"room {C.Cyan}{Next.roomId}{C.End}")
    start = time.time()

    # get room data and dictionary
    global Rooms, WordDict
    Room = Rooms[Next.roomId]
    NEW, OVER = -1, 0

    # get random word with random length, which falls at random column
    from random import choice, choices, randint

    lengths = [2, 3, 4, 5]
    weights = [50, 24, 24, 2]
    Next.length = choices(lengths, weights)[0]

    while True:
        Next.word = choice(WordDict[str(Next.length)])
        if Next.word not in Room.wordMap:
            break

    Next.left = randint(0, Room.width - Next.length)
    
    # set game information with dummy value for fallWord function
    for i, char in enumerate(Next.word):
        Room.gameTable[Next.left - Room.width + i] = char
    Room.wordMap[Next.word] = Next.left - Room.width
    Room.rowMap[NEW].append(Next.word)
    
    # word falls down
    Next.fall = fallWord(Room.gameTable, Room.wordMap, Room.rowMap, 
                         Room.height, Room.width, Next.word, Next.left)
    
    # game over if next word reached to top
    Next.status = "gameover" if Next.fall == OVER else "continue"
    if Next.status == "gameover":
        print(f"\n{C.red}GAMEOVER{C.End}\n")

    end = time.time()
    TOP = Room.height - getRow(min(Room.wordMap.values()), Room.width) if Room.wordMap else 0

    # print at terminal(for test)
    printWordTable(Room.gameTable, Room.height, Room.width)

    print(f"next word fell in {C.Cyan}{end - start}{C.End} secs")
    print(f"{C.Cyan}{sum(len(Room.rowMap[row]) for row in range(Room.height))}{C.End} words in table")
    print(f"top word in {C.Cyan}{TOP}{C.End} th rows")
    print(f"{C.Blue}NEXT WORD FELL{C.End}\n\n")

    return Next


# request and response body
class CheckBody(BaseModel):
    type: str
    roomId: str
    user: str
    answer: str
    remWords: Optional[list] = None     # [word, ...]
    moveInfo: Optional[list] = None     # [[word: str, fall: int], ...]
    increase: Optional[int] = None
# check and remove words similar with the answer
# if the answer in word table, lock it
@app.post("/check")
def check(Check: CheckBody) -> CheckBody:
    print(f"\n\n{C.Blue}CHECKING ANSWER{C.End}")
    print(f"{C.Cyan}{time.strftime('%Y-%m-%d %H:%M:%S')}{C.End}")
    print(f"room {C.Cyan}{Check.roomId}{C.End}")
    start = time.time()

    # get room data and dictionary
    global Rooms, WordDict, FindDict
    Room = Rooms[Check.roomId]
    Room.tries += 1

    # if the answer not in dictionary
    if str(len(Check.answer)) not in FindDict \
        or Check.answer[0] not in FindDict[str(len(Check.answer))] \
        or Check.answer not in FindDict[str(len(Check.answer))][Check.answer[0]]:
        Check.remWords = []
        Check.moveInfo = []
        Check.increase = 0

        end = time.time()
        TOP = Room.height - getRow(min(Room.wordMap.values()), Room.width) if Room.wordMap else 0

        print(f"answer checked in {C.Cyan}{end - start}{C.End} secs")
        print(f"try {C.Cyan}{Room.tries}{C.End}, user: {C.Cyan}{Check.user}{C.End}, answer: {C.Cyan}{Check.answer}{C.End}")
        print(f"{C.Cyan}{len(Check.remWords)}{C.End} words removed: {C.Cyan}{Check.remWords}{C.End}")
        print(f"{C.Cyan}{sum(len(Room.rowMap[row]) for row in range(Room.height))}{C.End} words in table")
        print(f"top word in {C.Cyan}{TOP}{C.End} th rows\n\n")
        print(f"{C.Blue}ANSWER NOT IN DICTIONARY{C.End}\n\n")
        return Check

    # get words to remove similar with the answer
    Check.remWords = getSimWords(simModel, list(Room.wordMap.keys()), Check.answer)

    # lock the answer if exists in word table
    if Check.answer in Check.remWords:
        Check.remWords.remove(Check.answer)

    # remove similar words
    Check.moveInfo = list()
    if removeWords:
        removeWords(Room.gameTable, Room.wordMap, Room.rowMap, 
                    Room.height, Room.width, Check.remWords)

        # words above removed words fall down
        for row in range(Room.height - 2, -1, -1):
            words = Room.rowMap[row][:]
            for word in words:
                fall = fallWord(Room.gameTable, Room.wordMap, Room.rowMap, 
                                Room.height, Room.width, word)
                if fall:
                    Check.moveInfo.append([word, fall])

    # update answer log
    if Check.remWords:
        Room.answerLog.append([Room.tries, Check.answer, Check.remWords])
    
    # update score
    increase = len(Check.remWords)
    Room.users[Check.user] += increase
    Check.increase = increase

    end = time.time()
    TOP = Room.height - getRow(min(Room.wordMap.values()), Room.width) if Room.wordMap else 0

    # print at terminal(for test)
    printWordTable(Room.gameTable, Room.height, Room.width)

    print(f"answer checked in {C.Cyan}{end - start}{C.End} secs")
    print(f"try {C.Cyan}{Room.tries}{C.End}, user: {C.Cyan}{Check.user}{C.End}, answer: {C.Cyan}{Check.answer}{C.End}")
    print(f"{C.Cyan}{len(Check.remWords)}{C.End} words removed: {C.Cyan}{Check.remWords}{C.End}")
    print(f"{C.Cyan}{sum(len(Room.rowMap[row]) for row in range(Room.height))}{C.End} words in table")
    print(f"top word in {C.Cyan}{TOP}{C.End} th rows\n\n")
    print(f"{C.Blue}ANSWER CHECKED{C.End}\n\n")

    return Check


# request and response body
class FinishBody(BaseModel):
    type: str
    roomId: str
    times: float
    scores: Optional[list] = None       # [[rank, user, score, contr], ...]
    answerLog: Optional[list] = None    # [[try, answer, [removedWord, ...]], ...]
# show each user's score from first to last
# and what words removed with each answer
@app.post("/finish")
def finish(Finish: FinishBody) -> FinishBody:
    print(f"\n\n{C.Blue}FINISHING GAME{C.End}")
    print(f"{C.Cyan}{time.strftime('%Y-%m-%d %H:%M:%S')}{C.End}")
    print(f"room {C.Cyan}{Finish.roomId}{C.End}")
    start = time.time()

    # get room data and dictionary
    global Rooms
    Room = Rooms[Finish.roomId]
    Room.times = Finish.times

    # user's score in score descending order
    scores = sorted([[user, score] for user, score \
        in Room.users.items()], key=lambda x: -x[1])
    # put rank at first
    TOTAL = sum(score[1] for score in scores)
    Finish.scores = [[rank, user, score,
                      int(score / TOTAL * 100) if TOTAL != 0 else 0] \
                          for rank, (user, score) in enumerate(scores, start=1)]

    # answer log and game time
    Finish.answerLog = Room.answerLog
    Finish.times = Room.times

    end = time.time()
    print(f"game data analyzed in {C.Cyan}{end - start}{C.End} secs")
    print(f"played {C.Cyan}{Room.times}{C.End} secs, {C.Cyan}{Room.tries}{C.End} tries")
    print(f"total {C.Cyan}{TOTAL}{C.End} words removed")
    for rank, user, score, contr in Finish.scores:
        print(f"rank {C.Cyan}{rank}{C.End}: {C.Cyan}{user}{C.End}, contributed: {C.Cyan}{score}({contr}%){C.End}")
    print(f"{C.Blue}GAME FINISHED{C.End}\n\n")
    
    # delete room data
    del(Rooms[Finish.roomId])
    
    return Finish


# sentry
@app.get("/sentry-debug")
async def trigger_error():
    division_by_zero = 1 / 0
