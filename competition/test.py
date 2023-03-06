import os
import json
def get_json(fileName: str) -> dict:
    dirPath = os.path.dirname(os.path.realpath(__file__)) + "/"
    with open(dirPath + fileName, "r", encoding="utf8") as file:
        json_file = json.load(file)
    return json_file
FirstDict = get_json("chars.json")  # {first: {len: [words], ...}, ...}
LastDict = get_json("lasts.json")   # {last: {first: {len: [words], ...}, ...}, ...}
WordDict = get_json("words.json")   # {len: [words], ...}
FindDict = get_json("finds.json")   # {first: {len: [words], ...}, ...}


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
    global Rooms, FirstDict, WordDict, FindDict
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
    getGameData(FirstDict, LastDict, WordDict, Room.gameTable, Room.wordMap, adds, 
                Room.height, Room.width)
    moves.append(adds)

    # print at terminal(for test)
    printGameTable(Room.gameTable, Room.height, Room.width)
    wordList = Room.wordMap.keys()
    print(f"{len(wordList)} words in table: {wordList}")


def check(answer, roomId = "room01"):
    global Rooms, FirstDict, FindDict
    Room = Rooms[roomId]
    Room.turns += 1

    # get words in game table
    wordList = list(Room.wordMap.keys())
    # if the answer not in dictionary
    if answer not in FindDict[answer[0]][str(len(answer))]:
        remWords = []
    # if the answer in word table, remove only the word(includes duplicated)
    elif answer in wordList:
        remWords = [answer]
    # get similar words in word table
    else:
        remWords = getSimWords(simModel, wordList, answer)
        for word in remWords:
            if word not in wordList:
                remWords.remove(word)
    print(remWords)

    # update room data
    moves = list()
    updateGameData(FirstDict, LastDict, WordDict, Room.gameTable, Room.wordMap, 
                   remWords, moves, Room.height, Room.width)

    # update user score and answer log
    increase = len(remWords)
    increase = increase
    Room.answerLog.append([Room.turns, answer, remWords])

    # reset table if words in table less than standard count
    MIN = 20
    if len(list(Room.wordMap.keys())) < MIN:
        # set move information for all cells -> empty
        SIZE = Room.height * Room.width
        removes = [[i, SIZE, Room.gameTable[i]] for i in range(SIZE - 1, -1, -1)]
        moves.append(removes)
        # reset gameTable
        Room.gameTable = defaultdict(list)
        initGameTable(Room.gameTable, Room.height, Room.width)
        adds = list()
        getGameData(FirstDict, LastDict, WordDict, Room.gameTable, Room.wordMap, adds, 
                    Room.height, Room.width)
        moves.append(adds)

    # print at terminal(for test)
    for i, move in enumerate(moves):
        if i == 0:
            print(f"removes: {move}")
        elif i == 1:
            print(f"falls: {move}")
        elif i == 2:
            print(f"adds: {move}")
        elif i == 3:
            print(f"(reset)removes: {move}")
        elif i == 4:
            print(f"(reset)adds: {move}")
    printGameTable(Room.gameTable, Room.height, Room.width)
    wordList = Room.wordMap.keys()
    print(f"{len(wordList)} words in table: {wordList}")

init()
while True:
    answer = input()
    check(answer)
