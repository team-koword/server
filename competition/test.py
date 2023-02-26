import os
import json
def get_json(fileName: str) -> dict:
    dirPath = os.path.dirname(os.path.realpath(__file__)) + "/"
    with open(dirPath + fileName, "r", encoding="utf8") as file:
        json_file = json.load(file)
    return json_file
CharDict = get_json("chars.json")
WordDict = get_json("words.json")
FindDict = get_json("finds.json")


import fasttext
simModel = fasttext.load_model(os.path.dirname(__file__) + "/model.bin")


from collections import defaultdict
class RoomData:
    def __init__(self) -> None:
        self.roomId: str = ""
        self.gameTable: dict[int, list] = defaultdict(list) # {loc: [char, connections], ...}
        self.wordMap: dict[str, list] = defaultdict(list)   # {word: [loc, ...], ...}
        self.height: int = 0
        self.width: int = 0
        self.users: dict[str, int] = defaultdict(int)       # {user: score, ...}
        self.turns: int = -1                                # will be 0 when game initialized
        self.answerLog: list = list()                       # [[answer, [removes words]], ...]
Rooms = defaultdict(RoomData)


from comp_mode_functions import *
from comp_mode_modeling import *


EMPTY, DISCNT = "  ", "X"
CHAR, CONN = 0, 1
SIZE = 11
def init(roomId = "room01", size = SIZE):
    global Rooms, CharDict, WordDict, FindDict
    Room = Rooms[roomId]
    Room.roomId = roomId
    Room.turns = 0
    Room.height, Room.width = size, size
    Room.gameTable = defaultdict(list)

    # initialize table
    initGameTable(Room.gameTable, Room.height, Room.width)

    # get game data
    moves = list()
    adds = list()
    getGameData(CharDict, WordDict, Room.gameTable, Room.wordMap, adds, 
                Room.height, Room.width)
    moves.append(adds)

    # print at terminal(for test)
    printGameTable(Room.gameTable, Room.height, Room.width)


def check(roomId = "room01", answer = "사과"):
    global Rooms, CharDict, FindDict
    Room = Rooms[roomId]
    Room.turns += 1

    # get words in game table
    wordList = list(Room.wordMap.keys())
    # if the answer not in dictionary
    if answer not in FindDict[answer[0]][str(len(answer))]:
        removedWords = []
    # if the answer in word table, remove only the word(includes duplicated)
    elif answer in wordList:
        removedWords = [answer]
    # get similar words in word table
    else:
        removedWords = getSimWords(simModel, wordList, answer)
    print(removedWords)

    # update room data
    moves = list()
    updateGameData(CharDict, WordDict, Room.gameTable, Room.wordMap, 
                   removedWords, moves, Room.height, Room.width)

    # update user score and answer log
    increase = len(removedWords)
    increase = increase
    Room.answerLog.append([Room.turns, answer, removedWords])

    # reset table if words in table less than standard count
    MIN = 20
    if len(list(Room.wordMap.keys())) < MIN:
        SIZE = Room.height * Room.width
        removes = [[i, SIZE, Room.gameTable[i]] for i in range(SIZE - 1, -1, -1)]
        moves.append(removes)
        Room.gameTable = defaultdict(list)
        initGameTable(Room.gameTable, Room.height, Room.width)
        adds = list()
        getGameData(CharDict, WordDict, Room.gameTable, Room.wordMap, adds, 
                    Room.height, Room.width)
        moves.append(adds)

    # print at terminal(for test)
    printGameTable(Room.gameTable, Room.height, Room.width)
    print(*moves)

init()
check() 