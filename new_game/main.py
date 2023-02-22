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
# get json data
print(f"LOADING DATA: {C.Cyan}dictionary{C.End}")
start = time.time()

import json
try:
    with open("./words.json", "r", encoding="utf8") as file:
        WordData = json.load(file)
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

print(f"{C.Blue}GAME SERVER IS READY{C.End}\n\n")


# modeling functions module
from new_modeling import *




## game data
from collections import defaultdict
# each room data
class RoomData:
    def __init__(self) -> None:
        self.roomId: str = ""
        self.wordTable = defaultdict(lambda: "  ")  # {loc: char, ...}
        self.wordMap = defaultdict(int)            # {word: loc, ...}
        self.wordRows = defaultdict(list)           # {row: [words], ...}
        self.height: int = 0
        self.width: int = 0
        self.tick: float = 0                          # next word per tick seconds
        self.users = defaultdict(int)               # {user: score, ...}
        self.tries: int = -1                        # will be 0 when game initialized
        self.answerLog: list = list()               # [[answer, [removed words]], ...]


# rooms data
Rooms = defaultdict(RoomData)


# game functions module
from new_game_functions import *




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
    roomId: str
    size: int
    tick: float
    users: list
# initialize new game in size(height * width)
@app.post("/init")
def init(Init: InitBody) -> InitBody:
    print(f"\n\n{C.Blue}NEW GAME STARTED{C.End}")
    print(f"room {C.Cyan}{Init.roomId}{C.End}")
    start = time.time()

    # get room data and initialize
    global Rooms
    Room = Rooms[Init.roomId]
    Room.roomId = Init.roomId
    Room.tries = 0
    Room.height, Room.width = Init.size, Init.size
    Room.tick = Init.tick
    START = 0
    for user in Init.users:
        Room.users[user] = START

    # initialize word table
    initWordTable(Room.wordTable, Room.height, Room.width)

    # print at terminal(for test)
    printWordTable(Room.wordTable, Room.height, Room.width)

    end = time.time()
    print(f"game initialized in {C.Cyan}{end - start}{C.End} secs")
    print(f"a word falls every {C.Cyan}{Room.tick}{C.End} secs")
    print(f"{C.Blue}GAME START{C.End}\n\n")
    
    return Init


# request and response body
class NextBody(BaseModel):
    roomId: str
    type: Optional[str] = None	# "continue" | "gameover"
    word: Optional[str] = None
    left: Optional[int] = None
    length: Optional[int] = None
    fall: Optional[int] = None
# put next new word
# if the new word reach to top, game over
@app.post("/next")
def next(Next: NextBody) -> NextBody:
    print(f"\n\n{C.Blue}NEW WORD FALLING{C.End}")
    print(f"room {C.Cyan}{Next.roomId}{C.End}")
    start = time.time()

    # get room data and dictionary
    global Rooms, WordData
    Room = Rooms[Next.roomId]
    NEW, OVER = -1, 0

    # get random word with random length, which falls at random column
    from random import choice, randint
    Next.length = randint(2, 5)
    while True:
        Next.word = choice(WordData[str(Next.length)])
        if Next.word not in Room.wordMap.keys():
            break
    Next.left = randint(0, Room.width - Next.length)
    
    # set game information with dummy value for fallWord function
    for i in range(len(Next.word)):
        Room.wordTable[Next.left - Room.width + i] = Next.word[i]
    Room.wordMap[Next.word] = Next.left - Room.width
    Room.wordRows[NEW].append(Next.word)
    
    # word falls down
    Next.fall = fallWord(Room.wordTable, Room.wordMap, Room.wordRows, 
                         Room.height, Room.width, Next.word, Next.left)
    
    # game over if next word reached to top
    Next.type = "gameover" if Next.fall == OVER else "continue"
    if Next.type == "gameover":
        print(f"\n{C.red}GAMEOVER{C.End}\n")

    end = time.time()

    # print at terminal(for test)
    printWordTable(Room.wordTable, Room.height, Room.width)

    print(f"next word fell in {C.Cyan}{end - start}{C.End} secs")
    print(f"{C.Cyan}{sum(len(Room.wordRows[row]) for row in range(Room.height))}{C.End} words in table")
    print(f"top word in {C.Cyan}{Room.height - getRow(min(Room.wordMap.values()), Room.width)}{C.End} th rows")
    print(f"{C.Blue}NEXT WORD FELL{C.End}\n\n")

    return Next


# request and response body
class CheckBody(BaseModel):
    roomId: str
    user: str
    answer: str
    removedWords: Optional[list] = None # [word, ...]
    moveInfo: Optional[list] = None     # [[word: str, fall: int], ...]
# check and remove words similar with the answer
# if the answer in word table, lock it
@app.post("/check")
def check(Check: CheckBody) -> CheckBody:
    print(f"\n\n{C.Blue}CHECKING ANSWER{C.End}")
    print(f"room {C.Cyan}{Check.roomId}{C.End}")
    start = time.time()

    # get room data and dictionary
    global Rooms, WordData
    Room = Rooms[Check.roomId]
    Room.tries += 1

    # get words to remove similar with the answer
    Check.removedWords = getSimWords(simModel, list(Room.wordMap.keys()), Check.answer)
    # lock the answer if exists in word table
    if Check.answer in Check.removedWords:
        Check.removedWords.remove(Check.answer)
    # update answer log
    Room.answerLog.append([Room.tries, Check.answer, Check.removedWords])

    # set moveInfo
    Check.moveInfo = list()
    if removeWords:
        # remove similar words
        removeWords(Room.wordTable, Room.wordMap, Room.wordRows, 
                    Room.height, Room.width, Check.removedWords)

        # words above removed words fall down
        for row in range(Room.height - 2, -1, -1):
            words = Room.wordRows[row][:]
            for word in words:
                fall = fallWord(Room.wordTable, Room.wordMap, Room.wordRows, 
                                Room.height, Room.width, word)
                if fall:
                    Check.moveInfo.append([word, fall])

    end = time.time()

    # print at terminal(for test)
    printWordTable(Room.wordTable, Room.height, Room.width)

    print(f"answer checked in {C.Cyan}{end - start}{C.End} secs")
    print(f"try {C.Cyan}{Room.tries}{C.End}, user: {C.Cyan}{Check.user}{C.End}, answer: {C.Cyan}{Check.answer}{C.End}")
    print(f"{C.Cyan}{len(Check.removedWords)}{C.End} words removed: {C.Cyan}{Check.removedWords}{C.End}")
    print(f"{C.Cyan}{sum(len(Room.wordRows[row]) for row in range(Room.height))}{C.End} words in table")
    print(f"top word in {Room.height - getRow(min(Room.wordMap.values()), Room.width)} th rows\n\n")
    print(f"{C.Blue}ANSWER CHECKED{C.End}\n\n")

    return Check