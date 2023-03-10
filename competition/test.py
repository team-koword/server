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

    # initialize table
    Room.gameTable, Room.wordMap \
        = initGameData(Room.gameTable, Room.wordMap, Room.height, Room.width)

    # get game data
    moves = list()
    adds = list()
    Room.gameTable, Room.wordMap, adds = \
        getGameData(FirstDict, LastDict, WordDict, 
                    Room.gameTable, Room.wordMap, adds, 
                    Room.height, Room.width)
    moves.append(adds)

    # print at terminal(for test)
    printGameTable(Room.gameTable, Room.height, Room.width)
    wordList = list(Room.wordMap.keys())
    print(f"{len(wordList)} words in table: {wordList}")
    print(f"wordMap: {Room.wordMap}")


def check(answer, roomId = "room01"):
    global Rooms, FirstDict, FindDict
    Room = Rooms[roomId]
    Room.turns += 1

    # get words in game table
    wordList = list(Room.wordMap.keys())
    # if the answer not in dictionary
    if str(len(answer)) not in FindDict \
        or answer[0] not in FindDict[str(len(answer))] \
        or answer not in FindDict[str(len(answer))][answer[0]]:
        remWords = []
    # if the answer in word table, remove only the word(includes duplicated)
    elif answer in wordList:
        remWords = [answer]
    # get similar words in word table
    else:
        remWords = getSimWords(simModel, wordList, answer)

    # update room data
    moves = list()
    Room.gameTable, Room.wordMap, moves \
        = updateGameData(FirstDict, LastDict, WordDict,
                         Room.gameTable, Room.wordMap, moves, 
                         remWords, Room.height, Room.width)
    print(f"{len(list(Room.wordMap.keys()))} words in table")

    # update user score and answer log
    increase = len(remWords)
    increase = increase
    Room.answerLog.append([Room.turns, answer, remWords])
    print(f"wordMap: {Room.wordMap}")

    # reset table if words in table less than standard count
    MIN = 40
    SIZE = Room.height * Room.width
    if len(list(Room.wordMap.keys())) < MIN:
        # set move information for all cells -> empty
        removes = [[i, SIZE, Room.gameTable[i][CHAR]] for i in range(SIZE - 1, -1, -1)]
        moves.append(removes)
        # reset gameTable
        Room.gameTable, Room.wordMap \
            = initGameData(Room.gameTable, Room.wordMap, Room.height, Room.width)
        adds = list()
        Room.gameTable, Room.wordMap, adds \
            = getGameData(FirstDict, LastDict, WordDict, 
                          Room.gameTable, Room.wordMap, adds, 
                          Room.height, Room.width)
        moves.append(adds)
        print(f"too little words in table, TABLE REFRESHED")

    # print at terminal(for test)
    for i, move in enumerate(moves):
        if i == 0:
            print(f"removes: {len(move)} {move}")
        elif i == 1:
            print(f"falls: {len(move)} {move}")
        elif i == 2:
            print(f"adds: {len(move)} {move}")
        elif i == 3:
            print(f"(reset)removes: {len(move)} {move}")
        elif i == 4:
            print(f"(reset)adds: {len(move)} {move}")
    printGameTable(Room.gameTable, Room.height, Room.width)
    
    def _error(FirstDict: dict, LastDict: dict, WordDict: dict, 
               gameTable: dict, wordMap: dict, 
               moves: list, height: int, width: int) \
        -> Tuple[dict, dict, list]:
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
        for i, move in enumerate(moves):
            if i == 0:
                print(f"removes: {len(move)} {move}")
            elif i == 1:
                print(f"falls: {len(move)} {move}")
            elif i == 2:
                print(f"adds: {len(move)} {move}")
        printGameTable(gameTable, height, width)
        return gameTable, wordMap, moves

    # initialize gameTable if removed and added chars counts different
    if len(moves[0]) != len(moves[2]):
        print(f"ERROR removes and adds counts different")
        Room.gameTable, Room.wordMap, moves \
            = _error(FindDict, LastDict, WordDict, Room.gameTable, Room.wordMap, 
                     moves, Room.height, Room.width)

    # check error if gameTable and wordMap unmatched
    flag = False
    wordList = list(Room.wordMap.keys())
    for word in wordList:
        temp = ""
        for loc in Room.wordMap[word]:
            temp += Room.gameTable[loc][CHAR]
        if word != temp:
            print(f"ERROR gameTable and wordMap different, word: {word}, locs: {Room.wordMap[word]}")
            Room.gameTable, Room.wordMap, moves \
                = _error(FindDict, LastDict, WordDict, Room.gameTable, Room.wordMap, 
                        moves, Room.height, Room.width)
            flag = True
            break
        if flag == True:
            break
        

init()
while True:
    answer = input()
    check(answer)
