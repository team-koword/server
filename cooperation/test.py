import os
import json
with open(os.path.dirname(__file__) + "/words.json", "r", encoding="utf8") as file:
	WordDict = json.load(file)


import fasttext
simModel = fasttext.load_model(os.path.dirname(__file__) + "/model.bin")


from collections import defaultdict
class RoomData:
    def __init__(self) -> None:
        self.roomId: str = ""
        self.gameTable = defaultdict(lambda: "  ")  # {loc: char, ...}
        self.wordMap = defaultdict(int)            # {word: loc, ...}
        self.rowMap = defaultdict(list)           # {row: [words], ...}
        self.height: int = 0
        self.width: int = 0
        self.tick: float = 0                          # next word per tick seconds
        self.users = defaultdict(int)               # {user: score, ...}
        self.tries: int = -1                        # will be 0 when game initialized
        self.answerLog: list = list()               # [[answer, [removed words]], ...]
Rooms = defaultdict(RoomData)


from coop_mode_functions import *
from coop_mode_modeling import *


SIZE = 11
def init(roomId = "room01", size = SIZE):
    global Rooms
    Room = Rooms[roomId]
    Room.tries = 0
    Room.height, Room.width = size, size
    
    initWordTable(Room.gameTable, Room.height, Room.width)

    # printWordTable(Room.gameTable, Room.height, Room.width)


def next(roomId = "room01"):
    global Rooms
    Room = Rooms[roomId]
    NEW, OVER = -1, 0

    from random import choice, randint
    length = randint(2, 5)
    while True:
        word = choice(WordDict[str(length)])
        if word not in Room.wordMap.keys():
            break
    left = randint(0, Room.width - length)

    for i in range(len(word)):
        Room.gameTable[left - Room.width + i] = word[i]
    Room.wordMap[word] = left - Room.width
    Room.rowMap[NEW].append(word)

    fall = fallWord(Room.gameTable, Room.wordMap, Room.rowMap, 
                    Room.height, Room.width, word, left)

    status = "gameover" if fall == OVER else "continue"

    printWordTable(Room.gameTable, Room.height, Room.width)
    # print(f"wordMap: {Room.wordMap}")
    # print(f"rowMap: {Room.rowMap}")

    if status == "gameover":
        print("GAME OVER")
        finish()

    print(f"status: {status}")
    print(f"{sum(len(Room.rowMap[row]) for row in range(Room.height))} words in table")
    print(f"top word in {Room.height - getRow(min(Room.wordMap.values()), Room.width)} th rows\n\n")


def check(answer, roomId = "room01"):
    global Rooms, WordDict
    Room = Rooms[roomId]
    Room.tries += 1

    removedWords = getSimWords(simModel, list(Room.wordMap.keys()), answer)
    if answer in removedWords:
        removedWords.remove(answer)
    Room.answerLog.append([Room.tries, answer, removedWords])

    moveInfo = list()
    if removedWords:
        removeWords(Room.gameTable, Room.wordMap, Room.rowMap, 
                    Room.height, Room.width, removedWords)

        for row in range(Room.height - 2, -1, -1):
            words = Room.rowMap[row][:]
            for word in words:
                fall = fallWord(Room.gameTable, Room.wordMap, Room.rowMap, 
                                Room.height, Room.width, word)
                if fall:
                    moveInfo.append([word, fall])

    printWordTable(Room.gameTable, Room.height, Room.width)
    # print(f"wordMap: {Room.wordMap}")
    # print(f"rowMap: {Room.rowMap}")

    print(f"try: {Room.tries}, answer: {answer}")
    print(f"{len(removedWords)} words removed: {removedWords}")
    print(f"{sum(len(Room.rowMap[row]) for row in range(Room.height))} words in table")
    print(f"top word in {Room.height - getRow(min(Room.wordMap.values()), Room.width)} th rows\n\n")

    return


def finish(roomId = "room01"):
    global Rooms
    Room = Rooms[roomId]
    
    scores = sorted([[user, score] for user, score \
        in Room.users.items()], key=lambda x: -x[1])
    # put rank at first
    scores = [[rank, user, score] for rank, (user, score) \
        in enumerate(scores, start=1)]

    # answer log
    answerLog = Room.answerLog
    
    # total count for removed words
    TOTAL = sum(score[2] for score in scores)
    
    print(f"{Room.tries} tries")
    print(f"total {TOTAL} words removed")
    for rank, user, score in scores:
        print(f"rank {rank}: {user}, score: {score}")

    exit()


TICK = 0.5
def play():
    import threading
    import time

    def next_loop(delay = TICK):
        while True:
            next()
            time.sleep(delay)

    def check_loop():
        while True:
            answer = input()
            check(answer)

    print("GAME START")
    init()
    threading.Thread(target=next_loop).start()
    threading.Thread(target=check_loop).start()




# init()
# next()

play()
