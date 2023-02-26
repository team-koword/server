from typing import Optional, Union, Tuple, TypeVar
from random import choice, randint
from collections import defaultdict


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


# get rightwards distance exclude itself
# flag CHAR for empty cells, CONN for not connected cells
def getRightDist(gameTable: dict, loc: int, flag: int,
                 height: int, width: int) -> int:
    FLAG = [EMPTY, DISCNT]
    dist = 1
    while getCol(loc, width) + dist < width:
        if gameTable[loc + dist][flag] == FLAG[flag]:
            dist += 1
        else:
            break
    return dist - 1


# get downwards distance exclude itself
# flag CHAR for empty cells, CONN for not connected cells
def getDownDist(gameTable: dict, loc: int, flag: int,
                height: int, width: int) -> int:
    FLAG = [EMPTY, DISCNT]
    dist = 1
    while getRow(loc, width) + dist < height:
        if gameTable[loc + dist * width][flag] == FLAG[flag]:
            dist += 1
        else:
            break
    return dist - 1


# get a random character
def getRandChar(CharDict: dict) -> str:
    return choice(list(CharDict))


# get a random word, with length less or equal than distance
def getRandWord(WordDict: dict, dist: int) -> str:
    dist = min(dist, 5)
    length = str(randint(2, dist))
    word = choice(WordDict[length])
    return word


# init word table with empty cells
def initGameTable(gameTable: dict, height: int, width: int) -> None:
    SIZE = height * width

    for loc in range(SIZE):
        gameTable[loc] = [EMPTY, DISCNT]


# put words in empty cells on table
def getGameData(CharDict: dict, WordDict: dict, FindDict: dict,
                gameTable: dict, wordMap: dict, moves: list, 
                height: int, width: int) -> None:
    SIZE = height * width
    RIGHT, DOWN, NODIR = 1, width, 0
    # get direction right or down with distances in each direction
    def _dir(rightDist: int, downDist: int) -> int:
        ABLE, UNABLE = 2, 1
        if rightDist >= ABLE and downDist >= ABLE:
            return choice([RIGHT, RIGHT, DOWN])     # double RIGHT for calibration
        elif rightDist >= ABLE and downDist <= UNABLE:
            return RIGHT
        elif rightDist <= UNABLE and downDist >= ABLE:
            return DOWN
        else:
            return NODIR

    # put gameTable, wordMap, moves with the word in the direction
    def _put(gameTable: dict, wordMap: dict, moves: list, 
             loc: int, word: str, dir: int) -> None:
        # TODO: put data in wordMap {word: [locs], ...}
        if dir != NODIR:
            wordMap[word] = list(range(loc, loc + len(word) * dir, dir))

        # put each character and connection of the word
        for i, char in enumerate(word):
            if dir == NODIR:
                gameTable[loc] = [word, DISCNT]
            # TODO: fill the word in gameTable {loc: [char, conn], ...}
            else:
                if i == 0:
                    conn = "R" if dir == RIGHT else "D"
                elif i == len(word) - 1:
                    conn = "L" if dir == RIGHT else "U"
                else:
                    conn = "LR" if dir == RIGHT else "UD"
                gameTable[loc + i * dir] = [char, conn]

            # TODO: put data in moves [[dep, arr, char], ...]
            # calculate dep
            arr = loc + i * dir
            fall = getDownDist(gameTable, loc + (len(word) - 1) * dir, CHAR, height, width)
            depth = 1 if dir == RIGHT else len(word)
            dep = arr - (getRow(loc, width) + fall + depth) * width
            moves.append([dep, arr, char])

        return

    rightCnt, downCnt, nodirCnt = 0, 0, 0
    # TODO: fill empty cells
    for loc in range(SIZE):
        # continue if the cell already filled
        if gameTable[loc][CHAR] != EMPTY:
            continue
        # get a random direction and distance
        rightDist = getRightDist(gameTable, loc, CHAR, height, width) + 1
        downDist = getDownDist(gameTable, loc, CHAR, height, width) + 1
        dir = _dir(rightDist, downDist)
        dist = rightDist if dir == RIGHT else downDist
        if dir == RIGHT: rightCnt += 1
        elif dir == DOWN: downCnt += 1

        # get a random word(or random character if unable to put a word)
        if dir == NODIR:
            word = getRandChar(CharDict)
        else:
            while True:
                word = getRandWord(WordDict, dist)
                if word not in wordMap:
                    break
        # put each character and connection of the word
        _put(gameTable, wordMap, moves, loc, word, dir)

    # TODO: find single characters can be a word with other single character
    # get word candidates in direction
    def _cand(gameTable: dict, loc: int, dir: int, dist: int) -> list:
        words, word = list(), str()
        for length in range(dist):
            word += gameTable[loc + length * dir][CHAR]
            if length >= 1:
                words.append(word)
        return words[::-1]

    for loc in range(SIZE):
        # continue if the cell already connected
        if gameTable[loc][CONN] != DISCNT:
            continue
        # get a random direction and distance
        rightDist = getRightDist(gameTable, loc, CONN, height, width) + 1
        downDist = getDownDist(gameTable, loc, CONN, height, width) + 1
        dir = _dir(rightDist, downDist)
        dist = rightDist if dir == RIGHT else downDist
        # unable to put a word
        if dir == NODIR:
            nodirCnt += 1
            continue
        # get word candidates
        cand = _cand(gameTable, loc, dir, dist)
        # check if possible to put a word
        for word in cand:
            if word[0] not in FindDict:
                continue
            if str(len(word)) in FindDict[word[0]] \
                and word in FindDict[word[0]][str(len(word))]:
                if dir == RIGHT: rightCnt += 1
                elif dir == DOWN: downCnt += 1
                _put(gameTable, wordMap, moves, loc, word, dir)
                continue
        # try again in the other direction
        dir = list({RIGHT, DOWN} - {dir})[0]
        dist = rightDist if dir == RIGHT else downDist
        if dist < 2:
            continue
                # get word candidates
        cand = _cand(gameTable, loc, dir, dist)
        # check if possible to put a word
        for word in cand:
            if word[0] not in FindDict:
                continue
            if str(len(word)) in FindDict[word[0]] \
                and word in FindDict[word[0]][str(len(word))]:
                if dir == RIGHT: rightCnt += 1
                elif dir == DOWN: downCnt += 1
                _put(gameTable, wordMap, moves, loc, word, dir)

    moves.sort(key=lambda x: x[1])
    # print(f"rightCnt, downCnt, nodirCnt: {rightCnt}, {downCnt}, {nodirCnt}")
    return


def updateGameData(CharDict: dict, WordDict: dict, FindDict: dict,
                   gameTable: dict, wordMap: dict, 
                   remWords: list, moves: list, height: int, width: int) -> None:
    SIZE = height * width

    # TODO: remove words in remWords
    removes = list()
    for i, word in enumerate(remWords):
        if word in wordMap:
            locs = wordMap.pop(word)
            for j, loc in enumerate(locs):
                if gameTable[loc][CHAR] != EMPTY:
                    removes.append([loc, SIZE + i, word[j]])
                    gameTable[loc] = [EMPTY, DISCNT]

    # TODO: fall characters remaining on gameTable
    # get word by loc from wordMap
    def _get(wordMap: dict, loc: int) -> Tuple[str, list]:
        for word, locs in wordMap.items():
            if locs[-1] == loc:
                return word, locs[:]
        return "", []

    falls = list()
    for loc in range(SIZE - width - 1, - 1, -1):
        # continue if cell is empty or not last of word(include single character)
        if gameTable[loc][CHAR] == EMPTY \
            or gameTable[loc][CONN] not in ["L", "U", "X"]:
            continue

        # fall a rightwards word: check word still connected after falls
        if gameTable[loc][CONN] == "L":
            # get falling distances of each character
            word, locs = _get(wordMap, loc)
            _falls = list()
            for i in range(len(word)):
                _falls.append(getDownDist(gameTable, locs[i], CHAR, height, width))
            # word still connected
            if _falls.count(_falls[0]) == len(word):
                # continue if word not falling
                if _falls[0] == 0:
                    continue
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
                falls.append([locs[i], locs[i] + _falls[i] * width, word[i]])
                if _falls[i] == 0:
                    continue
                gameTable[locs[i] + _falls[i] * width] = gameTable[locs[i]]
                gameTable[locs[i]] = [EMPTY, DISCNT]

        # fall a downwards word: entire word falls
        elif gameTable[loc][CONN] == "U":
            # get falling distance of whole word
            word, locs = _get(wordMap, loc)
            fall = getDownDist(gameTable, loc, CHAR, height, width)
            if fall == 0:
                continue
            # update gameTable and moves
            for i in range(len(word) - 1, -1, -1):
                falls.append([locs[i], locs[i] + fall * width, word[i]])
                gameTable[locs[i] + fall * width] = gameTable[locs[i]]
                gameTable[locs[i]] = [EMPTY, DISCNT]
                wordMap[word][i] += fall * width

        # fall a single character
        else:
            fall = getDownDist(gameTable, loc, CHAR, height, width)
            if fall == 0:
                continue
            falls.append([loc, loc + fall * width, gameTable[loc][CHAR]])
            gameTable[loc + fall * width] = gameTable[loc]
            gameTable[loc] = [EMPTY, DISCNT]

    # TODO: add new characters in empty cells
    adds = list()
    getGameData(CharDict, WordDict, FindDict, gameTable, wordMap, adds, height, width)
    
    # update moves
    moves.append(removes)
    moves.append(sorted(falls, key=lambda x: x[1]))
    moves.append(sorted(adds, key=lambda x: x[1]))

    return


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
