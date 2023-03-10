from typing import Tuple
from collections import defaultdict
from random import choice, shuffle


# global variables
EMPTY, DISCNT = "  ", "X"
CHAR, CONN = 0, 1


# loc = row * width + col
def getLoc(row: int, col: int, width: int) -> int:
    return row * width + col


# row = loc // width
def getRow(loc: int, width: int) -> int:
    return loc // width


# col = loc % width
def getCol(loc: int, width: int) -> int:
    return loc % width


# get rightwards distance include itself
# flag CHAR for empty cells, CONN for not connected cells
def getRightDist(gameTable: dict, loc: int, flag: int,
                 height: int, width: int) -> int:
    FLAG = [EMPTY, DISCNT]
    dist = 1
    while getCol(loc, width) + dist < width:
        if gameTable[loc + dist][flag] != FLAG[flag]:
            break
        dist += 1
    return dist


# get downwards distance include itself
# flag CHAR for empty cells, CONN for not connected cells
def getDownDist(gameTable: dict, loc: int, flag: int,
                height: int, width: int) -> int:
    FLAG = [EMPTY, DISCNT]
    dist = 1
    while getRow(loc, width) + dist < height:
        if gameTable[loc + dist * width][flag] != FLAG[flag]:
            break
        dist += 1
    return dist


# init gameTable and wordMap
def initGameData(gameTable: dict, wordMap: dict, height: int, width: int) \
    -> Tuple[dict, dict]:
    SIZE = height * width
    gameTable = defaultdict(list)
    for loc in range(SIZE):
        gameTable[loc] = [EMPTY, DISCNT]
    wordMap = defaultdict(list)
    return gameTable, wordMap


# put words in empty cells on table
def getGameData(FirstDict: dict, LastDict: dict, WordDict: dict,
                gameTable: dict, wordMap: dict, moves: list, 
                height: int, width: int) \
    -> Tuple[dict, dict, list]:
    # local variables
    SIZE = height * width
    RIGHT, DOWN, NODIR = 1, width, 0

    # get random direction and following information -> loc, dir, dist, first, last
    def _dir(FirstDict: dict, LastDict: dict, gameTable: dict, loc: int, 
             height: int, width: int) \
        -> Tuple[int, int, int, str, str]:
        # get rightwards word information
        def __right(FirstDict: dict, LastDict: dict, gameTable: dict, loc: int,
                height: int, width: int) \
            -> Tuple[int, int, str, str]:
            first, last = str(), str()
            # get distance
            dist = getRightDist(gameTable, loc, CHAR, height, width)
            # check right cell first(for using LastDict)
            if getCol(loc, width) + dist < width - 1 \
                and gameTable[loc + dist][CONN] == DISCNT \
                and gameTable[loc + dist][CHAR] in LastDict:
                last = gameTable[loc + dist][CHAR]
                dist += 1
            # check left cell
            if getCol(loc, width) > 0 and gameTable[loc - 1][CONN] == DISCNT \
                and (((last and dist < 5 and str(dist + 1) in LastDict[last] \
                        and gameTable[loc - 1][CHAR] in LastDict[last][str(dist + 1)])) \
                    or (not last and gameTable[loc - 1][CHAR] in FirstDict)):
                first = gameTable[loc - 1][CHAR]
                dist += 1
                loc -= 1
            return loc, dist, first, last

        # get downwards word information
        def __down(LastDict: dict, gameTable: dict, loc: int,
                height: int, width: int) \
            -> Tuple[int, int, str, str]:
            first, last = str(), str()
            # get distance
            dist = getDownDist(gameTable, loc, CHAR, height, width)
            # check below cell
            if getRow(loc, width) + dist < height - 1 \
                and gameTable[loc + dist * width][CONN] == DISCNT \
                and gameTable[loc + dist * width][CHAR] in LastDict:
                last = gameTable[loc + dist * width][CHAR]
                dist += 1
            return loc, dist, first, last

        first, last = str(), str()
        # get random direction
        dir = choice([RIGHT, RIGHT, RIGHT, RIGHT, DOWN])
        # check rightwards first
        if dir == RIGHT:
            loc, dist, first, last \
                = __right(FirstDict, LastDict, gameTable, loc, height, width)
            if dist == 1:
                dir = DOWN
                loc, dist, first, last \
                    = __down(LastDict, gameTable, loc, height, width)
        # check downwards
        else:
            loc, dist, first, last \
                = __down(LastDict, gameTable, loc, height, width)
            if dist == 1:
                dir = RIGHT
                loc, dist, first, last \
                    = __right(FirstDict, LastDict, gameTable, loc, height, width)
        # if both directions unavailable
        if dist == 1:
            dir = NODIR
        return loc, dir, dist, first, last

    # get a random word end with the last character
    def _randlast(LastDict: dict, wordMap: dict, 
                  last: str, first: str, dist: int) -> str:
        if first:
            words = list(LastDict[last][str(dist)][first])
            shuffle(words)
            for word in words:
                if word not in wordMap:
                    return word
        else:
            if str(dist) in LastDict[last]:
                firsts = list(LastDict[last][str(dist)])
                shuffle(firsts)
                for first in firsts:
                    words = LastDict[last][str(dist)][first]
                    shuffle(words)
                    for word in words:
                        if word not in wordMap:
                            first = ""
                            return word
        return ""

    # get a random word start with the first character
    def _randfirst(FirstDict: dict, wordMap: dict, first: str, dist: int) -> str:
        dist = min(dist, 5)
        lens = list(FirstDict[first])
        shuffle(lens)
        for len in lens:
            if int(len) > dist:
                continue
            words = list(FirstDict[first][len])
            shuffle(words)
            for word in words:
                if word not in wordMap:
                    return word
        return ""

    # get a random single character
    def _randchar(FirstDict: dict) -> str:
        return choice(list(FirstDict))

    # get a random word without using the first or last letter
    def _randword(WordDict: dict, wordMap: dict, dist: int) -> str:
        # set random length list with calibrating
        dist = min(dist, 5)
        end = [50, 74, 98, 99][dist - 2]
        # get a random length
        rand = choice(range(end))
        if rand <= 50:
            length = "2"
        elif 50 < rand <= 74:
            length = "3"
        elif 74 < rand <= 98:
            length = "4"
        else:
            length = "5"
        # get a random word
        while True:
            word = choice(WordDict[length])
            if word not in wordMap:
                break
        return word

    # put gameTable, wordMap, moves with the word in the direction
    def _put(gameTable: dict, wordMap: dict, loc: int, word: str, dir: int) -> None:
        # put data in wordMap {word: [locs], ...}
        if dir != NODIR:
            wordMap[word] = list(range(loc, loc + len(word) * dir, dir))
        # put each character and connection of the word
        for i, char in enumerate(word):
            if dir == NODIR:
                gameTable[loc] = [word, DISCNT]
            # fill the word in gameTable {loc: [char, conn], ...}
            else:
                if i == 0:
                    conn = "R" if dir == RIGHT else "D"
                elif i == len(word) - 1:
                    conn = "L" if dir == RIGHT else "U"
                else:
                    conn = "LR" if dir == RIGHT else "UD"
                gameTable[loc + i * dir] = [char, conn]
        return

    # put data in moves [[dep, arr, char], ...]
    def _move(gameTable: dict, moves: list, loc: int, word: str, dir: int, 
              height: int, width: int) -> None:
        for i, char in enumerate(word):
            arr = loc + i * dir
            fall = getDownDist(gameTable, loc + (len(word) - 1) * dir, CHAR, 
                               height, width)
            depth = 1 if dir == RIGHT else len(word)
            dep = arr - (getRow(loc, width) + fall + depth) * width
            moves.append([dep, arr, char])

    # find single characters can be a word with other single character
    def _recycle(FirstDict: dict, gameTable: dict, wordMap: dict, 
              height: int, width: int) -> None:
        # get word candidates in direction
        def __find(FirstDict: dict, gameTable: dict, 
                   loc: int, dir: int, dist: int) -> str:
            words, word = list(), str()
            for length in range(dist):
                word += gameTable[loc + length * dir][CHAR]
                if not 0 < length < 5:
                    continue
                if word[0] in FirstDict and str(len(word)) in FirstDict[word[0]] \
                    and word in FirstDict[word[0]][str(len(word))]:
                    words.append(word)
            # return longest word, not duplicated with words on table
            while words:
                word = words.pop()
                if word not in wordMap:
                    return word
            return ""

        # find each single character if able to be a word
        for loc in range(SIZE):
            # continue if the cell is empty or already connected
            if gameTable[loc][CHAR] == EMPTY or gameTable[loc][CONN] != DISCNT:
                continue
            # get a direction and distance
            rightDist = getRightDist(gameTable, loc, CONN, height, width)
            downDist = getDownDist(gameTable, loc, CONN, height, width)
            dir = RIGHT if rightDist >= 2 else DOWN
            if dir == DOWN and downDist == 1:
                dir = NODIR
            dist = rightDist if dir == RIGHT else downDist
            # unable to put a word
            if dir == NODIR:
                continue
            # check if possible to put a word
            word = __find(FirstDict, gameTable, loc, dir, dist)
            if word:
                _put(gameTable, wordMap, loc, word, dir)
                continue
            # try again in the other direction
            if dir == RIGHT:
                dir = DOWN
            dist = downDist
            if dist < 2:
                continue
            # check if possible to put a word
            word = __find(FirstDict, gameTable, loc, dir, dist)
            if word:
                _put(gameTable, wordMap, loc, word, dir)


    # getGameData(FirstDict, LastDict, WordDict,
    #             gameTable, wordMap, moves, height, width)
    # TODO: fill empty cells
    for loc in range(SIZE):
        # continue if the cell already filled
        if gameTable[loc][CHAR] != EMPTY:
            continue

        # get direction and distance, check if possible to connect with adjacent cells
        loc, dir, dist, first, last = _dir(FirstDict, LastDict, gameTable, loc, 
                                           height, width)
        word = str()

        # try to use the last letter
        if last:
            word = _randlast(LastDict, wordMap, last, first, dist)
            if not word:
                dist -= 1
                last = ""
                if dist == 1:
                    dir = NODIR

        # try to use the first letter
        if first and not word:
            word = _randfirst(FirstDict, wordMap, first, dist)
            if not word:
                loc += 1
                dist -= 1
                first = ""
                if dist == 1:
                    dir = NODIR

        # not using first or last letter
        if not word:
            # get a random character if unable to put a word
            if dist == 1 or dir == NODIR:
                word = _randchar(FirstDict)
            # get a random word without using the first or last letter
            else:
                word = _randword(WordDict, wordMap, dist)

        # put word in gameTable
        _put(gameTable, wordMap, loc, word, dir)

        # put moves
        if first:
            word = word[1:]
            loc += 1
        if last:
            word = word[:-1]
        _move(gameTable, moves, loc, word, dir, height, width)
    
    # TODO: try to get words with single characters
    _recycle(FirstDict, gameTable, wordMap, height, width)

    moves.sort(key=lambda x: x[1])
    return gameTable, wordMap, moves


def updateGameData(FirstDict: dict, LastDict: dict, WordDict: dict,
                   gameTable: dict, wordMap: dict, moves: list,
                   remWords: list, height: int, width: int) \
    -> Tuple[dict, dict, list]:
    # local variables
    SIZE = height * width

    # get word by loc from wordMap
    def __get(wordMap: dict, loc: int) -> Tuple[str, list]:
        for word, locs in wordMap.items():
            if locs[-1] == loc:
                return word, locs[:]
        return "", []

    # fall a rightwards word: check word still connected after falls
    def _rightwards(gameTable: dict, wordMap: dict, falls: list, loc: int, 
                    height: int, width: int) -> None:
        # get falling distances of each character
        word, locs = __get(wordMap, loc)
        _falls = list()
        for i in range(len(word)):
            _falls.append(getDownDist(gameTable, locs[i], CHAR, height, width) - 1)
        # word still connected
        if _falls.count(_falls[0]) == len(word):
            # continue if word not falling
            if _falls[0] == 0:
                return
            # update locations in wordMap
            for i in range(len(word)):
                    wordMap[word][i] += _falls[0] * width
        # if word disconnected, remove word in wordMap and update connection
        else:
            del(wordMap[word])
            for i in range(len(word)):
                gameTable[locs[i]][CONN] = DISCNT
        # update gameTable and moves
        for i in range(len(word) - 1, -1, -1):
            if _falls[i] == 0:
                continue
            falls.append([locs[i], locs[i] + _falls[i] * width, word[i]])
            gameTable[locs[i] + _falls[i] * width] = gameTable[locs[i]]
            gameTable[locs[i]] = [EMPTY, DISCNT]

    # fall a downwards word: entire word falls
    def _downwards(gameTable: dict, wordMap: dict, falls: list, loc: int, 
                   height: int, width: int) -> None:
        # get falling distance of whole word
        word, locs = __get(wordMap, loc)
        fall = getDownDist(gameTable, loc, CHAR, height, width) - 1
        if fall == 0:
            return
        # update gameTable and moves
        for i in range(len(word) - 1, -1, -1):
            falls.append([locs[i], locs[i] + fall * width, word[i]])
            gameTable[locs[i] + fall * width] = gameTable[locs[i]]
            gameTable[locs[i]] = [EMPTY, DISCNT]
            wordMap[word][i] += fall * width

    # fall a single character
    def _nowards(gameTable: dict, falls: list, loc: int, 
                 height: int, width: int) -> None:
        fall = getDownDist(gameTable, loc, CHAR, height, width) - 1
        if fall == 0:
            return
        falls.append([loc, loc + fall * width, gameTable[loc][CHAR]])
        gameTable[loc + fall * width] = gameTable[loc]
        gameTable[loc] = [EMPTY, DISCNT]


    # updateGameData(FirstDict, LastDict, WordDict,
    #                gameTable, wordMap, remWords, moves, height, width) -> None:
    # TODO: remove words in remWords
    removes = list()
    for i, word in enumerate(remWords):
        locs = wordMap.pop(word)
        for j, loc in enumerate(locs):
            if gameTable[loc][CHAR] != EMPTY:
                removes.append([loc, SIZE + i, word[j]])
                gameTable[loc] = [EMPTY, DISCNT]
    # print("removed")
    # printGameTable(gameTable, height, width)

    # TODO: fall characters remaining on gameTable
    falls = list()
    for loc in range(SIZE - width - 1, - 1, -1):
        # continue if cell is empty or not the last letter of word(include single character)
        if gameTable[loc][CHAR] == EMPTY \
            or gameTable[loc][CONN] not in ["L", "U", "X"]:
            continue
        if gameTable[loc][CONN] == "L":
            _rightwards(gameTable, wordMap, falls, loc, height, width)
        elif gameTable[loc][CONN] == "U":
            _downwards(gameTable, wordMap, falls, loc, height, width)
        else:
            _nowards(gameTable, falls, loc, height, width)
    # print("falled")
    # printGameTable(gameTable, height, width)

    # TODO: add new characters in empty cells
    adds = list()
    getGameData(FirstDict, LastDict, WordDict, gameTable, wordMap,
                adds, height, width)
    # print("added")
    # printGameTable(gameTable, height, width)

    # update moves
    moves.append(removes)
    moves.append(sorted(falls, key=lambda x: -x[1]))
    moves.append(sorted(adds, key=lambda x: -x[1]))

    return gameTable, wordMap, moves


# print gameTable in terminal(for test)
def printGameTable(gameTable: dict, height: int, width: int) -> None:
    for row in range(height):
        for col in range(width):
            loc = row * width + col
            cell = gameTable[loc][CHAR]
            # print connection
            conn = gameTable[loc][CONN]
            cell += conn
            if len(conn) == 1:
                cell += " "
            # print location
            DIGIT = len(str(height * width))
            cell = str(loc).zfill(DIGIT) + cell
            print(cell, end=" ")
        print()
    print()
